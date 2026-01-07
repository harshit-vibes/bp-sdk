import { NextRequest, NextResponse } from "next/server";
import { callAgentForJSON, getCredentialsFromCookies, AGENT_IDS } from "@/lib/lyzr";

// Fallback suggestions when agent is not available
const FALLBACK_SUGGESTIONS = [
  "Tell me more about this",
  "Can you show an example?",
  "What else can you help with?",
];

interface ChatSuggestionsRequest {
  session_id: string;
  manager_id: string;
  messages: Array<{ role: string; content: string }>;
}

interface SuggestionsResult {
  suggestions?: string[];
}

/**
 * POST /api/builder/chat-suggestions
 *
 * Generates reply suggestions for the chat playground.
 */
export async function POST(request: NextRequest) {
  try {
    const body: ChatSuggestionsRequest = await request.json();
    const { session_id, messages } = body;

    // Get credentials from cookies
    const cookieHeader = request.headers.get("cookie");
    const { apiKey } = getCredentialsFromCookies(cookieHeader);

    // If no API key or no reply suggester agent configured, return fallback
    if (!apiKey || !AGENT_IDS.replySuggester) {
      return NextResponse.json({ suggestions: FALLBACK_SUGGESTIONS });
    }

    try {
      // Build context from recent messages
      const recentMessages = messages.slice(-4);
      const context = recentMessages
        .map((m) => `${m.role}: ${m.content}`)
        .join("\n");

      const prompt = `Based on this conversation, suggest 3 short follow-up questions the user might want to ask. Return ONLY a JSON object with a "suggestions" array of 3 strings.

Conversation:
${context}

Return JSON only.`;

      const result = await callAgentForJSON<SuggestionsResult>({
        agentId: AGENT_IDS.replySuggester,
        apiKey,
        sessionId: session_id,
        message: prompt,
      });

      if (result.suggestions && result.suggestions.length > 0) {
        return NextResponse.json({ suggestions: result.suggestions.slice(0, 3) });
      }
    } catch (error) {
      console.error("Reply suggester error:", error);
    }

    // Return fallback on any error
    return NextResponse.json({ suggestions: FALLBACK_SUGGESTIONS });
  } catch (error) {
    console.error("Chat suggestions API error:", error);
    return NextResponse.json({ suggestions: FALLBACK_SUGGESTIONS });
  }
}
