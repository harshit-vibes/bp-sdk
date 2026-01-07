import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

// Fallback options if backend/AI call fails (8 options each)
const FALLBACK_OPTIONS: Record<string, Array<{ value: string; label: string; description?: string }>> = {
  role: [
    { value: "product manager", label: "Product Manager", description: "Building and shipping products" },
    { value: "customer success lead", label: "Customer Success", description: "Ensuring customer satisfaction" },
    { value: "sales leader", label: "Sales Leader", description: "Growing revenue and closing deals" },
    { value: "marketing director", label: "Marketing Director", description: "Driving awareness and demand" },
    { value: "operations manager", label: "Operations Manager", description: "Streamlining processes" },
    { value: "engineering lead", label: "Engineering Lead", description: "Building technical solutions" },
    { value: "HR manager", label: "HR Manager", description: "Managing people and culture" },
    { value: "founder", label: "Founder / Executive", description: "Leading the organization" },
  ],
  problem: [
    { value: "automate repetitive tasks that consume my team's time", label: "Automate Repetitive Work", description: "Free up time from manual tasks" },
    { value: "respond to customer inquiries faster and more consistently", label: "Faster Customer Response", description: "Improve response time and quality" },
    { value: "qualify and prioritize incoming leads efficiently", label: "Lead Qualification", description: "Focus on high-value prospects" },
    { value: "generate and optimize content at scale", label: "Content at Scale", description: "Create more content, faster" },
    { value: "extract insights from documents and data", label: "Extract Insights", description: "Make sense of information" },
    { value: "onboard and train team members effectively", label: "Team Onboarding", description: "Get people up to speed" },
    { value: "research and synthesize information quickly", label: "Research & Synthesis", description: "Gather and summarize knowledge" },
    { value: "coordinate work across multiple processes", label: "Process Coordination", description: "Orchestrate complex workflows" },
  ],
  domain: [
    { value: "customer support", label: "Customer Support", description: "Tickets, inquiries, help desk" },
    { value: "sales", label: "Sales", description: "Leads, deals, pipeline" },
    { value: "marketing", label: "Marketing", description: "Campaigns, content, demand gen" },
    { value: "human resources", label: "Human Resources", description: "Recruiting, policies, L&D" },
    { value: "product development", label: "Product", description: "Features, roadmap, feedback" },
    { value: "operations", label: "Operations", description: "Processes, efficiency, logistics" },
    { value: "finance", label: "Finance", description: "Accounting, reporting, analysis" },
    { value: "legal and compliance", label: "Legal & Compliance", description: "Contracts, policies, risk" },
  ],
};

interface OptionsRequest {
  slot_type: "role" | "problem" | "domain";
  context?: {
    role?: string;
    problem?: string;
  };
}

interface OptionsResponse {
  options: Array<{ value: string; label: string; description?: string }>;
}

/**
 * POST /api/builder/options
 *
 * Fetches dynamic options for statement slots.
 * Options can be contextualized based on previous selections.
 */
export async function POST(request: NextRequest) {
  try {
    const body: OptionsRequest = await request.json();
    const { slot_type, context } = body;

    // Validate slot type
    if (!["role", "problem", "domain"].includes(slot_type)) {
      return NextResponse.json(
        { error: "Invalid slot_type. Must be: role, problem, or domain" },
        { status: 400 }
      );
    }

    // Try backend first
    try {
      const response = await fetch(`${BACKEND_URL}/api/v1/builder/options`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ slot_type, context }),
        signal: AbortSignal.timeout(5000), // 5 second timeout
      });

      if (response.ok) {
        const data: OptionsResponse = await response.json();
        if (data.options && data.options.length >= 4) {
          return NextResponse.json(data);
        }
      }
    } catch {
      // Backend not available, fall through to fallback
    }

    // Generate contextual fallback options
    let options = [...FALLBACK_OPTIONS[slot_type]];

    // For problem and domain, we could filter/prioritize based on context
    // but for now just return the full list
    if (context?.role && slot_type === "problem") {
      // Could prioritize problems relevant to the role
      // For now, just return all options
    }

    if (context?.problem && slot_type === "domain") {
      // Could prioritize domains relevant to the problem
      // For now, just return all options
    }

    return NextResponse.json({ options });
  } catch (error) {
    console.error("Options API error:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Internal server error" },
      { status: 500 }
    );
  }
}
