"use client";

/**
 * useBuilder - Stage-based Blueprint Builder hook.
 *
 * This hook manages the blueprint creation journey using direct API calls
 * to specialized agents (Architect, Crafter) instead of streaming.
 *
 * Flow:
 * 1. Define: User fills GuidedChat statement
 * 2. Design: POST /api/builder/architect → architecture JSON
 * 3. Design Review: User approves/revises architecture
 * 4. Craft: POST /api/builder/craft (for each agent) → agent spec JSON
 * 5. Craft Review: User approves/revises each agent
 * 6. Create: POST /api/builder/create → blueprint result
 * 7. Complete: Show success with Studio URL
 */

import { useState, useCallback, useMemo } from "react";
import type {
  ArchitectResponse,
  CraftResponse,
  CreateResponse,
  AgentYAMLSpec,
  BuilderStage,
} from "@/lib/types";
import { validateAgentSpec, type ValidationResult } from "@/lib/validation";
import {
  saveAgentToSession,
  saveBlueprintToSession,
  clearSession,
} from "@/lib/stores";

// UI Stage mapping (for header display)
export type UIStage = 1 | 2 | 3 | 4 | 5;

// Action mode for footer buttons
export type ActionMode = "submit" | "hitl" | "complete" | "loading";

// Screen type
export type ScreenType = "guided-chat" | "review";

interface UseBuilderReturn {
  // Stage info
  stage: UIStage;
  builderStage: BuilderStage;
  actionMode: ActionMode;
  screenType: ScreenType;

  // Data
  sessionId: string | null;
  architecture: ArchitectResponse | null;
  currentAgentSpec: AgentYAMLSpec | null;
  agentSpecs: AgentYAMLSpec[];
  currentAgentIndex: number;
  totalAgents: number;
  blueprintResult: CreateResponse | null;

  // Content for review screen
  reviewContent: string;
  reviewTitle: string;

  // Validation
  validationResult: ValidationResult | null;

  // Edit mode
  isEditMode: boolean;
  editedSpec: AgentYAMLSpec | null;

  // Loading/error
  isLoading: boolean;
  error: string | null;

  // Actions
  submitStatement: (statement: string) => Promise<void>;
  approveArchitecture: () => Promise<void>;
  reviseArchitecture: (feedback: string) => Promise<void>;
  approveAgent: () => Promise<void>;
  reviseAgent: (feedback: string) => Promise<void>;
  reset: () => void;

  // Edit mode actions
  enterEditMode: () => void;
  exitEditMode: () => void;
  updateAgentSpec: (spec: Partial<AgentYAMLSpec>) => void;
  saveEditedAgent: () => void;
}

