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

import { useState, useCallback, useMemo, useRef, useEffect } from "react";
import type {
  ArchitectResponse,
  CraftResponse,
  CreateResponse,
  AgentYAMLSpec,
  BuilderStage,
} from "@/lib/types";
import {
  validateAgentSpec,
  validateArchitectureGate,
  validateAgentGate,
  buildAndValidateBlueprintRequest,
  detectPlaceholders,
  GENERIC_TERMS,
  type ValidationResult,
} from "@/lib/validation";
import { toFlatAgentSpecs } from "@/lib/schemas";
import {
  saveAgentToSession,
  saveBlueprintToSession,
  clearSession,
} from "@/lib/stores";
import type { UnifiedStage, BuildProgress } from "@/lib/schemas/stage";
import { generateReadme, AGENT_IDS } from "@/lib/lyzr";

// Action mode for footer buttons
export type ActionMode = "submit" | "hitl" | "complete" | "loading";

// Screen type
export type ScreenType = "guided-chat" | "review";

/**
 * Sub-step within the Build stage
 */
export interface BuildSubStep {
  id: string;
  label: string;
  index: number;
}

interface UseBuilderReturn {
  // Stage info
  builderStage: BuilderStage;
  actionMode: ActionMode;
  screenType: ScreenType;

  // Unified stage progress (3-stage: Define → Build → Complete)
  unifiedStage: UnifiedStage;
  buildProgress: BuildProgress | undefined;

  // Navigation
  buildSubSteps: BuildSubStep[];
  navigateToDefine: () => void;
  navigateToBuild: () => void;
  navigateToComplete: () => void;
  navigateToSubStep: (index: number) => void;

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

  // Define step edit mode
  isDefineReadOnly: boolean;
  enterDefineEditMode: () => void;
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

  // Ref to always have latest agentSpecs (fixes React closure stale state issues)
  const agentSpecsRef = useRef<AgentYAMLSpec[]>([]);
  useEffect(() => {
    agentSpecsRef.current = agentSpecs;
    console.log("[useBuilder] agentSpecsRef updated, count:", agentSpecs.length);
  }, [agentSpecs]);

  // Define step: read-only mode when returning from Build
  // When true, options are disabled until user clicks "Edit"
  const [isDefineReadOnly, setIsDefineReadOnly] = useState(false);

  // === DERIVED VALUES ===

  // Total agents to craft (coordinator + specialists)
  const totalAgents = useMemo(() => {
    if (!architecture?.agents) return 0;
    return architecture.agents.length;
  }, [architecture]);

  // Current agent being crafted/reviewed
  const currentAgentSpec = useMemo(() => {
    if (builderStage === "craft-review" && agentSpecs.length > currentAgentIndex) {
      return agentSpecs[currentAgentIndex];
    }
    return null;
  }, [builderStage, agentSpecs, currentAgentIndex]);

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

  // Unified stage (3-stage progress: Define → Build → Complete)
  const unifiedStage: UnifiedStage = useMemo(() => {
    if (builderStage === "define") return "define";
    if (builderStage === "complete") return "complete";
    return "build"; // designing, design-review, crafting, craft-review, creating
  }, [builderStage]);

  // Build progress (N/M for the Build stage - agents only)
  const buildProgress: BuildProgress | undefined = useMemo(() => {
    if (unifiedStage !== "build") return undefined;

    // Total = just the agents (no architecture step)
    const total = totalAgents;

    // Current progress based on stage
    let current = 0;
    if (builderStage === "designing" || builderStage === "design-review") {
      current = 0; // Architecture phase, no agents yet
    } else if (builderStage === "crafting") {
      current = currentAgentIndex; // Working on agent N (0-indexed)
    } else if (builderStage === "craft-review") {
      current = currentAgentIndex + 1; // Agent N done (1-indexed for display)
    } else if (builderStage === "creating") {
      current = total; // All agents done
    }

    return { current, total };
  }, [unifiedStage, builderStage, totalAgents, currentAgentIndex]);

