/**
 * Blueprint Schema
 *
 * Validates the complete blueprint creation request.
 * Gate 3: All Agents Approved → Create Blueprint transition.
 *
 * This ensures the full hierarchy is valid before sending to the API:
 * - Manager has sub_agents linking to workers
 * - All workers referenced in sub_agents exist
 * - Pattern type is preserved from architecture
 */

import { z } from "zod";
import { ManagerSpecSchema, WorkerSpecSchema } from "./agent-spec";

// Blueprint creation request - explicit hierarchy
export const BlueprintRequestSchema = z
  .object({
    session_id: z.string().min(1, "Session ID is required"),

    // Explicit hierarchy (not flat array!)
    manager: ManagerSpecSchema,
    // Workers array can be empty for single-agent blueprints
    workers: z.array(WorkerSpecSchema).default([]),

    // Orchestration metadata preserved from architecture
    pattern: z.enum(["single_agent", "manager_workers"]),

    // Optional delegation strategy from architecture reasoning
    delegation_strategy: z.string().optional(),
  })
  .refine(
    (data) => {
      // Skip validation for single-agent blueprints (no workers)
      if (data.workers.length === 0) return true;
      // Validate that manager's sub_agents match worker filenames
      const workerFilenames = new Set(data.workers.map((w) => w.filename));
      return data.manager.sub_agents.every((sa) => workerFilenames.has(sa));
    },
    {
      message: "Manager's sub_agents must reference existing worker filenames",
      path: ["manager", "sub_agents"],
    }
  )
  .refine(
    (data) => {
      // Skip validation for single-agent blueprints (no workers)
      if (data.workers.length === 0) return true;
      // Validate all workers are referenced in manager's sub_agents
      const subAgentSet = new Set(data.manager.sub_agents);
      return data.workers.every((w) => subAgentSet.has(w.filename));
    },
    {
      message: "All workers must be referenced in manager's sub_agents",
      path: ["workers"],
    }
  )
  .refine(
    (data) => {
      // Ensure pattern matches worker count
      if (data.pattern === "single_agent" && data.workers.length > 0) return false;
      if (data.pattern === "manager_workers" && data.workers.length === 0) return false;
      return true;
    },
    {
      message: "Pattern must match worker count (single_agent = no workers, manager_workers = at least one)",
      path: ["pattern"],
    }
  );

export type BlueprintRequest = z.infer<typeof BlueprintRequestSchema>;

// Legacy flat array format (for backward compatibility during migration)
export const LegacyCreateRequestSchema = z.object({
  session_id: z.string().min(1, "Session ID is required"),
  agent_specs: z.array(
    z.object({
      filename: z.string(),
      is_manager: z.boolean(),
      agent_index: z.number(),
      name: z.string(),
      description: z.string(),
      model: z.string(),
      temperature: z.number(),
      role: z.string(),
      goal: z.string(),
      instructions: z.string(),
      usage_description: z.string().optional(),
      features: z.array(z.string()),
      sub_agents: z.array(z.string()),
    })
  ),
});

export type LegacyCreateRequest = z.infer<typeof LegacyCreateRequestSchema>;

/**
 * Convert from new BlueprintRequest to legacy flat array format.
 * Used during migration to maintain backward compatibility with existing API.
 */
export function toFlatAgentSpecs(request: BlueprintRequest): LegacyCreateRequest {
  const managerSpec = {
    ...request.manager,
    // Ensure sub_agents is set on manager
    sub_agents: request.manager.sub_agents,
  };

  const workerSpecs = request.workers.map((w) => ({
    ...w,
    // Ensure workers have empty sub_agents
    sub_agents: [] as string[],
  }));

  return {
    session_id: request.session_id,
    agent_specs: [managerSpec, ...workerSpecs],
  };
}

/**
 * Convert from legacy flat array to new hierarchical format.
 * Used to upgrade existing data to the new schema.
 */
export function fromFlatAgentSpecs(
  sessionId: string,
  agentSpecs: LegacyCreateRequest["agent_specs"],
  pattern: "single_agent" | "manager_workers" = "manager_workers"
): BlueprintRequest {
  const manager = agentSpecs.find((a) => a.is_manager);
  const workers = agentSpecs.filter((a) => !a.is_manager);

  if (!manager) {
    throw new Error("No manager found in agent specs");
  }

  // Ensure manager has sub_agents
  const managerWithSubAgents = {
    ...manager,
    is_manager: true as const,
    sub_agents: workers.map((w) => w.filename),
  };

  // Ensure workers have usage_description
  const workersWithUsage = workers.map((w) => ({
    ...w,
    is_manager: false as const,
    sub_agents: [] as string[],
    usage_description: w.usage_description || `Use ${w.name} for specialized tasks`,
  }));

  return {
    session_id: sessionId,
    manager: managerWithSubAgents,
    workers: workersWithUsage,
    pattern,
  };
}
