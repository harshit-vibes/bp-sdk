import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

// Fallback suggestions if backend/AI call fails (8 options each)
const FALLBACK_SUGGESTIONS: Record<string, string[]> = {
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

interface SuggestResponse {
  suggestions: string[];
}

/**
 * POST /api/builder/suggest
 *
 * Generates 8 contextual revision suggestions based on current spec.
 * Uses a fast AI model for quick response times.
 */
export async function POST(request: NextRequest) {
  try {
    const body: SuggestRequest = await request.json();

    // Try backend first
    try {
      const response = await fetch(`${BACKEND_URL}/api/v1/builder/suggest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(5000), // 5 second timeout
      });

      if (response.ok) {
        const data: SuggestResponse = await response.json();
        return NextResponse.json(data);
      }
    } catch {
      // Backend not available, fall through to fallback
    }

    // Use fallback suggestions with context awareness
    const fallbackType = body.type || "agent";
    let suggestions = [...FALLBACK_SUGGESTIONS[fallbackType]];

    // Customize based on context
    if (body.type === "agent" && body.agent_name) {
      suggestions = generateContextualSuggestions(body);
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
 * Generate context-aware suggestions based on agent spec
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
  if (body.role?.toLowerCase().includes("manager")) {
    suggestions.push("Improve delegation logic");
  } else {
    suggestions.push("Clarify when to be used");
  }

  suggestions.push("Other...");

  // Return first 8
  return suggestions.slice(0, 8);
}
