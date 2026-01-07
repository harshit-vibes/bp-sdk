import { NextRequest, NextResponse } from "next/server";
import { callAgentForJSON, getCredentialsFromCookies, AGENT_IDS } from "@/lib/lyzr";

// Default suggestions by type (fallback)
const DEFAULT_SUGGESTIONS: Record<string, string[]> = {
  architecture: [
    "Add more worker agents",
    "Simplify the structure",
    "Add specialized roles",
    "Improve task delegation",
    "Add error handling",
    "Enhance coordination",
    "Split responsibilities",
    "Change the pattern",
  ],
  agent: [
    "Add detailed steps",
    "Clarify the goal",
    "Improve instructions",
    "Add edge cases",
    "Enhance output format",
    "Add constraints",
    "Simplify the role",
    "Change the tone",
  ],
};

interface SuggestRequest {
  session_id: string;
  type: "architecture" | "agent";
  agent_name?: string;
  role?: string;
  goal?: string;
  instructions?: string;
  context?: string;
}

interface SuggestResult {
  suggestions?: string[];
}

/**
 * POST /api/builder/suggest
 *
 * Generates contextual revision suggestions based on current spec.
 * Calls the suggest agent if available, falls back to static/generated suggestions.
 */
export async function POST(request: NextRequest) {
  try {
    const body: SuggestRequest = await request.json();
    const { session_id, type, agent_name, role, goal, instructions, context } = body;
    const suggestionType = type || "agent";

    // Get credentials from cookies
    const cookieHeader = request.headers.get("cookie");
    const { apiKey } = getCredentialsFromCookies(cookieHeader);

    // Try to call the suggest agent if configured
    if (apiKey && AGENT_IDS.suggest) {
      try {
        const prompt = `Generate 8 revision suggestions for ${suggestionType === "architecture" ? "a blueprint architecture" : `an agent named "${agent_name}"`}.

${suggestionType === "agent" && role ? `Agent role: ${role}` : ""}
${suggestionType === "agent" && goal ? `Agent goal: ${goal}` : ""}
${suggestionType === "agent" && instructions ? `Current instructions (first 500 chars): ${instructions.slice(0, 500)}` : ""}
${context ? `Context: ${context}` : ""}

Return ONLY a JSON object with a "suggestions" array containing 8 short, actionable suggestion strings (5-10 words each).
Focus on practical improvements the user can make.`;

        const result = await callAgentForJSON<SuggestResult>({
          agentId: AGENT_IDS.suggest,
          apiKey,
          sessionId: session_id || `suggest-${Date.now()}`,
          message: prompt,
        });

        if (result.suggestions && result.suggestions.length >= 4) {
          return NextResponse.json({ suggestions: result.suggestions.slice(0, 8) });
        }
      } catch (error) {
        console.error("Suggest agent error, using fallback:", error);
      }
    }

    // Fallback: generate contextual suggestions or use defaults
    let suggestions: string[];

    if (suggestionType === "agent" && agent_name) {
      suggestions = generateContextualSuggestions(body);
    } else {
      suggestions = [...DEFAULT_SUGGESTIONS[suggestionType]];
    }

    return NextResponse.json({ suggestions });
  } catch (error) {
    console.error("Suggest API error:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Internal server error" },
      { status: 500 }
    );
  }
}

/**
 * Generate context-aware suggestions based on agent spec (fallback)
 */
function generateContextualSuggestions(body: SuggestRequest): string[] {
  const suggestions: string[] = [];

  // Check for short goal
  if (body.goal && body.goal.length < 50) {
    suggestions.push("Make goal more specific");
  }

  // Check for short instructions
  if (body.instructions && body.instructions.length < 200) {
    suggestions.push("Add more detailed instructions");
  }

  // General suggestions
  suggestions.push(
    "Add edge case handling",
    "Improve output format",
    "Add guardrails and constraints",
    "Clarify role responsibilities",
    "Add example scenarios"
  );

  // Agent-type specific
  if (body.role?.toLowerCase().includes("manager") || body.role?.toLowerCase().includes("coordinator")) {
    suggestions.push("Improve delegation logic");
  } else {
    suggestions.push("Clarify when to be used");
  }

  suggestions.push("Other...");

  // Return first 8
  return suggestions.slice(0, 8);
}