  // Build sub-steps for navigation (shown during Build stage including architecture review)
  const buildSubSteps: BuildSubStep[] = useMemo(() => {
    // Show sub-steps during entire Build stage (architecture + crafting)
    if (unifiedStage !== "build" || !architecture?.agents) return [];
    // Don't show during designing (loading) phase
    if (builderStage === "designing") return [];

    // Map agents to sub-steps (first = coordinator, rest = specialists)
    return architecture.agents.map((agent, index) => ({
      id: index === 0 ? "coordinator" : `specialist-${index - 1}`,
      label: agent.name,
      index,
    }));
  }, [unifiedStage, builderStage, architecture]);

  // Review content (markdown for display)
  const reviewContent = useMemo(() => {
    if (builderStage === "designing" || builderStage === "crafting" || builderStage === "creating") {
      return "Working on it...";
    }

    if (builderStage === "design-review" && architecture?.agents) {
      return generateArchitectureMarkdown(architecture);
    }

    if (builderStage === "craft-review" && currentAgentSpec) {
      return generateAgentMarkdown(currentAgentSpec, currentAgentIndex, totalAgents);
    }

    if (builderStage === "complete" && blueprintResult) {
      // Content is displayed via the compact header + chat UI, no markdown needed
      return "";
    }

    return "";
  }, [builderStage, architecture, currentAgentSpec, currentAgentIndex, totalAgents, blueprintResult]);

