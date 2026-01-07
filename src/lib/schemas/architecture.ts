/**
 * Architecture Schema
 *
 * Validates the output from the Architect Agent.
 * Gate 1: Architecture → Build transition.
 */

import { z } from "zod";

// Agent info from architecture (lightweight, before full spec)
export const AgentInfoSchema = z.object({
  name: z
    .string()
    .min(1, "Agent name is required")
    .max(100, "Agent name must be under 100 characters"),
  purpose: z
    .string()
    .min(1, "Agent purpose is required")
    .max(500, "Agent purpose must be under 500 characters"),
});

export type AgentInfo = z.infer<typeof AgentInfoSchema>;

// Architecture output from Architect Agent
export const ArchitectureOutputSchema = z
  .object({
    pattern: z.enum(["single_agent", "manager_workers"]),
    reasoning: z
      .string()
      .min(1, "Architecture reasoning is required")
      .optional(),
    manager: AgentInfoSchema,
    // Workers can be empty for single-agent blueprints
    workers: z
      .array(AgentInfoSchema)
      .max(10, "Maximum 10 worker agents allowed")
      .default([]),
  })
  .refine(
    (data) => {
      // Validate pattern matches worker count
      if (data.pattern === "single_agent") return data.workers.length === 0;
      if (data.pattern === "manager_workers") return data.workers.length >= 1;
      return true;
    },
    {
      message: "Pattern must match worker count (single_agent = 0 workers, manager_workers = 1+ workers)",
      path: ["pattern"],
    }
  );

export type ArchitectureOutput = z.infer<typeof ArchitectureOutputSchema>;

// Session context passed between stages
export const SessionContextSchema = z.object({
  session_id: z.string().min(1, "Session ID is required"),
  requirements: z.string().min(1, "Requirements are required"),
  architecture: ArchitectureOutputSchema.optional(),
});

export type SessionContext = z.infer<typeof SessionContextSchema>;
