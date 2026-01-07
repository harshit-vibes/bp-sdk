import { NextRequest, NextResponse } from "next/server";

// Backend API URL - configurable via environment variable
const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // Forward request to FastAPI backend (v1 API)
    const response = await fetch(`${BACKEND_URL}/api/v1/builder/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      // Try to get error details from backend
      let errorDetail = `Backend error: ${response.status}`;
      try {
        const errorBody = await response.text();
        errorDetail = errorBody || errorDetail;
      } catch {
        // Couldn't read body
      }
      return NextResponse.json(
        { error: errorDetail },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Builder chat API error:", error);
    return NextResponse.json(
      {
        error: error instanceof Error ? error.message : "Internal server error",
      },
      { status: 500 }
    );
  }
}
