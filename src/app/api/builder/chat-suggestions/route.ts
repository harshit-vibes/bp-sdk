import { NextRequest, NextResponse } from "next/server";

// Backend API URL - configurable via environment variable
const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // Forward request to FastAPI backend (v1 API)
    const response = await fetch(`${BACKEND_URL}/api/v1/builder/chat-suggestions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      // Return fallback suggestions on error
      return NextResponse.json({
        suggestions: [
          "Tell me more about this",
          "Can you show an example?",
          "What else can you help with?",
        ],
      });
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Chat suggestions API error:", error);
    // Return fallback suggestions on error
    return NextResponse.json({
      suggestions: [
        "Tell me more about this",
        "Can you show an example?",
        "What else can you help with?",
      ],
    });
  }
}
