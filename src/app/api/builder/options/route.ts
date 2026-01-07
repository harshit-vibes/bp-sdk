import { NextRequest, NextResponse } from "next/server";
import { callAgentForJSON, getCredentialsFromCookies, AGENT_IDS } from "@/lib/lyzr";

// Fallback options for each slot type
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

interface OptionsResult {
  options?: Array<{ value: string; label: string; description?: string }>;
}

/**
 * POST /api/builder/options
 *
 * Fetches dynamic options for statement slots.
 * Calls the options agent if available, falls back to static options.
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

    // Get credentials from cookies
    const cookieHeader = request.headers.get("cookie");
    const { apiKey } = getCredentialsFromCookies(cookieHeader);

    // Try to call the options agent if configured
    if (apiKey && AGENT_IDS.options) {
      try {
        const prompt = `Generate 8 options for the "${slot_type}" slot in a blueprint builder statement.
${context?.role ? `Context - User role: ${context.role}` : ""}
${context?.problem ? `Context - Problem: ${context.problem}` : ""}

Return ONLY a JSON object with an "options" array. Each option should have:
- value: the actual value (lowercase)
- label: display label (Title Case)
- description: short description (5-10 words)`;

        const result = await callAgentForJSON<OptionsResult>({
          agentId: AGENT_IDS.options,
          apiKey,
          sessionId: `options-${Date.now()}`,
          message: prompt,
        });

        if (result.options && result.options.length >= 4) {
          return NextResponse.json({ options: result.options.slice(0, 8) });
        }
      } catch (error) {
        console.error("Options agent error, using fallback:", error);
      }
    }

    // Fallback to static options
    return NextResponse.json({ options: FALLBACK_OPTIONS[slot_type] });
  } catch (error) {
    console.error("Options API error:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Internal server error" },
      { status: 500 }
    );
  }
}
