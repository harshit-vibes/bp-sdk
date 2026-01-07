import { NextRequest, NextResponse } from "next/server";

// Backend API URL - configurable via environment variable
const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

// Fallback suggestions when API fails
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

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // Forward request to FastAPI backend (v1 API)
    const response = await fetch(`${BACKEND_URL}/api/v1/builder/create-suggestions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      // Return fallback suggestions on error
      return NextResponse.json({
        suggestions: FALLBACK_SUGGESTIONS,
      });
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Create suggestions API error:", error);
    // Return fallback suggestions on error
    return NextResponse.json({
      suggestions: FALLBACK_SUGGESTIONS,
    });
  }
}
