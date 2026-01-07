/**
 * Architecture Schema
 *
 * Validates the output from the Design Agent.
 * Pattern-agnostic: flat agents array with coordinator + specialists.
 */

import { z } from "zod";

// Agent info from architecture (lightweight, before full spec)
export const AgentInfoSchema = z.object({
  name: z
    .string()
    .min(1, "Agent name is required")
    .max(100, "Agent name must be under 100 characters"),
  role: z
    .string()
    .min(10, "Role must be at least 10 characters")
    .max(100, "Role must be under 100 characters"),
  goal: z
    .string()
    .min(20, "Goal must be at least 20 characters")
    .max(300, "Goal must be under 300 characters"),
});

export type AgentInfo = z.infer<typeof AgentInfoSchema>;

// Architecture output from Design Agent
// Pattern-agnostic: first agent is coordinator, rest are specialists
export const ArchitectureOutputSchema = z.object({
  reasoning: z
    .string()
    .min(1, "Architecture reasoning is required"),
  agents: z
    .array(AgentInfoSchema)
    .min(1, "At least one agent is required")
    .max(11, "Maximum 11 agents allowed (1 coordinator + 10 specialists)"),
});

export type ArchitectureOutput = z.infer<typeof ArchitectureOutputSchema>;

// Session context passed between stages
export const SessionContextSchema = z.object({
  session_id: z.string().min(1, "Session ID is required"),
  requirements: z.string().min(1, "Requirements are required"),
  architecture: ArchitectureOutputSchema.optional(),
});

export type SessionContext = z.infer<typeof SessionContextSchema>;
