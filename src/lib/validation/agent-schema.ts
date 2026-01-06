/**
 * Agent Validation Schema
 *
 * Port of SDK Pydantic validation rules to TypeScript.
 * Rules sourced from: sdk/models.py AgentConfig class
 */

import type { AgentYAMLSpec } from "@/lib/types";

// ============================================================================
// Types
// ============================================================================

export interface ValidationError {
  field: string;
  message: string;
  type: "error";
}

export interface ValidationWarning {
  field: string;
  message: string;
  type: "warning";
}

export interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
  score: number; // 0-100 quality score
}

// ============================================================================
// Constants (from SDK models.py)
// ============================================================================

/** Generic terms that should not appear in role field */
export const GENERIC_TERMS = ["worker", "helper", "bot", "agent", "assistant"];

/** Valid features list from SDK */
export const VALID_FEATURES = [
  "memory",
  "voice",
  "context",
  "file_output",
  "image_output",
  "reflection",
  "groundedness",
  "fairness",
  "rai",
  "llm_judge",
];

/** Known valid model identifiers (aligned with agent-fields.ts) */
export const VALID_MODELS = [
  // OpenAI
  "gpt-4o",
  "gpt-4o-mini",
  "gpt-4.1",
  "gpt-4.1-mini",
  "gpt-4-turbo",
  "gpt-3.5-turbo",
  // Anthropic (with prefix)
  "anthropic/claude-sonnet-4-20250514",
  "anthropic/claude-3-5-sonnet-20241022",
  "anthropic/claude-3-5-haiku-20241022",
  "anthropic/claude-3-opus-20240229",
  // Google (with prefix)
  "gemini/gemini-2.0-flash",
  "gemini/gemini-1.5-pro",
  "gemini/gemini-1.5-flash",
  // Groq (with prefix)
  "groq/llama-3.3-70b-versatile",
  "groq/llama-3.1-70b-versatile",
  // Perplexity (with prefix)
  "perplexity/sonar-reasoning",
  "perplexity/sonar-reasoning-pro",
  "perplexity/sonar-deep-research",
];

/** Field constraints from SDK */
export const FIELD_CONSTRAINTS = {
  name: { min: 1, max: 100 },
  description: { min: 20, max: undefined },
  role: { min: 15, max: 80 },
  goal: { min: 50, max: 300 },
  instructions: { min: 50, minWords: 10 },
  temperature: { min: 0, max: 1 },
  top_p: { min: 0, max: 1 },
};

// ============================================================================
// Validation Functions
// ============================================================================

/**
 * Validate agent specification against SDK rules
 */