  // Review title
  const reviewTitle = useMemo(() => {
    if (builderStage === "design-review") return "Review Design";
    if (builderStage === "craft-review" && currentAgentSpec) {
      const agentType = currentAgentIndex === 0 ? "Coordinator" : "Specialist";
      return `Review ${agentType} (${currentAgentIndex + 1}/${totalAgents})`;
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

    const data = await response.json();

    // Transform old format (manager/workers) to new pattern-agnostic format (agents)
    if (data.agents) {
      // Already in new format
      return data as ArchitectResponse;
    }

    // Convert old format to new format
    const agents: Array<{ name: string; role: string; goal: string }> = [];

    // Manager becomes coordinator (first agent)
    if (data.manager) {
      agents.push({
        name: data.manager.name,
        role: data.manager.purpose?.split(".")[0] || "Workflow coordinator",
        goal: data.manager.purpose || "Orchestrate the workflow",
      });
    }

    // Workers become specialists
    if (data.workers && Array.isArray(data.workers)) {
      for (const worker of data.workers) {
        agents.push({
          name: worker.name,
          role: worker.purpose?.split(".")[0] || "Specialist",
          goal: worker.purpose || "Handle specialized tasks",
        });
      }
    }

    return {
      session_id: data.session_id,
      reasoning: data.reasoning || "",
      agents,
    };
  }, [sessionId]);

  const callCrafter = useCallback(async (
    agentName: string,
    agentPurpose: string,
    isManager: boolean,
    agentIndex: number,
    workerNames: string[]
  ): Promise<CraftResponse> => {
    if (!sessionId || !architecture?.agents) {
      throw new Error("Missing session or architecture");
    }

    // Build context string
    const [coordinator, ...specialists] = architecture.agents;
    const context = `Coordinator: ${coordinator.name}
- Role: ${coordinator.role}
- Goal: ${coordinator.goal}
Specialists: ${specialists.map(s => `${s.name} (${s.role})`).join(", ")}
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

  const callCreate = useCallback(async (specs: AgentYAMLSpec[], readmeContent?: string): Promise<CreateResponse> => {
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
        readme: readmeContent,
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
    // Smart reset: only clear progress if statement changed AND we have existing progress
    const isNewStatement = requirements && statement !== requirements;
    if (isNewStatement && (architecture || agentSpecs.length > 0)) {
      setArchitecture(null);
      setAgentSpecs([]);
      setCurrentAgentIndex(0);
      setBlueprintResult(null);
    }

    setIsLoading(true);
    setError(null);
    setBuilderStage("designing");
    setRequirements(statement);

    try {
      const result = await callArchitect(statement);

      // Gate 1: Validate architecture output
      const gate = validateArchitectureGate({
        reasoning: result.reasoning,
        agents: result.agents,
      });

      if (!gate.valid) {
        console.warn("Architecture gate validation failed:", gate.errors);
        // Continue anyway but log the issues - architecture is still usable
      }

      setSessionId(result.session_id);
      setArchitecture(result);
      setBuilderStage("design-review");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to design architecture");
      setBuilderStage("define");
    } finally {
      setIsLoading(false);
    }
  }, [callArchitect, requirements, architecture, agentSpecs]);

  const craftNextAgent = useCallback(async (agentIndex?: number, retryCount = 0) => {
    if (!architecture?.agents) return;

    // Use passed index or fall back to current state (for initial call)
    const indexToUse = agentIndex ?? currentAgentIndex;

    const MAX_RETRIES = 5;

    setIsLoading(true);
    setError(null);
    setBuilderStage("crafting");

    try {
      const isCoordinator = indexToUse === 0;
      const agentInfo = architecture.agents[indexToUse];

      // Specialists (non-coordinators) don't need to know about other agents
      const specialistNames = isCoordinator
        ? architecture.agents.slice(1).map(a => a.name)
        : [];

      const result = await callCrafter(
        agentInfo.name,
        `${agentInfo.role}: ${agentInfo.goal}`,
        isCoordinator,
        indexToUse,  // Fixed: was currentAgentIndex (stale state)
        specialistNames
      );

      // === Background Quality Gate ===
      // All quality issues trigger automatic retry - user never sees them
      const shouldRetry = checkAgentQuality(result.agent_yaml);
      if (shouldRetry && retryCount < MAX_RETRIES) {
        console.log(`Agent quality check failed (attempt ${retryCount + 1}/${MAX_RETRIES}), retrying...`);
        return craftNextAgent(indexToUse, retryCount + 1);
      }

      // If still failing after all retries, show error
      if (shouldRetry) {
        throw new Error(
          "Unable to generate a valid agent configuration. " +
          "The app is experiencing an issue. Please report to harshit.choudhary@lyzr.ai"
        );
      }

      // Ensure coordinator has sub_agents linking to specialists
      const agentYaml = result.agent_yaml;
      if (isCoordinator && architecture.agents.length > 1) {
        // Generate specialist filenames to set as sub_agents
        const specialistFilenames = architecture.agents.slice(1).map((a) =>
          `${a.name.toLowerCase().replace(/\s+/g, "-")}.yaml`
        );
        agentYaml.sub_agents = specialistFilenames;
      }

      // DEBUG: Log what's being added to state with unique identifier
      const instrHash = agentYaml.instructions?.length || 0;
      console.log(`[craftNextAgent] Adding agent to state: index=${indexToUse}, name="${agentYaml.name}", instrLen=${instrHash}`);
      console.log(`[craftNextAgent] Agent role="${agentYaml.role}", goal first 50="${agentYaml.goal?.substring(0, 50)}"`);

      setAgentSpecs((prev) => {
        // Log ALL specs in the array to detect any duplication
        console.log(`[craftNextAgent] State update: prev.length=${prev.length}, adding "${agentYaml.name}"`);
        prev.forEach((spec, i) => {
          console.log(`[craftNextAgent]   Existing[${i}]: name="${spec.name}", instrLen=${spec.instructions?.length}`);
        });
        return [...prev, agentYaml];
      });
      setBuilderStage("craft-review");

      // Save agent YAML to session store
      saveAgentToSession(agentYaml);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to craft agent. Please report to harshit.choudhary@lyzr.ai");
      setBuilderStage("design-review");
    } finally {
      setIsLoading(false);
    }
  }, [architecture, currentAgentIndex, callCrafter]);

  const approveArchitecture = useCallback(async () => {
    // Start crafting the first agent (manager) - explicitly pass index 0
    await craftNextAgent(0);
  }, [craftNextAgent]);

  const reviseArchitecture = useCallback(async (feedback: string) => {
    if (!requirements) return;

    setIsLoading(true);
    setError(null);
    setBuilderStage("designing");

    // Reset agent-related state when architecture is revised
    setAgentSpecs([]);
    setCurrentAgentIndex(0);

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
      // More agents to craft - pass the next index explicitly to avoid stale closure
      setCurrentAgentIndex(nextIndex);
      await craftNextAgent(nextIndex);
    } else {
      // All agents crafted, create blueprint
      setIsLoading(true);
      setError(null);
      setBuilderStage("creating");

      try {
        // IMPORTANT: Use ref to get latest state, avoiding stale closure issues
        const currentSpecs = agentSpecsRef.current;
        console.log("[useBuilder] Using agentSpecsRef.current, count:", currentSpecs.length);

        // Pre-check: Scan all agents for placeholder text before sending to backend
        for (const spec of currentSpecs) {
          const fieldsToCheck = [
            { name: "instructions", value: spec.instructions },
            { name: "description", value: spec.description },
            { name: "role", value: spec.role },
            { name: "goal", value: spec.goal },
            { name: "usage_description", value: spec.usage_description },
          ].filter(f => f.value);

          for (const field of fieldsToCheck) {
            const placeholders = detectPlaceholders(field.value as string);
            if (placeholders.length > 0) {
              console.error(`Agent "${spec.name}" has placeholder in ${field.name}:`, placeholders);
              setError(`Agent "${spec.name}" contains placeholder text in ${field.name}. Please revise.`);
              setBuilderStage("craft-review");
              setIsLoading(false);
              return;
            }
          }
        }

        // DEBUG: Log agentSpecs before validation (using ref value)
        console.log("[useBuilder] currentSpecs count:", currentSpecs.length);
        currentSpecs.forEach((spec, i) => {
          console.log(`[useBuilder] Agent ${i}: name="${spec.name}", is_manager=${spec.is_manager}`);
          console.log(`[useBuilder] Agent ${i}: instructions first 100:`, spec.instructions?.substring(0, 100));
        });

        // Gate 3: Validate complete blueprint request before creating
        // Derive pattern from agent count (no longer stored in state)
        const derivedPattern = currentSpecs.length === 1 ? "single_agent" : "manager_workers";
        const gate = buildAndValidateBlueprintRequest(
          sessionId || "",
          currentSpecs,
          derivedPattern
        );

        if (!gate.valid) {
          console.error("Blueprint validation failed:", gate.errors);
          // Show first error to user
          setError(`Validation failed: ${gate.errors[0]}`);
          setBuilderStage("craft-review");
          setIsLoading(false);
          return;
        }

        // Convert validated hierarchical request to flat array for API
        // (backward compatible until API is updated)
        const flatRequest = toFlatAgentSpecs(gate.data!);

        // DEBUG: Log flatRequest after transformation
        console.log("[useBuilder] flatRequest.agent_specs count:", flatRequest.agent_specs.length);
        flatRequest.agent_specs.forEach((spec, i) => {
          console.log(`[useBuilder] flatRequest[${i}]: name="${spec.name}", is_manager=${spec.is_manager}`);
          console.log(`[useBuilder] flatRequest[${i}]: instructions first 100:`, spec.instructions?.substring(0, 100));
        });

        // Generate README silently in background (don't block on failure)
        let readmeContent: string | undefined;
        if (AGENT_IDS.readmeBuilder && sessionId) {
          try {
            const managerSpec = currentSpecs.find((s) => s.is_manager);
            readmeContent = await generateReadme({
              agentId: AGENT_IDS.readmeBuilder,
              sessionId,
              blueprintName: managerSpec?.name?.replace("Coordinator", "Blueprint") || "Blueprint",
              blueprintDescription: managerSpec?.description || "AI agent blueprint",
              agents: currentSpecs.map((spec) => ({
                name: spec.name,
                role: spec.role,
                goal: spec.goal,
                is_manager: spec.is_manager,
                instructions: spec.instructions,
              })),
            });
            console.log("[useBuilder] README generated successfully");
          } catch (readmeErr) {
            // Silently log error - README is optional, don't block blueprint creation
            console.warn("[useBuilder] README generation failed (non-blocking):", readmeErr);
          }
        }

        // Pass all agent specs directly to ensure all workers are created
        const result = await callCreate(flatRequest.agent_specs, readmeContent);
        setBlueprintResult(result);
        setBuilderStage("complete");

        // Save blueprint YAML to session store
        const managerSpec = currentSpecs.find((s) => s.is_manager);
        saveBlueprintToSession(
          result.blueprint_name || result.blueprint_id,
          managerSpec?.description || "",
          currentSpecs,
          { visibility: result.share_type || "private" }
        );
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to create blueprint");
        setBuilderStage("craft-review");
      } finally {
        setIsLoading(false);
      }
    }
  }, [currentAgentIndex, totalAgents, craftNextAgent, callCreate, agentSpecs, sessionId]);

  const reviseAgent = useCallback(async (feedback: string) => {
    if (!architecture?.agents) return;

    setIsLoading(true);
    setError(null);
    setBuilderStage("crafting");

    try {
      const isCoordinator = currentAgentIndex === 0;
      const agentInfo = architecture.agents[currentAgentIndex];

      const specialistNames = isCoordinator
        ? architecture.agents.slice(1).map(a => a.name)
        : [];

      // Include feedback in the purpose
      const revisedPurpose = `${agentInfo.role}: ${agentInfo.goal}\n\nRevision feedback: ${feedback}`;

      const result = await callCrafter(
        agentInfo.name,
        revisedPurpose,
        isCoordinator,
        currentAgentIndex,
        specialistNames
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
    setIsDefineReadOnly(false);

    // Clear YAML session store
    clearSession();
  }, []);

  // === NAVIGATION ACTIONS ===

  /**
   * Navigate back to Define stage - preserves Build progress
   * Progress is only reset when user submits a NEW statement
   * Sets read-only mode if there's existing progress (user must click Edit to change)
   */
  const navigateToDefine = useCallback(() => {
    // Just switch stage - preserve all progress
    setBuilderStage("define");
    setIsEditMode(false);
    setEditedSpec(null);
    setError(null);
    // If there's existing progress, enter read-only mode
    // User must click "Edit" to modify the statement
    if (architecture) {
      setIsDefineReadOnly(true);
    }
    // Keep: architecture, agentSpecs, currentAgentIndex, blueprintResult, requirements
  }, [architecture]);

  /**
   * Navigate to Build stage - always goes to Architecture review
   * Click sub-steps to navigate to specific agents
   */
  const navigateToBuild = useCallback(() => {
    if (!architecture) return; // No progress to return to
    setBuilderStage("design-review");
    setIsEditMode(false);
    setEditedSpec(null);
    setError(null);
  }, [architecture]);

  /**
   * Navigate to Complete stage - shows the success screen
   * Only works if blueprint has been created
   */
  const navigateToComplete = useCallback(() => {
    if (!blueprintResult) return; // No blueprint to show
    setBuilderStage("complete");
    setIsEditMode(false);
    setEditedSpec(null);
    setError(null);
  }, [blueprintResult]);

  /**
   * Navigate to a specific agent sub-step within Build stage
   * Index 0 = Manager, 1+ = Workers
   *
   * Navigation rules:
   * - Can navigate to any completed step (0 to agentSpecs.length - 1)
   * - Cannot navigate beyond what's been completed
   * - Going backward then forward doesn't reset progress (unless you make changes)
   */
  const navigateToSubStep = useCallback((targetIndex: number) => {
    const maxCompleted = agentSpecs.length - 1;

    // Can only navigate to completed steps
    if (targetIndex > maxCompleted) return;

    // Skip if already at this step AND already in craft-review
    // (allows navigating from design-review back to any agent)
    if (targetIndex === currentAgentIndex && builderStage === "craft-review") return;

    // Exit edit mode if active
    setIsEditMode(false);
    setEditedSpec(null);
    setError(null);

    // Navigate to the target agent review
    setCurrentAgentIndex(targetIndex);
    setBuilderStage("craft-review");
  }, [agentSpecs.length, currentAgentIndex, builderStage]);

  /**
   * Enter edit mode for Define step
   * Enables the slot selectors so user can change their statement
   */
  const enterDefineEditMode = useCallback(() => {
    setIsDefineReadOnly(false);
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
    builderStage,
    actionMode,
    screenType,

    // Unified stage progress (3-stage: Define → Build → Complete)
    unifiedStage,
    buildProgress,

    // Navigation (use currentAgentIndex for current step, agentSpecs.length - 1 for max completed)
    buildSubSteps,
    navigateToDefine,
    navigateToBuild,
    navigateToComplete,
    navigateToSubStep,

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

    // Define step edit mode
    isDefineReadOnly,
    enterDefineEditMode,
  };
}

// === HELPER FUNCTIONS ===

function generateArchitectureMarkdown(arch: ArchitectResponse): string {
  const lines: string[] = [];
  const [coordinator, ...specialists] = arch.agents;

  // Summary as blockquote
  lines.push(`> ${arch.reasoning}`);
  lines.push("");
  lines.push("---");
  lines.push("");

  // Coordinator section
  lines.push("## Coordinator");
  lines.push("");
  lines.push(`### ${coordinator.name}`);
  lines.push("");
  lines.push(`**Role:** ${coordinator.role}`);
  lines.push("");
  lines.push(`**Goal:** ${coordinator.goal}`);
  lines.push("");

  // Specialists section
  if (specialists.length > 0) {
    lines.push("## Specialists");
    lines.push("");
    for (const specialist of specialists) {
      lines.push(`### ${specialist.name}`);
      lines.push("");
      lines.push(`**Role:** ${specialist.role}`);
      lines.push("");
      lines.push(`**Goal:** ${specialist.goal}`);
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
  const agentType = index === 0 ? "Coordinator" : "Specialist";

  lines.push(`## ${spec.name}`);
  lines.push(`*${agentType} (${index + 1}/${total})*`);
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

/**
 * Check agent quality - returns true if agent should be retried
 * Consolidates all quality checks that would cause backend rejection
 */
function checkAgentQuality(spec: AgentYAMLSpec): boolean {
  // 1. Check for placeholder text in critical fields
  const textFields = [
    spec.instructions,
    spec.description,
    spec.role,
    spec.goal,
    spec.usage_description,
  ].filter(Boolean);

  const hasPlaceholders = textFields.some(
    (field) => detectPlaceholders(field as string).length > 0
  );
  if (hasPlaceholders) return true;

  // 2. Check for generic terms in role (backend rejects these)
  if (spec.role) {
    const lowerRole = spec.role.toLowerCase();
    const hasGenericTerm = GENERIC_TERMS.some((term) =>
      lowerRole.includes(term.toLowerCase())
    );
    if (hasGenericTerm) return true;
  }

  // 3. Basic field validation (backend will reject)
  if (!spec.name || spec.name.length < 1) return true;
  if (!spec.description || spec.description.length < 20) return true;
  if (!spec.instructions || spec.instructions.length < 50) return true;
  if (!spec.model) return true;

  // 4. Role/goal length validation
  if (spec.role && (spec.role.length < 15 || spec.role.length > 80)) return true;
  if (spec.goal && (spec.goal.length < 50 || spec.goal.length > 300)) return true;

  return false;
}
