/**
 * Agent Fields Configuration
 *
 * Builds InfoItem arrays for editing agent specifications.
 * Used by ReviewScreen in edit mode to allow inline agent editing.
 */

import type { InfoItem, AgentYAMLSpec } from "@/lib/types";
import { FIELD_CONSTRAINTS } from "@/lib/validation";

// Model presets for the model selector
export const MODEL_PRESETS = [
  { value: "gpt-4o", label: "GPT-4o", provider: "OpenAI" },
  { value: "gpt-4o-mini", label: "GPT-4o Mini", provider: "OpenAI" },
  { value: "gpt-4.1", label: "GPT-4.1", provider: "OpenAI" },
  { value: "gpt-4.1-mini", label: "GPT-4.1 Mini", provider: "OpenAI" },
  { value: "anthropic/claude-sonnet-4-20250514", label: "Claude Sonnet 4", provider: "Anthropic" },
  { value: "anthropic/claude-3-5-sonnet-20241022", label: "Claude 3.5 Sonnet", provider: "Anthropic" },
  { value: "anthropic/claude-3-5-haiku-20241022", label: "Claude 3.5 Haiku", provider: "Anthropic" },
  { value: "gemini/gemini-2.0-flash", label: "Gemini 2.0 Flash", provider: "Google" },
  { value: "gemini/gemini-1.5-pro", label: "Gemini 1.5 Pro", provider: "Google" },
  { value: "groq/llama-3.3-70b-versatile", label: "Llama 3.3 70B", provider: "Groq" },
];

/**
 * Build InfoItem array for editing an agent specification
 */
export function buildAgentInfoItems(
  spec: AgentYAMLSpec,
  isManager: boolean
): InfoItem[] {
  const items: InfoItem[] = [
    {
      id: "name",
      question: "Agent Name",
      type: "text",
      required: true,
      default: spec.name,
      minLength: FIELD_CONSTRAINTS.name.min,
      maxLength: FIELD_CONSTRAINTS.name.max,
    },
    {
      id: "description",
      question: "Description",
      type: "textarea",
      required: true,
      default: spec.description,
      minLength: FIELD_CONSTRAINTS.description.min,
      rows: 3,
      placeholder: "A clear description of what this agent does...",
    },
    {
      id: "role",
      question: "Role",
      type: "text",
      required: true,
      default: spec.role,
      minLength: FIELD_CONSTRAINTS.role.min,
      maxLength: FIELD_CONSTRAINTS.role.max,
      placeholder: "e.g., Senior Software Architect, Data Analyst...",
    },
    {
      id: "goal",
      question: "Goal",
      type: "textarea",
      required: true,
      default: spec.goal,
      minLength: FIELD_CONSTRAINTS.goal.min,
      maxLength: FIELD_CONSTRAINTS.goal.max,
      rows: 2,
      placeholder: "The primary objective this agent strives to achieve...",
    },
    {
      id: "instructions",
      question: "Instructions",
      type: "textarea",
      required: true,
      default: spec.instructions,
      minLength: FIELD_CONSTRAINTS.instructions.min,
      rows: 8,
      placeholder: "Detailed instructions for how the agent should behave...",
    },
    {
      id: "model",
      question: "Model",
      type: "model",
      required: true,
      default: spec.model,
    },
    {
      id: "temperature",
      question: "Temperature",
      type: "number",
      required: true,
      default: String(spec.temperature),
      minValue: FIELD_CONSTRAINTS.temperature.min,
      maxValue: FIELD_CONSTRAINTS.temperature.max,
      step: 0.1,
    },
  ];

  // Add usage_description for workers only
  if (!isManager) {
    items.push({
      id: "usage_description",
      question: "When to Use (for Manager)",
      type: "textarea",
      required: true,
      default: spec.usage_description || "",
      rows: 3,
      placeholder: "Describe when the manager should delegate tasks to this worker...",
    });
  }

  return items;
}

/**
 * Convert form answers back to AgentYAMLSpec partial
 */
export function answersToAgentSpec(
  original: AgentYAMLSpec,
  answers: Record<string, string>
): AgentYAMLSpec {
  return {
    ...original,
    name: answers.name || original.name,
    description: answers.description || original.description,
    role: answers.role || original.role,
    goal: answers.goal || original.goal,
    instructions: answers.instructions || original.instructions,
    model: answers.model || original.model,
    temperature: parseFloat(answers.temperature) || original.temperature,
    usage_description: answers.usage_description || original.usage_description,
  };
}

/**
 * Convert AgentYAMLSpec to form answers
 */
export function agentSpecToAnswers(spec: AgentYAMLSpec): Record<string, string> {
  return {
    name: spec.name,
    description: spec.description,
    role: spec.role,
    goal: spec.goal,
    instructions: spec.instructions,
    model: spec.model,
    temperature: String(spec.temperature),
    usage_description: spec.usage_description || "",
  };
}