export function useBuilder(): UseBuilderReturn {
  // === STATE ===
  const [builderStage, setBuilderStage] = useState<BuilderStage>("define");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [requirements, setRequirements] = useState<string | null>(null);
  const [architecture, setArchitecture] = useState<ArchitectResponse | null>(null);
  const [agentSpecs, setAgentSpecs] = useState<AgentYAMLSpec[]>([]);
  const [currentAgentIndex, setCurrentAgentIndex] = useState(0);
  const [blueprintResult, setBlueprintResult] = useState<CreateResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Edit mode state
  const [isEditMode, setIsEditMode] = useState(false);
  const [editedSpec, setEditedSpec] = useState<AgentYAMLSpec | null>(null);

  // === DERIVED VALUES ===

  // Total agents to craft (1 manager + N workers)
  const totalAgents = useMemo(() => {
    if (!architecture) return 0;
    return 1 + architecture.workers.length;
  }, [architecture]);

  // Current agent being crafted/reviewed
  const currentAgentSpec = useMemo(() => {
    if (builderStage === "craft-review" && agentSpecs.length > currentAgentIndex) {
      return agentSpecs[currentAgentIndex];
    }
    return null;
  }, [builderStage, agentSpecs, currentAgentIndex]);

  // Map builder stage to UI stage (1-5)
  const stage: UIStage = useMemo(() => {
    switch (builderStage) {
      case "define":
        return 1;
      case "designing":
      case "design-review":
        return 3; // Skip to Design (no Explore phase in new flow)
      case "crafting":
      case "craft-review":
        return 4;
      case "creating":
      case "complete":
        return 5;
      default:
        return 1;
    }
  }, [builderStage]);

  // Action mode for footer buttons
  const actionMode: ActionMode = useMemo(() => {
    if (isLoading) return "loading";
    if (builderStage === "define") return "submit";
    if (builderStage === "complete") return "complete";
    if (builderStage === "design-review" || builderStage === "craft-review") return "hitl";
    return "loading";
  }, [builderStage, isLoading]);

  // Screen type
  const screenType: ScreenType = useMemo(() => {
    return builderStage === "define" ? "guided-chat" : "review";
  }, [builderStage]);

  // Review content (markdown for display)
  const reviewContent = useMemo(() => {
    if (builderStage === "designing" || builderStage === "crafting" || builderStage === "creating") {
      return "Working on it...";
    }

    if (builderStage === "design-review" && architecture) {
      return generateArchitectureMarkdown(architecture);
    }

    if (builderStage === "craft-review" && currentAgentSpec) {
      return generateAgentMarkdown(currentAgentSpec, currentAgentIndex, totalAgents);
    }

    if (builderStage === "complete" && blueprintResult) {
      return `# Blueprint Created!\n\nYour blueprint **${blueprintResult.blueprint_id}** has been created successfully.`;
    }

    return "";
  }, [builderStage, architecture, currentAgentSpec, currentAgentIndex, totalAgents, blueprintResult]);

  // Review title
  const reviewTitle = useMemo(() => {
    if (builderStage === "design-review") return "Review Architecture";
    if (builderStage === "craft-review" && currentAgentSpec) {
      const agentType = currentAgentIndex === 0 ? "Manager" : "Worker";
      return `Review ${agentType} Agent (${currentAgentIndex + 1}/${totalAgents})`;
    }
    if (builderStage === "complete") return "Blueprint Created";
    return "";
  }, [builderStage, currentAgentSpec, currentAgentIndex, totalAgents]);

  // Validation result for current agent spec (uses editedSpec if in edit mode)
  const validationResult = useMemo((): ValidationResult | null => {
    if (builderStage === "craft-review") {
      const specToValidate = isEditMode && editedSpec ? editedSpec : currentAgentSpec;
      if (specToValidate) {
        return validateAgentSpec(specToValidate);
      }
    }
    return null;
  }, [builderStage, currentAgentSpec, isEditMode, editedSpec]);

  // === API CALLS ===

  const callArchitect = useCallback(async (reqs: string): Promise<ArchitectResponse> => {
    const response = await fetch("/api/builder/architect", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId || undefined,
        requirements: reqs,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP ${response.status}`);
    }

    return response.json();
  }, [sessionId]);

  const callCrafter = useCallback(async (
    agentName: string,
    agentPurpose: string,
    isManager: boolean,
    agentIndex: number,
    workerNames: string[]
  ): Promise<CraftResponse> => {
    if (!sessionId || !architecture) {
      throw new Error("Missing session or architecture");
    }

    // Build context string
    const context = `Pattern: ${architecture.pattern}
Manager: ${architecture.manager.name} - ${architecture.manager.purpose}
Workers: ${architecture.workers.map(w => `${w.name} - ${w.purpose}`).join(", ")}
Requirements: ${requirements || ""}`;

    const response = await fetch("/api/builder/craft", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        agent_name: agentName,
        agent_purpose: agentPurpose,
        is_manager: isManager,
        agent_index: agentIndex,
        context,
        worker_names: workerNames,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP ${response.status}`);
    }

    return response.json();
  }, [sessionId, architecture, requirements]);

  const callCreate = useCallback(async (specs: AgentYAMLSpec[]): Promise<CreateResponse> => {
    if (!sessionId) {
      throw new Error("Missing session");
    }

    // Send agent specs directly to avoid session state issues
    // Backend may have lost session state, so we send all specs
    const response = await fetch("/api/builder/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        agent_specs: specs,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP ${response.status}`);
    }

    return response.json();
  }, [sessionId]);

  // === ACTIONS ===

  const submitStatement = useCallback(async (statement: string) => {
    setIsLoading(true);
    setError(null);
    setBuilderStage("designing");
    setRequirements(statement);

    try {
      const result = await callArchitect(statement);
      setSessionId(result.session_id);
      setArchitecture(result);
      setBuilderStage("design-review");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to design architecture");
      setBuilderStage("define");
    } finally {
      setIsLoading(false);
    }
  }, [callArchitect]);

  const craftNextAgent = useCallback(async (retryCount = 0) => {
    if (!architecture) return;

    const MAX_RETRIES = 2;

    setIsLoading(true);
    setError(null);
    setBuilderStage("crafting");

    try {
      const isManager = currentAgentIndex === 0;
      const agentInfo = isManager
        ? architecture.manager
        : architecture.workers[currentAgentIndex - 1];

      const workerNames = isManager
        ? architecture.workers.map(w => w.name)
        : [];

      const result = await callCrafter(
        agentInfo.name,
        agentInfo.purpose,
        isManager,
        currentAgentIndex,
        workerNames
      );

      // Validate the generated agent spec
      const validation = validateAgentSpec(result.agent_yaml);

      // If validation has errors and we haven't exceeded retries, retry
      if (!validation.valid && retryCount < MAX_RETRIES) {
        console.log(`Agent QC failed (attempt ${retryCount + 1}/${MAX_RETRIES}), retrying...`);
        // Retry with incremented count
        return craftNextAgent(retryCount + 1);
      }

      setAgentSpecs(prev => [...prev, result.agent_yaml]);
      setBuilderStage("craft-review");

      // Save agent YAML to session store
      saveAgentToSession(result.agent_yaml);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to craft agent");
      setBuilderStage("design-review");
    } finally {
      setIsLoading(false);
    }
  }, [architecture, currentAgentIndex, callCrafter]);

  const approveArchitecture = useCallback(async () => {
    // Start crafting the first agent (manager)
    await craftNextAgent();
  }, [craftNextAgent]);

  const reviseArchitecture = useCallback(async (feedback: string) => {
    if (!requirements) return;

    setIsLoading(true);
    setError(null);
    setBuilderStage("designing");

    try {
      // Include feedback in requirements
      const revisedRequirements = `${requirements}\n\nRevision feedback: ${feedback}`;
      const result = await callArchitect(revisedRequirements);
      setSessionId(result.session_id);
      setArchitecture(result);
      setBuilderStage("design-review");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to revise architecture");
      setBuilderStage("design-review");
    } finally {
      setIsLoading(false);
    }
  }, [requirements, callArchitect]);

  const approveAgent = useCallback(async () => {
    const nextIndex = currentAgentIndex + 1;

    if (nextIndex < totalAgents) {
      // More agents to craft
      setCurrentAgentIndex(nextIndex);
      await craftNextAgent();
    } else {
      // All agents crafted, create blueprint
      setIsLoading(true);
      setError(null);
      setBuilderStage("creating");

      try {
        // Pass all agent specs directly to ensure all workers are created
        const result = await callCreate(agentSpecs);
        setBlueprintResult(result);
        setBuilderStage("complete");

        // Save blueprint YAML to session store
        const managerSpec = agentSpecs.find((s) => s.is_manager);
        saveBlueprintToSession(
          result.blueprint_name || result.blueprint_id,
          managerSpec?.description || "",
          agentSpecs,
          { visibility: result.share_type || "private" }
        );
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to create blueprint");
        setBuilderStage("craft-review");
      } finally {
        setIsLoading(false);
      }
    }
  }, [currentAgentIndex, totalAgents, craftNextAgent, callCreate, agentSpecs]);

  const reviseAgent = useCallback(async (feedback: string) => {
    if (!architecture) return;

    setIsLoading(true);
    setError(null);
    setBuilderStage("crafting");

    try {
      const isManager = currentAgentIndex === 0;
      const agentInfo = isManager
        ? architecture.manager
        : architecture.workers[currentAgentIndex - 1];

      const workerNames = isManager
        ? architecture.workers.map(w => w.name)
        : [];

      // Include feedback in the purpose
      const revisedPurpose = `${agentInfo.purpose}\n\nRevision feedback: ${feedback}`;

      const result = await callCrafter(
        agentInfo.name,
        revisedPurpose,
        isManager,
        currentAgentIndex,
        workerNames
      );

      // Replace the current agent spec
      setAgentSpecs(prev => {
        const updated = [...prev];
        updated[currentAgentIndex] = result.agent_yaml;
        return updated;
      });
      setBuilderStage("craft-review");

      // Update YAML in session store
      saveAgentToSession(result.agent_yaml);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to revise agent");
      setBuilderStage("craft-review");
    } finally {
      setIsLoading(false);
    }
  }, [architecture, currentAgentIndex, callCrafter]);

  const reset = useCallback(() => {
    setBuilderStage("define");
    setSessionId(null);
    setRequirements(null);
    setArchitecture(null);
    setAgentSpecs([]);
    setCurrentAgentIndex(0);
    setBlueprintResult(null);
    setIsLoading(false);
    setError(null);
    setIsEditMode(false);
    setEditedSpec(null);

    // Clear YAML session store
    clearSession();
  }, []);

  // === EDIT MODE ACTIONS ===

  const enterEditMode = useCallback(() => {
    if (currentAgentSpec) {
      setEditedSpec({ ...currentAgentSpec });
      setIsEditMode(true);
    }
  }, [currentAgentSpec]);

  const exitEditMode = useCallback(() => {
    setIsEditMode(false);
    setEditedSpec(null);
  }, []);

  const updateAgentSpec = useCallback((updates: Partial<AgentYAMLSpec>) => {
    setEditedSpec(prev => {
      if (!prev) return null;
      return { ...prev, ...updates };
    });
  }, []);

  const saveEditedAgent = useCallback(() => {
    if (!editedSpec || !isEditMode) return;

    // Validate before saving - block if there are errors
    const validation = validateAgentSpec(editedSpec);
    if (!validation.valid) {
      // Don't save if validation fails - errors will be shown in UI
      console.warn("Cannot save agent: validation errors", validation.errors);
      return;
    }

    // Update the agent spec in the array
    setAgentSpecs(prev => {
      const updated = [...prev];
      updated[currentAgentIndex] = editedSpec;
      return updated;
    });

    // Update YAML in session store
    saveAgentToSession(editedSpec);

    // Exit edit mode
    setIsEditMode(false);
    setEditedSpec(null);
  }, [editedSpec, isEditMode, currentAgentIndex]);

  return {
    // Stage info
    stage,
    builderStage,
    actionMode,
    screenType,

    // Data
    sessionId,
    architecture,
    currentAgentSpec,
    agentSpecs,
    currentAgentIndex,
    totalAgents,
    blueprintResult,

    // Content
    reviewContent,
    reviewTitle,

    // Validation
    validationResult,

    // Edit mode
    isEditMode,
    editedSpec,

    // Loading/error
    isLoading,
    error,

    // Actions
    submitStatement,
    approveArchitecture,
    reviseArchitecture,
    approveAgent,
    reviseAgent,
    reset,

    // Edit mode actions
    enterEditMode,
    exitEditMode,
    updateAgentSpec,
    saveEditedAgent,
  };
}

