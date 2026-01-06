/**
 * Review Screen Schema Definitions
 *
 * Defines the structure for review screen content and actions
 */

import { z } from "zod";

/**
 * Blueprint result schema - returned when blueprint is created
 */
export const BlueprintResultSchema = z.object({
  /** Blueprint ID */
  id: z.string().min(1),

  /** Blueprint name */
  name: z.string().min(1),

  /** URL to view in Lyzr Studio */
  studio_url: z.string(),

  /** Manager agent ID for chat */
  manager_id: z.string().optional(),

  /** Organization ID */
  organization_id: z.string().optional(),

  /** Creation timestamp */
  created_at: z.string().optional(),

  /** Share type */
  share_type: z.string().optional(),
});

export type BlueprintResult = z.infer<typeof BlueprintResultSchema>;

/**
 * Review action types
 */
export const ReviewActionTypeSchema = z.enum([
  "approve",       // Approve and continue to next stage
  "revise",        // Request changes with feedback
  "reply",         // Reply in conversational mode
  "create_another" // Start over (complete state only)
]);

export type ReviewActionType = z.infer<typeof ReviewActionTypeSchema>;

/**
 * Review content schema - defines what's displayed in the review screen
 */
export const ReviewContentSchema = z.object({
  /** Markdown content to display */
  markdown: z.string(),

  /** Whether this is the final complete state */
  isComplete: z.boolean().optional().default(false),

  /** Blueprint result for complete state */
  blueprint: BlueprintResultSchema.optional(),

  /** Whether this is a conversational stage (affects button labels) */
  isConversational: z.boolean().optional().default(false),
});

export type ReviewContent = z.infer<typeof ReviewContentSchema>;

/**
 * Review state schema - tracks user interaction state
 */
export const ReviewStateSchema = z.object({
  /** Whether user is in revision/reply mode */
  isEditing: z.boolean().default(false),

  /** User's feedback/reply text */
  feedbackText: z.string().default(""),

  /** Whether actions are loading */
  isLoading: z.boolean().default(false),
});

export type ReviewState = z.infer<typeof ReviewStateSchema>;

/**
 * Agent preview schema - for HITL agent review
 */
export const AgentPreviewSchema = z.object({
  name: z.string(),
  role: z.string().optional(),
  goal: z.string().optional(),
  instructions: z.string().optional(),
  model: z.string().optional(),
  temperature: z.number().optional(),
  is_manager: z.boolean().optional(),
  usage_description: z.string().optional(),
});

export type AgentPreview = z.infer<typeof AgentPreviewSchema>;

/**
 * Architecture preview schema - for HITL architecture review
 */
export const ArchitecturePreviewSchema = z.object({
  manager: z.object({
    name: z.string(),
    purpose: z.string(),
  }).optional(),
  workers: z.array(z.object({
    name: z.string(),
    purpose: z.string(),
  })).optional().default([]),
});

export type ArchitecturePreview = z.infer<typeof ArchitecturePreviewSchema>;

/**
 * Validate blueprint result
 */
export function validateBlueprintResult(data: unknown): BlueprintResult {
  return BlueprintResultSchema.parse(data);
}

/**
 * Create review content for architecture HITL
 */
export function createArchitectureContent(
  preview: ArchitecturePreview,
  summary?: string
): string {
  let content = `# Proposed Architecture\n\n${summary || "Based on your requirements, here's the recommended structure:"}\n\n`;

  if (preview.manager) {
    content += `## Manager Agent\n\n**${preview.manager.name}**\n\n${preview.manager.purpose}\n\n`;
  }

  if (preview.workers && preview.workers.length > 0) {
    content += `## Worker Agents\n\n`;
    preview.workers.forEach((worker, i) => {
      content += `### ${i + 1}. ${worker.name}\n\n${worker.purpose}\n\n`;
    });
  }

  const pattern = preview.workers && preview.workers.length > 0
    ? "Manager + Workers"
    : "Single Agent";
  content += `---\n\n*This architecture uses the ${pattern} pattern.*`;

  return content;
}

/**
 * Create review content for agent HITL
 */
export function createAgentContent(
  agent: AgentPreview,
  summary?: string
): string {
  let content = `# Review Agent: ${agent.name}\n\n`;

  if (summary) {
    content += `${summary}\n\n`;
  }

  content += `## Overview\n\n`;
  content += `- **Type:** ${agent.is_manager ? "Manager" : "Worker"}\n`;
  if (agent.model) content += `- **Model:** ${agent.model}\n`;
  if (agent.temperature !== undefined) content += `- **Temperature:** ${agent.temperature}\n`;
  content += `\n`;

  if (agent.role) {
    content += `## Role\n\n${agent.role}\n\n`;
  }

  if (agent.goal) {
    content += `## Goal\n\n${agent.goal}\n\n`;
  }

  if (agent.usage_description) {
    content += `## When to Use\n\n${agent.usage_description}\n\n`;
  }

  if (agent.instructions) {
    content += `## Instructions\n\n\`\`\`\n${agent.instructions}\n\`\`\``;
  }

  return content;
}

/**
 * Create review content for blueprint success
 */
export function createSuccessContent(blueprint: BlueprintResult): string {
  return `# Blueprint Created Successfully!

Your blueprint **${blueprint.name}** has been created and is ready to use.

## What's Next?

1. **Test your blueprint** in Lyzr Studio
2. **Customize agents** further if needed
3. **Deploy to production** when ready

> Your blueprint includes all the agents configured based on your requirements.`;
}
