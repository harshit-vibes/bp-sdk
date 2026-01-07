/**
 * Validation Gates
 *
 * Stage transition validators that ensure data integrity at each point
 * in the blueprint creation flow. Each gate validates input/output
 * before allowing progression to the next stage.
 *
 * Flow:
 * Define → [Gate 1] → Design → [Gate 2] → Build → [Gate 3] → Create
 */

import { ZodError } from "zod";
import {
  ArchitectureOutputSchema,
  type ArchitectureOutput,
} from "../schemas/architecture";
import {
  AgentSpecSchema,
  ManagerSpecSchema,
  WorkerSpecSchema,
  type AgentSpec,
  type ManagerSpec,
  type WorkerSpec,
} from "../schemas/agent-spec";
import {
  BlueprintRequestSchema,
  type BlueprintRequest,
  fromFlatAgentSpecs,
} from "../schemas/blueprint";

/**
 * Gate result with typed data on success.
 */
export interface GateResult<T> {
  valid: boolean;
  data?: T;
  errors: string[];
  /** Raw Zod errors for detailed debugging */
  zodErrors?: ZodError;
}

/**
 * Format Zod errors into human-readable strings.
 */
function formatZodErrors(error: ZodError): string[] {
  return error.issues.map((issue) => {
    const path = issue.path.length > 0 ? `${issue.path.join(".")}: ` : "";
    return `${path}${issue.message}`;
  });
}

/**
 * Gate 1: Architecture Validation
 *
 * Validates the output from the Design Agent before allowing
 * the user to proceed to agent crafting.
 *
 * Checks:
 * - Reasoning is present
 * - At least one agent (coordinator) exists
 * - All agents have valid name, role, goal
 *
 * @param data - Raw architecture output from Design Agent
 * @returns GateResult with validated ArchitectureOutput on success
 */
export function validateArchitectureGate(data: unknown): GateResult<ArchitectureOutput> {
  const result = ArchitectureOutputSchema.safeParse(data);

  if (result.success) {
    return {
      valid: true,
      data: result.data,
      errors: [],
    };
  }

  return {
    valid: false,
    errors: formatZodErrors(result.error),
    zodErrors: result.error,
  };
}

/**
 * Gate 2: Agent Spec Validation
 *
 * Validates each agent specification before showing to user for approval.
 * Uses discriminated union to apply manager or worker-specific rules.
 *
 * Manager checks:
 * - is_manager: true
 * - sub_agents is array (can be empty for single-agent blueprints)
 * - No usage_description required
 *
 * Worker checks:
 * - is_manager: false
 * - sub_agents is empty
 * - usage_description is required (20-500 chars)
 *
 * @param data - Raw agent spec from Crafter Agent
 * @param isManager - Whether this is the manager agent
 * @returns GateResult with validated AgentSpec on success
 */
export function validateAgentGate(
  data: unknown,
  isManager: boolean
): GateResult<AgentSpec> {
  // Use specific schema based on agent type
  const schema = isManager ? ManagerSpecSchema : WorkerSpecSchema;
  const result = schema.safeParse(data);

  if (result.success) {
    return {
      valid: true,
      data: result.data as AgentSpec,
      errors: [],
    };
  }

  return {
    valid: false,
    errors: formatZodErrors(result.error),
    zodErrors: result.error,
  };
}

/**
 * Gate 2b: Flexible Agent Validation
 *
 * Validates an agent spec using the discriminated union schema.
 * Automatically determines if it's a manager or worker based on is_manager field.
 *
 * @param data - Raw agent spec with is_manager field
 * @returns GateResult with validated AgentSpec on success
 */
export function validateAgentSpecAuto(data: unknown): GateResult<AgentSpec> {
  const result = AgentSpecSchema.safeParse(data);

  if (result.success) {
    return {
      valid: true,
      data: result.data,
      errors: [],
    };
  }

  return {
    valid: false,
    errors: formatZodErrors(result.error),
    zodErrors: result.error,
  };
}

/**
 * Gate 3: Blueprint Request Validation
 *
 * Validates the complete blueprint creation request with full hierarchy.
 * This is the final gate before calling the Create API.
 *
 * Checks:
 * - Session ID is present
 * - Manager is valid (sub_agents can be empty for single-agent)
 * - All workers are valid with usage_description (if any)
 * - Manager's sub_agents match worker filenames (if workers exist)
 * - Pattern type matches worker count (single_agent=0, manager_workers=1+)
 *
 * @param data - Complete blueprint request with manager, workers, pattern
 * @returns GateResult with validated BlueprintRequest on success
 */
export function validateBlueprintGate(data: unknown): GateResult<BlueprintRequest> {
  const result = BlueprintRequestSchema.safeParse(data);

  if (result.success) {
    return {
      valid: true,
      data: result.data,
      errors: [],
    };
  }

  return {
    valid: false,
    errors: formatZodErrors(result.error),
    zodErrors: result.error,
  };
}

/**
 * Gate 3b: Build Blueprint Request from Flat Specs
 *
 * Helper that converts flat agent specs to hierarchical BlueprintRequest
 * and validates in one step.
 *
 * @param sessionId - Session ID
 * @param agentSpecs - Flat array of agent specs
 * @param pattern - Orchestration pattern
 * @returns GateResult with validated BlueprintRequest on success
 */
export function buildAndValidateBlueprintRequest(
  sessionId: string,
  agentSpecs: Array<{
    filename: string;
    is_manager: boolean;
    agent_index: number;
    name: string;
    description: string;
    model: string;
    temperature: number;
    role: string;
    goal: string;
    instructions: string;
    usage_description?: string;
    features: string[];
    sub_agents: string[];
  }>,
  pattern: "single_agent" | "manager_workers" = "manager_workers"
): GateResult<BlueprintRequest> {
  try {
    // Convert flat to hierarchical
    const request = fromFlatAgentSpecs(sessionId, agentSpecs, pattern);

    // Validate the hierarchical structure
    return validateBlueprintGate(request);
  } catch (error) {
    return {
      valid: false,
      errors: [error instanceof Error ? error.message : "Failed to build blueprint request"],
    };
  }
}

/**
 * Quick validation check without full error details.
 * Useful for UI state management where you just need pass/fail.
 */
export function isValidArchitecture(data: unknown): boolean {
  return ArchitectureOutputSchema.safeParse(data).success;
}

export function isValidAgentSpec(data: unknown): boolean {
  return AgentSpecSchema.safeParse(data).success;
}

export function isValidBlueprintRequest(data: unknown): boolean {
  return BlueprintRequestSchema.safeParse(data).success;
}

/**
 * Collect validation errors from multiple agent specs.
 * Useful for batch validation before blueprint creation.
 */
export function validateAllAgentSpecs(
  specs: unknown[]
): { valid: boolean; errorsByIndex: Map<number, string[]> } {
  const errorsByIndex = new Map<number, string[]>();
  let allValid = true;

  specs.forEach((spec, index) => {
    const result = validateAgentSpecAuto(spec);
    if (!result.valid) {
      allValid = false;
      errorsByIndex.set(index, result.errors);
    }
  });

  return { valid: allValid, errorsByIndex };
}
