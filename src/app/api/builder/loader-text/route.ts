import { NextRequest, NextResponse } from "next/server";
import { callAgentForJSON, getCredentialsFromCookies, AGENT_IDS } from "@/lib/lyzr";

// Loading messages by stage (fallback)
const LOADING_MESSAGES: Record<string, string[]> = {
  designing: [
    "Consulting the architecture council...",
    "Sketching the blueprint foundation...",
    "Debating agent responsibilities...",
    "Mapping the delegation hierarchy...",
    "Calculating optimal worker count...",
    "Architecting your AI team...",
  ],
  crafting: [
    "Forging agent personality matrices...",
    "Calibrating instruction parameters...",
    "Infusing domain expertise...",
    "Polishing the goal alignment...",
    "Weaving the prompt tapestry...",
    "Fine-tuning the agent's voice...",
  ],
  creating: [
    "Materializing your blueprint...",
    "Registering agents in the system...",
    "Establishing the hierarchy links...",
    "Applying final configurations...",
    "Summoning your AI team...",
    "Almost there, one moment...",
  ],
  options: [
    "Scanning the multiverse of choices...",
    "Consulting the options oracle...",
    "Curating the perfect selection...",
    "Handpicking the best options...",
    "Reading between the lines...",
    "Finding your perfect match...",
  ],
};

interface LoaderResult {
  text?: string;
  message?: string;
}

/**
 * GET /api/builder/loader-text
 *
 * Returns a witty loading text message for the given stage.
 * Calls the loader agent if available, falls back to static messages.
 */
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const stage = searchParams.get("stage") || "designing";

    // Get credentials from cookies
    const cookieHeader = request.headers.get("cookie");
    const { apiKey } = getCredentialsFromCookies(cookieHeader);

    // Try to call the loader agent if configured
    if (apiKey && AGENT_IDS.loader) {
      try {
        const prompt = `Generate a single witty, creative loading message for the "${stage}" stage of building an AI agent blueprint.

Stage meanings:
- designing: Analyzing requirements and designing the agent architecture
- crafting: Writing detailed instructions and configurations for each agent
- creating: Creating the agents and assembling the blueprint in the system
- options: Loading dynamic options for user selection

Return ONLY a JSON object with a "text" field containing ONE creative loading message (10-20 words).
Be playful, slightly humorous, and reference AI/agents in a fun way.`;

        const result = await callAgentForJSON<LoaderResult>({
          agentId: AGENT_IDS.loader,
          apiKey,
          sessionId: `loader-${Date.now()}`,
          message: prompt,
        });

        if (result.text || result.message) {
          return NextResponse.json({ text: result.text || result.message });
        }
      } catch (error) {
        console.error("Loader agent error, using fallback:", error);
      }
    }

    // Fallback to static messages
    const messages = LOADING_MESSAGES[stage] || LOADING_MESSAGES.designing;
    const randomIndex = Math.floor(Math.random() * messages.length);

    return NextResponse.json({ text: messages[randomIndex] });
  } catch (error) {
    console.error("Loader text API error:", error);
    return NextResponse.json(
      { text: "Loading..." },
      { status: 200 }
    );
  }
}
