import { NextRequest } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

// Fallback witty messages if AI call fails
const FALLBACK_MESSAGES = [
  "Convincing the AI to think creatively... 🧠",
  "Teaching agents the fine art of task delegation... 📋",
  "Brewing some intelligent responses... ☕",
  "Polishing the blueprints... ✨",
  "Consulting the oracle of automation... 🔮",
  "Spinning up the creativity engines... ⚙️",
  "Gathering wisdom from the cloud... ☁️",
  "Running the imagination processors... 🎨",
];

/**
 * GET /api/builder/loader-stream
 *
 * Server-Sent Events endpoint that streams entertaining loading messages.
 * Uses a fast AI model to generate contextual, funny loading text.
 *
 * Query params:
 * - stage: Current builder stage (e.g., "designing", "crafting", "creating")
 * - context: Additional context (e.g., agent name, domain)
 */
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const stage = searchParams.get("stage") || "building";
  const context = searchParams.get("context") || "";

  // Create a readable stream for SSE
  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    async start(controller) {
      let messageIndex = 0;
      let isOpen = true;

      // Helper to send SSE message
      const sendMessage = (text: string) => {
        if (!isOpen) return;
        const data = JSON.stringify({ text });
        controller.enqueue(encoder.encode(`data: ${data}\n\n`));
      };

      // Try to get AI-generated messages from backend, fallback to local generation
      const generateMessage = async (): Promise<string> => {
        try {
          // Try backend first
          const response = await fetch(
            `${BACKEND_URL}/api/v1/builder/loader-text?stage=${encodeURIComponent(stage)}&context=${encodeURIComponent(context)}`,
            { method: "GET", signal: AbortSignal.timeout(3000) }
          );

          if (response.ok) {
            const data = await response.json();
            return data.text || FALLBACK_MESSAGES[messageIndex % FALLBACK_MESSAGES.length];
          }
        } catch {
          // Backend not available, use fallback
        }

        // Use fallback messages with stage context
        const stagePrefix = getStagePrefix(stage);
        const fallback = FALLBACK_MESSAGES[messageIndex % FALLBACK_MESSAGES.length];
        return `${stagePrefix}${fallback}`;
      };

      // Send initial message immediately
      const initialMessage = await generateMessage();
      sendMessage(initialMessage);
      messageIndex++;

      // Send new messages every 4 seconds
      const interval = setInterval(async () => {
        if (!isOpen) {
          clearInterval(interval);
          return;
        }

        const message = await generateMessage();
        sendMessage(message);
        messageIndex++;

        // Stop after 10 messages (40 seconds max)
        if (messageIndex >= 10) {
          clearInterval(interval);
          isOpen = false;
          controller.close();
        }
      }, 4000);

      // Clean up on abort
      request.signal.addEventListener("abort", () => {
        isOpen = false;
        clearInterval(interval);
        controller.close();
      });
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}

// Get context-aware prefix for the stage
function getStagePrefix(stage: string): string {
  switch (stage) {
    case "designing":
      return "Designing architecture... ";
    case "design-review":
      return "Architecture ready! ";
    case "crafting":
      return "Crafting agent... ";
    case "craft-review":
      return "Agent crafted! ";
    case "creating":
      return "Creating blueprint... ";
    default:
      return "Working on it... ";
  }
}
