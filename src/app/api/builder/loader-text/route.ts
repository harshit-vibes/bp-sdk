import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

// Fallback loading messages by stage
const FALLBACK_MESSAGES: Record<string, string[]> = {
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

/**
 * GET /api/builder/loader-text
 *
 * Returns a witty loading text message for the given stage.
 * Tries backend first, falls back to local messages.
 */
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const stage = searchParams.get("stage") || "designing";
    const context = searchParams.get("context") || "";

    // Try backend first
    try {
      const backendUrl = new URL(`${BACKEND_URL}/api/v1/builder/loader-text`);
      backendUrl.searchParams.set("stage", stage);
      if (context) {
        backendUrl.searchParams.set("context", context);
      }

      const response = await fetch(backendUrl.toString(), {
        method: "GET",
        signal: AbortSignal.timeout(3000), // 3 second timeout
      });

      if (response.ok) {
        const data = await response.json();
        if (data.text) {
          return NextResponse.json(data);
        }
      }
    } catch {
      // Backend not available, fall through to fallback
    }

    // Generate fallback message
    const messages = FALLBACK_MESSAGES[stage] || FALLBACK_MESSAGES.designing;
    const randomIndex = Math.floor(Math.random() * messages.length);
    return NextResponse.json({ text: messages[randomIndex] });
  } catch (error) {
    console.error("Loader text API error:", error);
    return NextResponse.json(
      { text: "Loading..." },
      { status: 200 } // Return 200 even on error so UI doesn't break
    );
  }
}
