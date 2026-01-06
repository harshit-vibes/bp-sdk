/**
 * Pure derivation functions for builder state.
 *
 * These functions derive UI state from the agent response.
 * No side effects, no React hooks - just pure logic.
 */

import type { HITLSuggestion, BlueprintResult, InfoItem } from "@/lib/types";

/**
 * The minimal stored state for the builder.
 */
export interface BuilderState {
  /** User submitted the initial statement */
  hasSubmitted: boolean;
  /** Answers to HITL info_items */
  infoAnswers: Record<string, string>;
  /** Latest agent response - THE source of truth */
  lastResponse: AgentResponse | null;
  /** Backend session ID */
  sessionId: string | null;
  /** Request in progress */
  isLoading: boolean;
}

/**
 * Agent response structure - what drives UI state.
 */
export interface AgentResponse {
  /** The action the agent wants to take */
  action: "continue" | "hitl" | "create_blueprint";
  /** Message content for display */
  message: string;
  /** HITL suggestion if action is "hitl" */
  hitl?: HITLSuggestion;
  /** Created blueprint if complete */
  blueprint?: BlueprintResult;
}

/**
 * Stage number (1-5) for the journey.
 */
export type Stage = 1 | 2 | 3 | 4 | 5;

/**
 * Action mode determines which buttons to show.
 */
export type ActionMode = "submit" | "hitl" | "conversational" | "complete";

/**
 * Screen type determines which screen component to render.
 */
export type ScreenType = "guided-chat" | "review";

/**
 * Derive the current stage from builder state.
 *
 * Stage progression:
 * 1. Define - User hasn't submitted statement yet
 * 2. Explore - User submitted, agent is asking questions
 * 3. Design - Agent proposed architecture (confirm_architecture HITL)
 * 4. Build - Agent is crafting agents (review_agent/review_blueprint HITL)
 * 5. Launch - Blueprint created
 */
export function deriveStage(state: BuilderState): Stage {
  const { hasSubmitted, lastResponse } = state;

  // Stage 1: Define - haven't submitted yet
  if (!hasSubmitted) return 1;

  // Stage 5: Launch - blueprint exists
  if (lastResponse?.blueprint) return 5;

  // Stage 4: Build - reviewing agent or final blueprint
  const hitlType = lastResponse?.hitl?.type;
  if (hitlType === "review_agent" || hitlType === "review_blueprint") return 4;

  // Stage 3: Design - confirming architecture
  if (hitlType === "confirm_architecture") return 3;

  // Stage 2: Explore - conversational phase
  return 2;
}

/**
 * Derive the action mode from builder state.
 * This determines which buttons to show in the footer.
 */
export function deriveActionMode(state: BuilderState): ActionMode {
  const { hasSubmitted, lastResponse } = state;

  // Not yet submitted - show Submit button
  if (!hasSubmitted) return "submit";

  // Blueprint created - show Complete buttons
  if (lastResponse?.blueprint) return "complete";

  // HITL active - show Approve/Revise buttons
  if (lastResponse?.hitl) return "hitl";

  // Conversational - show Reply button
  return "conversational";
}

/**
 * Derive the screen type from builder state.
 * Simple: guided-chat for stage 1, review for everything else.
 */
export function deriveScreenType(state: BuilderState): ScreenType {
  return state.hasSubmitted ? "review" : "guided-chat";
}

/**
 * Check if all required info_items are answered.
 */
export function areInfoItemsComplete(
  infoItems: InfoItem[],
  answers: Record<string, string>
): boolean {
  const required = infoItems.filter((item) => item.required);
  return required.every((item) => !!answers[item.id]?.trim());
}

/**
 * Derive whether the primary button should be enabled.
 *
 * Rules:
 * - Disabled while loading
 * - For HITL mode: disabled until all required info_items answered
 * - For other modes: enabled by default (caller may add additional checks)
 */
export function deriveButtonEnabled(state: BuilderState): boolean {
  if (state.isLoading) return false;

  const mode = deriveActionMode(state);

  if (mode === "hitl") {
    const infoItems = state.lastResponse?.hitl?.info_items ?? [];
    return areInfoItemsComplete(infoItems, state.infoAnswers);
  }

  // For other modes, enabled by default
  return true;
}

/**
 * Get the info items from the current HITL, if any.
 */
export function getInfoItems(state: BuilderState): InfoItem[] {
  return state.lastResponse?.hitl?.info_items ?? [];
}

/**
 * Generate markdown from HITL preview data.
 * This creates structured content for architecture review.
 */
function generatePreviewMarkdown(hitl: HITLSuggestion): string | null {
  const preview = hitl.preview;
  if (!preview) return null;

  const lines: string[] = [];

  // Add work summary as intro
  if (hitl.work_summary) {
    lines.push(hitl.work_summary);
    lines.push("");
  }

  // Add pattern info
  if (preview.pattern) {
    lines.push(`**Pattern:** ${preview.pattern.replace(/_/g, " ")}`);
    lines.push("");
  }

  // Add manager section
  if (preview.manager) {
    lines.push("## Manager Agent");
    lines.push(`**${preview.manager.name}**`);
    lines.push("");
    lines.push(preview.manager.purpose);
    lines.push("");
  }

  // Add workers section
  if (preview.workers && preview.workers.length > 0) {
    lines.push("## Worker Agents");
    lines.push("");
    for (const worker of preview.workers) {
      lines.push(`### ${worker.name}`);
      lines.push(worker.purpose);
      lines.push("");
    }
  }

  // Add agent YAML for review_agent
  if (preview.agent_yaml) {
    lines.push("## Agent Configuration");
    lines.push("");
    if (preview.agent_yaml.name) {
      lines.push(`**Name:** ${preview.agent_yaml.name}`);
    }
    if (preview.agent_yaml.description) {
      lines.push("");
      lines.push(preview.agent_yaml.description);
    }
  }

  return lines.length > 0 ? lines.join("\n") : null;
}

/**
 * Get the review content to display.
 * For HITL with preview data, generates markdown from the preview.
 * Otherwise returns the last agent message, or a default loading message.
 */
export function getReviewContent(state: BuilderState): string {
  const hitl = state.lastResponse?.hitl;

  // If we have HITL with preview data, generate markdown from it
  if (hitl?.preview) {
    const previewMarkdown = generatePreviewMarkdown(hitl);
    if (previewMarkdown) {
      return previewMarkdown;
    }
  }

  // Fall back to the message
  if (state.lastResponse?.message) {
    return state.lastResponse.message;
  }
  if (state.isLoading) {
    return "Analyzing your requirements...";
  }
  return "";
}

/**
 * Create initial builder state.
 */
export function createInitialState(): BuilderState {
  return {
    hasSubmitted: false,
    infoAnswers: {},
    lastResponse: null,
    sessionId: null,
    isLoading: false,
  };
}