// === HELPER FUNCTIONS ===

function generateArchitectureMarkdown(arch: ArchitectResponse): string {
  const lines: string[] = [];

  lines.push(`## ${arch.reasoning}`);
  lines.push("");
  lines.push(`**Pattern:** ${arch.pattern.replace(/_/g, " ")}`);
  lines.push("");

  lines.push("### Manager Agent");
  lines.push(`**${arch.manager.name}**`);
  lines.push("");
  lines.push(arch.manager.purpose);
  lines.push("");

  if (arch.workers.length > 0) {
    lines.push("### Worker Agents");
    lines.push("");
    for (const worker of arch.workers) {
      lines.push(`#### ${worker.name}`);
      lines.push(worker.purpose);
      lines.push("");
    }
  }

  return lines.join("\n");
}

function generateAgentMarkdown(
  spec: AgentYAMLSpec,
  index: number,
  total: number
): string {
  const lines: string[] = [];
  const agentType = index === 0 ? "Manager" : "Worker";

  lines.push(`## ${spec.name}`);
  lines.push(`*${agentType} Agent (${index + 1}/${total})*`);
  lines.push("");
  lines.push(spec.description);
  lines.push("");
  lines.push("### Configuration");
  lines.push("");
  lines.push(`- **Model:** ${spec.model}`);
  lines.push(`- **Temperature:** ${spec.temperature}`);
  lines.push(`- **Role:** ${spec.role}`);
  lines.push("");
  lines.push("### Goal");
  lines.push(spec.goal);
  lines.push("");

  if (spec.usage_description) {
    lines.push("### When to Use");
    lines.push(spec.usage_description);
    lines.push("");
  }

  lines.push("### Instructions");
  lines.push("```");
  lines.push(spec.instructions);
  lines.push("```");

  return lines.join("\n");
}
