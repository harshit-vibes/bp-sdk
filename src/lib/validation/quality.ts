/**
 * Quality Detection for Agent Content
 *
 * Detects placeholders, weak patterns, and other quality issues
 * that indicate incomplete or low-quality agent configurations.
 */

import type { ValidationWarning } from "./agent-schema";

// ============================================================================
// Placeholder Detection
// ============================================================================

/** Patterns that indicate placeholder/incomplete content */
const PLACEHOLDER_PATTERNS = [
  // Common placeholder markers
  /\bTODO\b/i,
  /\bFIXME\b/i,
  /\bXXX\b/i,
  /\bTBD\b/i,

  // Bracketed placeholders - match backend's strict patterns
  // Backend uses: r"\[.*\]" and r"\{.*\}" which matches ANY brackets
  /\[[^\]]+\]/,  // Any [content] in square brackets
  /\{[^}]+\}/,   // Any {content} in curly brackets

  // Generic placeholder text
  /lorem\s+ipsum/i,
  /example\s+text/i,
  /sample\s+text/i,
  /placeholder\s+text/i,

  // Template markers
  /<\/?[A-Z_]+>/,
  /\$\{[^}]+\}/,
  /\{\{[^}]+\}\}/,
];

/**
 * Detect placeholder patterns in text
 * @returns Array of detected placeholder strings
 */
export function detectPlaceholders(text: string): string[] {
  if (!text) return [];

  const detected: string[] = [];

  for (const pattern of PLACEHOLDER_PATTERNS) {
    const matches = text.match(pattern);
    if (matches) {
      detected.push(matches[0]);
    }
  }

  return detected;
}

// ============================================================================
// Weak Pattern Detection
// ============================================================================

/** Patterns that indicate weak/generic instructions */
const WEAK_INSTRUCTION_PATTERNS = [
  // Overly generic starts
  { pattern: /^do\s+stuff/i, message: "Starts with 'do stuff' - be more specific" },
  { pattern: /^help\s+user/i, message: "Starts with 'help user' - describe how" },
  { pattern: /^be\s+helpful/i, message: "Starts with 'be helpful' - describe specific behaviors" },
  { pattern: /^assist\s+with/i, message: "Starts with 'assist with' - describe specific actions" },

  // AI self-reference (breaks immersion)
  { pattern: /^you\s+are\s+an?\s+(ai|assistant|bot|chatbot)/i, message: "Avoid 'You are an AI' - use role framing instead" },
  { pattern: /^as\s+an?\s+(ai|assistant|bot|chatbot)/i, message: "Avoid 'As an AI' - use role framing instead" },
  { pattern: /^i\s+am\s+an?\s+(ai|assistant|bot|chatbot)/i, message: "Avoid 'I am an AI' - use role framing instead" },

  // Vague instructions
  { pattern: /\bdo\s+your\s+best\b/i, message: "'Do your best' is vague - specify success criteria" },
  { pattern: /\btry\s+to\b/i, message: "'Try to' is weak - use definitive language" },
  { pattern: /\bif\s+possible\b/i, message: "'If possible' adds uncertainty - be specific about when" },

  // Catch-all phrases
  { pattern: /\band\s+other\s+things\b/i, message: "'And other things' is vague - be exhaustive or remove" },
  { pattern: /\betc\.?\s*$/i, message: "Ending with 'etc' is vague - list all relevant items" },
];

/**
 * Detect weak instruction patterns
 * @returns Array of warnings about weak patterns found
 */
export function detectWeakInstructions(text: string): ValidationWarning[] {
  if (!text) return [];

  const warnings: ValidationWarning[] = [];

  for (const { pattern, message } of WEAK_INSTRUCTION_PATTERNS) {
    if (pattern.test(text)) {
      warnings.push({
        field: "instructions",
        message,
        type: "warning",
      });
    }
  }

  return warnings;
}

// ============================================================================
// Role Quality Detection
// ============================================================================

/** Generic terms to avoid in role field */
export const ROLE_GENERIC_TERMS = [
  "worker",
  "helper",
  "bot",
  "agent",
  "assistant",
  "ai",
  "system",
];

/**
 * Detect generic terms in role
 * @returns Array of detected generic terms
 */
export function detectGenericTerms(role: string): string[] {
  if (!role) return [];

  const detected: string[] = [];
  const lowerRole = role.toLowerCase();

  for (const term of ROLE_GENERIC_TERMS) {
    // Check for whole word match to avoid false positives
    const regex = new RegExp(`\\b${term}\\b`, "i");
    if (regex.test(lowerRole)) {
      detected.push(term);
    }
  }

  return detected;
}

// ============================================================================
// Content Quality Checks
// ============================================================================

/**
 * Check if text is too short to be meaningful
 */
export function isTooShort(text: string, minLength: number): boolean {
  return !text || text.trim().length < minLength;
}

/**
 * Check if text has too few words
 */
export function hasTooFewWords(text: string, minWords: number): boolean {
  if (!text) return true;
  const wordCount = text.split(/\s+/).filter(Boolean).length;
  return wordCount < minWords;
}

/**
 * Check if text is mostly uppercase (potentially shouting/low quality)
 */
export function isMostlyUppercase(text: string): boolean {
  if (!text || text.length < 10) return false;
  const letters = text.replace(/[^a-zA-Z]/g, "");
  if (letters.length === 0) return false;
  const uppercase = letters.replace(/[^A-Z]/g, "").length;
  return uppercase / letters.length > 0.7;
}

// ============================================================================
// Combined Quality Check
// ============================================================================

export interface QualityIssue {
  field: string;
  issue: string;
  severity: "low" | "medium" | "high";
}

/**
 * Run all quality checks on a text field
 */
export function checkFieldQuality(
  field: string,
  text: string,
  options?: {
    minLength?: number;
    minWords?: number;
    checkPlaceholders?: boolean;
    checkWeakPatterns?: boolean;
  }
): QualityIssue[] {
  const issues: QualityIssue[] = [];
  const opts = {
    minLength: 0,
    minWords: 0,
    checkPlaceholders: true,
    checkWeakPatterns: true,
    ...options,
  };

  // Check for placeholders
  if (opts.checkPlaceholders) {
    const placeholders = detectPlaceholders(text);
    for (const placeholder of placeholders) {
      issues.push({
        field,
        issue: `Contains placeholder "${placeholder}"`,
        severity: "high",
      });
    }
  }

  // Check for weak patterns (instructions only)
  if (opts.checkWeakPatterns && field === "instructions") {
    const weakPatterns = detectWeakInstructions(text);
    for (const warning of weakPatterns) {
      issues.push({
        field,
        issue: warning.message,
        severity: "medium",
      });
    }
  }

  // Check length
  if (opts.minLength > 0 && isTooShort(text, opts.minLength)) {
    issues.push({
      field,
      issue: `Too short (minimum ${opts.minLength} characters)`,
      severity: "medium",
    });
  }

  // Check word count
  if (opts.minWords > 0 && hasTooFewWords(text, opts.minWords)) {
    issues.push({
      field,
      issue: `Too few words (minimum ${opts.minWords} words)`,
      severity: "medium",
    });
  }

  // Check for excessive uppercase
  if (isMostlyUppercase(text)) {
    issues.push({
      field,
      issue: "Mostly uppercase - consider using normal case",
      severity: "low",
    });
  }

  return issues;
}
