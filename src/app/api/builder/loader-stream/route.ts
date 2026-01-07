import { NextRequest } from "next/server";

// Witty loading messages
const LOADING_MESSAGES = [
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
 *
 * Query params:
 * - stage: Current builder stage (e.g., "designing", "crafting", "creating")
 */
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const stage = searchParams.get("stage") || "building";

  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    async start(controller) {
      let messageIndex = 0;
      let isOpen = true;

      const sendMessage = (text: string) => {
        if (!isOpen) return;
        const data = JSON.stringify({ text });
        controller.enqueue(encoder.encode(`data: ${data}\n\n`));
      };

      const generateMessage = (): string => {
        const stagePrefix = getStagePrefix(stage);
        const fallback = LOADING_MESSAGES[messageIndex % LOADING_MESSAGES.length];
        return `${stagePrefix}${fallback}`;
      };

      // Send initial message immediately
      sendMessage(generateMessage());
      messageIndex++;

      // Send new messages every 4 seconds
      const interval = setInterval(() => {
        if (!isOpen) {
          clearInterval(interval);
          return;
        }

        sendMessage(generateMessage());
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
