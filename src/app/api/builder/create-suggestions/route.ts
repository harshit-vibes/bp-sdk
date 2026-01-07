import { NextRequest, NextResponse } from "next/server";
import { callAgentForJSON, getCredentialsFromCookies, AGENT_IDS } from "@/lib/lyzr";

// Fallback suggestions when agent is not available
const FALLBACK_SUGGESTIONS = [
  { label: "Start Fresh", value: "fresh", description: "New blueprint from scratch" },
  { label: "Similar Pattern", value: "similar", description: "Same structure, new purpose" },
  { label: "Different Domain", value: "different_domain", description: "New business area" },
  { label: "More Workers", value: "more_workers", description: "Larger team structure" },
  { label: "Simpler Design", value: "simpler", description: "Single agent approach" },
  { label: "Automation Focus", value: "automation", description: "Task automation blueprint" },
  { label: "Customer Facing", value: "customer", description: "Support or sales agents" },
  { label: "Internal Tools", value: "internal", description: "Back-office automation" },
];

interface CreateSuggestionsRequest {
  session_id: string;
  previous_blueprint?: {
    name?: string;
    description?: string;
    domain?: string;
  };
}

interface SuggestionsResult {
  suggestions?: Array<{ label: string; value: string; description: string }>;
}

/**
 * POST /api/builder/create-suggestions
 *
 * Generates suggestions for what blueprint to create next.
 */
export async function POST(request: NextRequest) {
  try {
    const body: CreateSuggestionsRequest = await request.json();
    const { session_id, previous_blueprint } = body;

    // Get credentials from cookies
    const cookieHeader = request.headers.get("cookie");
    const { apiKey } = getCredentialsFromCookies(cookieHeader);

    // If no API key or no idea suggester agent configured, return fallback
    if (!apiKey || !AGENT_IDS.ideaSuggester) {
      return NextResponse.json({ suggestions: FALLBACK_SUGGESTIONS });
    }

    try {
      let prompt = `Suggest 8 blueprint ideas for the user to create next. Each suggestion should have a label (short name), value (identifier), and description (one sentence).

Return ONLY a JSON object with a "suggestions" array.`;

      if (previous_blueprint?.name) {
        prompt = `The user just created a blueprint called "${previous_blueprint.name}"${previous_blueprint.domain ? ` in the ${previous_blueprint.domain} domain` : ""}.

Suggest 8 related or complementary blueprints they might want to create next. Each suggestion should have a label (short name), value (identifier), and description (one sentence).

Return ONLY a JSON object with a "suggestions" array.`;
      }

      const result = await callAgentForJSON<SuggestionsResult>({
        agentId: AGENT_IDS.ideaSuggester,
        apiKey,
        sessionId: session_id,
        message: prompt,
      });

      if (result.suggestions && result.suggestions.length > 0) {
        return NextResponse.json({ suggestions: result.suggestions.slice(0, 8) });
      }
    } catch (error) {
      console.error("Idea suggester error:", error);
    }

    // Return fallback on any error
    return NextResponse.json({ suggestions: FALLBACK_SUGGESTIONS });
  } catch (error) {
    console.error("Create suggestions API error:", error);
    return NextResponse.json({ suggestions: FALLBACK_SUGGESTIONS });
  }
}
