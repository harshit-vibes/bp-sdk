/**
 * Journey Schema Definitions
 *
 * Defines the overall journey state and HITL configuration
 */

import { z } from "zod";
import { BlueprintResultSchema, AgentPreviewSchema, ArchitecturePreviewSchema } from "./review";

/**
 * Message role schema
 */
export const MessageRoleSchema = z.enum(["user", "assistant"]);
export type MessageRole = z.infer<typeof MessageRoleSchema>;

/**
 * Chat message schema
 */
export const MessageSchema = z.object({
  id: z.string(),
  role: MessageRoleSchema,
  content: z.string(),
  timestamp: z.number().optional(),
});

export type Message = z.infer<typeof MessageSchema>;

/**
 * HITL type schema - defines types of human-in-the-loop checkpoints
 */
export const HITLTypeSchema = z.enum([
  "confirm_architecture",  // Review proposed architecture
  "review_agent",          // Review individual agent spec
  "review_blueprint",      // Review final blueprint
]);

export type HITLType = z.infer<typeof HITLTypeSchema>;

/**
 * HITL preview schema - content shown during HITL
 */
export const HITLPreviewSchema = z.object({
  /** Architecture preview for confirm_architecture */
  manager: z.object({
    name: z.string(),
    purpose: z.string(),
  }).optional(),
  workers: z.array(z.object({
    name: z.string(),
    purpose: z.string(),
  })).optional(),

  /** Agent YAML for review_agent */
  agent_yaml: AgentPreviewSchema.optional(),
});

export type HITLPreview = z.infer<typeof HITLPreviewSchema>;

/**
 * HITL state schema - current HITL checkpoint
 */
export const HITLStateSchema = z.object({
  /** Type of HITL checkpoint */
  type: HITLTypeSchema,

  /** Title shown to user */
  title: z.string(),

  /** Summary of work done */
  work_summary: z.string().optional(),

  /** Preview content */
  preview: HITLPreviewSchema.optional(),
});

export type HITLState = z.infer<typeof HITLStateSchema>;

/**
 * Journey state schema - complete state of the journey
 */
export const JourneyStateSchema = z.object({
  /** Current stage (1-5) */
  currentStage: z.number().int().min(1).max(5),

  /** Whether user has submitted the initial statement */
  hasSubmitted: z.boolean().default(false),

  /** Statement selections */
  selections: z.record(z.string(), z.string().nullable()).default({}),

  /** Chat messages */
  messages: z.array(MessageSchema).default([]),

  /** Current HITL checkpoint */
  hitl: HITLStateSchema.nullable().default(null),

  /** Created blueprint */
  blueprint: BlueprintResultSchema.nullable().default(null),

  /** Loading state */
  isLoading: z.boolean().default(false),

  /** Error message */
  error: z.string().nullable().default(null),
});

export type JourneyState = z.infer<typeof JourneyStateSchema>;

/**
 * Journey action schema - actions that can be taken
 */
export const JourneyActionSchema = z.discriminatedUnion("type", [
  z.object({
    type: z.literal("submit_statement"),
    statement: z.string(),
  }),
  z.object({
    type: z.literal("send_message"),
    message: z.string(),
  }),
  z.object({
    type: z.literal("hitl_approve"),
  }),
  z.object({
    type: z.literal("hitl_revise"),
    feedback: z.string(),
  }),
  z.object({
    type: z.literal("reset"),
  }),
]);

export type JourneyAction = z.infer<typeof JourneyActionSchema>;

/**
 * Initial journey state
 */
export const INITIAL_JOURNEY_STATE: JourneyState = {
  currentStage: 1,
  hasSubmitted: false,
  selections: {},
  messages: [],
  hitl: null,
  blueprint: null,
  isLoading: false,
  error: null,
};

/**
 * Determine current stage based on state
 */
export function computeCurrentStage(state: {
  hasSubmitted: boolean;
  hitl: HITLState | null;
  blueprint: { id: string } | null;
}): number {
  if (state.blueprint) return 5; // Launch
  if (state.hitl?.type === "review_agent" || state.hitl?.type === "review_blueprint") return 4; // Build
  if (state.hitl?.type === "confirm_architecture") return 3; // Design
  if (state.hasSubmitted) return 2; // Explore
  return 1; // Define
}

/**
 * Determine which screen type to show
 */
export function computeScreenType(state: {
  hasSubmitted: boolean;
  currentStage: number;
}): "guided-chat" | "review" {
  if (!state.hasSubmitted && state.currentStage === 1) {
    return "guided-chat";
  }
  return "review";
}

/**
 * Validate journey state
 */
export function validateJourneyState(state: unknown): JourneyState {
  return JourneyStateSchema.parse(state);
}

/**
 * Create a new message
 */
export function createMessage(
  role: MessageRole,
  content: string
): Message {
  return {
    id: `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    role,
    content,
    timestamp: Date.now(),
  };
}
