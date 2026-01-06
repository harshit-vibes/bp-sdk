/**
 * Utility functions for parsing structured agent responses.
 * Extracted from use-chat.ts for testability.
 *
 * With JSON output mode enabled, the agent returns pure JSON.
 * Legacy markdown mode (```json blocks) is kept for backward compatibility.
 */

import type { HITLSuggestion } from "@/lib/types";

export interface ParsedResponse {
  message: string;
  hitl: HITLSuggestion | null;
  blueprint_yaml: object | null;
}

/**
 * Repair JSON with unescaped control characters in string values.
 * LLM streaming can result in actual newlines inside string values,
 * which is invalid JSON. This function escapes them.
 */
export function repairJson(text: string): string {
  let result = "";
  let inString = false;
  let escape = false;

  for (let i = 0; i < text.length; i++) {
    const char = text[i];

    if (escape) {
      result += char;
      escape = false;
      continue;
    }

    if (char === "\\") {
      escape = true;
      result += char;
      continue;
    }

    if (char === '"') {
      inString = !inString;
      result += char;
      continue;
    }

    // If we're inside a string, escape control characters
    if (inString) {
      if (char === "\n") {
        result += "\\n";
      } else if (char === "\r") {
        result += "\\r";
      } else if (char === "\t") {
        result += "\\t";
      } else {
        result += char;
      }
    } else {
      result += char;
    }
  }

  return result;
}

/**
 * Extract the best message from a parsed response.
 * For HITL responses, prioritize work_summary (full architecture) over message (brief intro).
 */
function extractMessage(parsed: { message?: string; hitl?: { work_summary?: string } }): string {
  if (parsed.hitl?.work_summary) {
    return parsed.hitl.work_summary;
  }
  return parsed.message || "";
}

/**
 * Parse structured response from agent.
 *
 * Priority:
 * 1. Pure JSON (JSON output mode) - agent returns {"action": "...", "message": "...", ...}
 * 2. Repaired JSON (with unescaped control chars fixed)
 * 3. Legacy markdown with ```json blocks (backward compatibility)
 * 4. Plain text fallback
 */
export function parseStructuredResponse(text: string): ParsedResponse {
  const trimmed = text.trim();

  // PRIMARY: Try direct JSON parsing (JSON output mode)
  // The agent should return: {"action": "continue|hitl|create_blueprint", "message": "...", ...}
  try {
    const parsed = JSON.parse(trimmed);
    if (parsed.action && typeof parsed.message === "string") {
      return {
        message: extractMessage(parsed),
        hitl: parsed.action === "hitl" && parsed.hitl ? parsed.hitl as HITLSuggestion : null,
        blueprint_yaml: parsed.action === "create_blueprint" ? parsed.blueprint_yaml : null,
      };
    }
  } catch {
    // Not valid JSON, try repair
  }

  // SECONDARY: Try to repair JSON with unescaped control characters
  // LLM streaming sometimes outputs actual newlines inside strings
  try {
    const repaired = repairJson(trimmed);
    const parsed = JSON.parse(repaired);
    if (parsed.action && typeof parsed.message === "string") {
      return {
        message: extractMessage(parsed),
        hitl: parsed.action === "hitl" && parsed.hitl ? parsed.hitl as HITLSuggestion : null,
        blueprint_yaml: parsed.action === "create_blueprint" ? parsed.blueprint_yaml : null,
      };
    }
  } catch {
    // Still not valid JSON, try legacy markdown
  }

  // LEGACY: Look for JSON code block (```json ... ```)
  // Kept for backward compatibility with older agent versions
  const codeBlockMatch = text.match(/```json\s*([\s\S]*?)```/);

  if (codeBlockMatch) {
    let jsonContent = codeBlockMatch[1].trim();

    // Unescape the content - backend may send with escaped characters
    jsonContent = jsonContent
      .replace(/\\n/g, '\n')
      .replace(/\\"/g, '"')
      .replace(/\\\\/g, '\\');

    try {
      const parsed = JSON.parse(jsonContent);
      if (parsed.action === "hitl" && parsed.hitl) {
        const textOutsideCodeBlock = text.replace(/```json[\s\S]*?```/, "").trim();
        const message = textOutsideCodeBlock || parsed.hitl.work_summary || parsed.message || "";
        return {
          message,
          hitl: parsed.hitl as HITLSuggestion,
          blueprint_yaml: null,
        };
      }
      // Handle create_blueprint in legacy mode too
      if (parsed.action === "create_blueprint" && parsed.blueprint_yaml) {
        const textOutsideCodeBlock = text.replace(/```json[\s\S]*?```/, "").trim();
        const message = textOutsideCodeBlock || parsed.message || "";
        return {
          message,
          hitl: null,
          blueprint_yaml: parsed.blueprint_yaml,
        };
      }
    } catch {
      // JSON parse failed
    }
  }

  // FALLBACK: No structured response found, return as plain text
  return { message: text, hitl: null, blueprint_yaml: null };
}
