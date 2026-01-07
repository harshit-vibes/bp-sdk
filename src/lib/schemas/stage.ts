/**
 * Stage Schema Definitions
 *
 * Unified 3-stage journey: Define → Build (N/M) → Complete
 */

import { z } from "zod";

/**
 * Screen types available in the journey
 * - guided-chat: Statement selector with dropdowns
 * - review: Markdown display with action buttons
 */
export const ScreenTypeSchema = z.enum(["guided-chat", "review"]);
export type ScreenType = z.infer<typeof ScreenTypeSchema>;

/**
 * Unified stage type for simplified progress
 */
export type UnifiedStage = "define" | "build" | "complete";

/**
 * Build progress for the Build stage
 */
export interface BuildProgress {
  current: number;
  total: number;
}

/**
 * Stage schema - defines a single stage in the journey
 */
export const StageSchema = z.object({
  /** Unique stage identifier (1-3 for unified stages) */
  id: z.number().int().min(1).max(5),

  /** Short stage name for footer indicator */
  name: z.string().min(1).max(20),

  /** Title displayed in header */
  title: z.string().min(1).max(50),

  /** Instruction text displayed below title */
  instruction: z.string().min(1).max(150),

  /** Which screen type this stage uses */
  screen: ScreenTypeSchema,
});

export type Stage = z.infer<typeof StageSchema>;

/**
 * Stage list schema - the complete journey
 */
export const StageListSchema = z.array(StageSchema).min(3).max(5);
export type StageList = z.infer<typeof StageListSchema>;

/**
 * Unified 3-stage configuration
 */
export const UNIFIED_STAGES: { id: UnifiedStage; name: string; title: string; instruction: string }[] = [
  {
    id: "define",
    name: "Describe",
    title: "Describe Your Need",
    instruction: "Click the underlined words to describe what you need",
  },
  {
    id: "build",
    name: "Design",
    title: "Design Your Solution",
    instruction: "Review and approve your solution",
  },
  {
    id: "complete",
    name: "Create",
    title: "Ready to Use",
    instruction: "Your solution has been created",
  },
];

/**
 * Default stages configuration (legacy, for backward compatibility)
 */
export const DEFAULT_STAGES: StageList = [
  {
    id: 1,
    name: "Define",
    title: "Define Your Problem",
    instruction: "Click the underlined phrases to describe your problem",
    screen: "guided-chat",
  },
  {
    id: 2,
    name: "Explore",
    title: "Explore Requirements",
    instruction: "Answer a few questions to refine your needs",
    screen: "review",
  },
  {
    id: 3,
    name: "Design",
    title: "Review Architecture",
    instruction: "Review the proposed agent structure",
    screen: "review",
  },
  {
    id: 4,
    name: "Build",
    title: "Review Agents",
    instruction: "Review and approve your agent specifications",
    screen: "review",
  },
  {
    id: 5,
    name: "Launch",
    title: "Blueprint Ready",
    instruction: "Your blueprint has been created",
    screen: "review",
  },
];

/**
 * Validate stages configuration
 */
export function validateStages(stages: unknown): StageList {
  return StageListSchema.parse(stages);
}

/**
 * Get stage by ID with validation
 */
export function getStageById(stages: StageList, id: number): Stage {
  const stage = stages.find((s) => s.id === id);
  if (!stage) {
    throw new Error(`Stage with id ${id} not found`);
  }
  return stage;
}
