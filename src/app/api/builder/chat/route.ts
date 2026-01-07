import { NextRequest, NextResponse } from "next/server";
import { streamFromAgent, getCredentialsFromCookies } from "@/lib/lyzr";
import { v4 as uuidv4 } from "uuid";

interface ChatRequest {
  manager_id: string;
  message: string;
  session_id?: string;
}

export async function POST(request: NextRequest) {
  try {
    const body: ChatRequest = await request.json();
    const { manager_id, message, session_id } = body;

    if (!manager_id || !message) {
      return NextResponse.json(
        { error: "manager_id and message are required" },
        { status: 400 }
      );
    }

    // Get credentials from cookies
    const cookieHeader = request.headers.get("cookie");
    const { apiKey } = getCredentialsFromCookies(cookieHeader);

    if (!apiKey) {
      return NextResponse.json(
        { error: "API key not found. Please set up your credentials." },
        { status: 401 }
      );
    }

    // Generate session ID if not provided
    const chatSessionId = session_id || uuidv4();

    // Call the manager agent
    const response = await streamFromAgent({
      agentId: manager_id,
      apiKey,
      sessionId: chatSessionId,
      message,
      userId: "builder-chat-user",
    });

    return NextResponse.json({
      response,
      session_id: chatSessionId,
    });
  } catch (error) {
    console.error("Chat API error:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Internal server error" },
      { status: 500 }
    );
  }
}