export function validateAgentSpec(spec: AgentYAMLSpec): ValidationResult {
  const errors: ValidationError[] = [];
  const warnings: ValidationWarning[] = [];

  // Name validation (1-100 chars)
  if (!spec.name || spec.name.length < FIELD_CONSTRAINTS.name.min) {
    errors.push({
      field: "name",
      message: "Name is required",
      type: "error",
    });
  } else if (spec.name.length > FIELD_CONSTRAINTS.name.max) {
    errors.push({
      field: "name",
      message: `Name must be at most ${FIELD_CONSTRAINTS.name.max} characters`,
      type: "error",
    });
  }

  // Description validation (min 20 chars)
  if (!spec.description || spec.description.length < FIELD_CONSTRAINTS.description.min) {
    errors.push({
      field: "description",
      message: `Description must be at least ${FIELD_CONSTRAINTS.description.min} characters`,
      type: "error",
    });
  }

  // Role validation (15-80 chars, no generic terms)
  if (spec.role) {
    if (spec.role.length < FIELD_CONSTRAINTS.role.min) {
      errors.push({
        field: "role",
        message: `Role must be at least ${FIELD_CONSTRAINTS.role.min} characters`,
        type: "error",
      });
    } else if (spec.role.length > FIELD_CONSTRAINTS.role.max) {
      errors.push({
        field: "role",
        message: `Role must be at most ${FIELD_CONSTRAINTS.role.max} characters`,
        type: "error",
      });
    }

    // Check for generic terms
    const lowerRole = spec.role.toLowerCase();
    for (const term of GENERIC_TERMS) {
      if (lowerRole.includes(term)) {
        warnings.push({
          field: "role",
          message: `Role contains generic term "${term}". Use more specific terminology.`,
          type: "warning",
        });
        break;
      }
    }
  }

  // Goal validation (50-300 chars)
  if (spec.goal) {
    if (spec.goal.length < FIELD_CONSTRAINTS.goal.min) {
      errors.push({
        field: "goal",
        message: `Goal must be at least ${FIELD_CONSTRAINTS.goal.min} characters`,
        type: "error",
      });
    } else if (spec.goal.length > FIELD_CONSTRAINTS.goal.max) {
      errors.push({
        field: "goal",
        message: `Goal must be at most ${FIELD_CONSTRAINTS.goal.max} characters`,
        type: "error",
      });
    }
  }

  // Instructions validation (min 50 chars, 10 words)
  if (!spec.instructions || spec.instructions.length < FIELD_CONSTRAINTS.instructions.min) {
    errors.push({
      field: "instructions",
      message: `Instructions must be at least ${FIELD_CONSTRAINTS.instructions.min} characters`,
      type: "error",
    });
  } else {
    const wordCount = spec.instructions.split(/\s+/).filter(Boolean).length;
    if (wordCount < FIELD_CONSTRAINTS.instructions.minWords) {
      errors.push({
        field: "instructions",
        message: `Instructions must have at least ${FIELD_CONSTRAINTS.instructions.minWords} words`,
        type: "error",
      });
    }
  }

  // Temperature validation (0-1)
  if (spec.temperature !== undefined) {
    if (spec.temperature < FIELD_CONSTRAINTS.temperature.min) {
      errors.push({
        field: "temperature",
        message: `Temperature must be at least ${FIELD_CONSTRAINTS.temperature.min}`,
        type: "error",
      });
    } else if (spec.temperature > FIELD_CONSTRAINTS.temperature.max) {
      errors.push({
        field: "temperature",
        message: `Temperature must be at most ${FIELD_CONSTRAINTS.temperature.max}`,
        type: "error",
      });
    }
  }

  // Model validation (warning for unknown models, not error)
  if (spec.model) {
    if (!VALID_MODELS.includes(spec.model)) {
      // Check if it looks like a valid model format (provider/model-name)
      const hasValidFormat = /^[a-z]+\/[a-z0-9.-]+$/i.test(spec.model) ||
                            /^gpt-[0-9.]+(-[a-z]+)?$/i.test(spec.model);
      if (!hasValidFormat) {
        warnings.push({
          field: "model",
          message: `Unknown model "${spec.model}". Ensure it's a valid model identifier.`,
          type: "warning",
        });
      }
    }
  } else {
    errors.push({
      field: "model",
      message: "Model is required",
      type: "error",
    });
  }

  // Features validation
  if (spec.features && Array.isArray(spec.features)) {
    for (const feature of spec.features) {
      if (!VALID_FEATURES.includes(feature)) {
        warnings.push({
          field: "features",
          message: `Unknown feature "${feature}"`,
          type: "warning",
        });
      }
    }
  }

  // Worker-specific: usage_description required for non-managers
  if (!spec.is_manager && (!spec.usage_description || spec.usage_description.trim() === "")) {
    warnings.push({
      field: "usage_description",
      message: "Workers should have a usage description explaining when the manager should use this worker",
      type: "warning",
    });
  }

  // Calculate quality score
  const score = calculateQualityScore(spec, errors, warnings);

  return {
    valid: errors.length === 0,
    errors,
    warnings,
    score,
  };
}

/**
 * Calculate quality score (0-100) based on field completeness and quality
 */
function calculateQualityScore(
  spec: AgentYAMLSpec,
  errors: ValidationError[],
  warnings: ValidationWarning[]
): number {
  let score = 100;

  // Deduct for errors (major deductions)
  score -= errors.length * 15;

  // Deduct for warnings (minor deductions)
  score -= warnings.length * 5;

  // Bonus for good field lengths
  if (spec.description && spec.description.length >= 50) {
    score += 5;
  }
  if (spec.instructions && spec.instructions.length >= 100) {
    score += 5;
  }
  if (spec.goal && spec.goal.length >= 100) {
    score += 5;
  }

  // Ensure score is in valid range
  return Math.max(0, Math.min(100, score));
}
