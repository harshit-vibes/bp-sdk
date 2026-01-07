import { NextRequest, NextResponse } from "next/server";
import { callAgentForJSON, getCredentialsFromCookies, AGENT_IDS } from "@/lib/lyzr";
import { v4 as uuidv4 } from "uuid";

interface ArchitectRequest {
  session_id?: string;
  requirements: string;
}

interface AgentResult {
  reasoning?: string;
  main_agent?: { name: string; purpose: string };
  specialists?: Array<{ name: string; purpose: string }>;
  // Old format support
  pattern?: string;
  manager?: { name: string; purpose: string };
  workers?: Array<{ name: string; purpose: string }>;
}

export async function POST(request: NextRequest) {
  try {
    const body: ArchitectRequest = await request.json();
    const { requirements, session_id } = body;

    if (!requirements) {
      return NextResponse.json(
        { error: "Requirements are required" },
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

    // Check agent ID is configured
    if (!AGENT_IDS.architect) {
      return NextResponse.json(
        { error: "Architect agent not configured. Set ARCHITECT_AGENT_ID env var." },
        { status: 500 }
      );
    }

    const sessionId = session_id || uuidv4();

    // Build prompt for architect agent
    const prompt = `Design a blueprint architecture for the following requirements:

${requirements}

Return ONLY valid JSON with the architecture proposal.`;

    // Call architect agent
    const result = await callAgentForJSON<AgentResult>({
      agentId: AGENT_IDS.architect,
      apiKey,
      sessionId,
      message: prompt,
    });

    // Transform to pattern-agnostic response format
    const response = transformToResponse(sessionId, result);

    return NextResponse.json(response);
  } catch (error) {
    console.error("Architect API error:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Internal server error" },
      { status: 500 }
    );
  }
}

/**
 * Transform agent result to response format.
 * Handles both old (manager/workers) and new (main_agent/specialists) schemas.
 */
function transformToResponse(sessionId: string, result: AgentResult) {
  // New pattern-agnostic schema (main_agent + specialists)
  if (result.main_agent) {
    const mainAgent = result.main_agent;
    const specialists = result.specialists || [];

    // Convert to flat agents array with role/goal
    const agents = [
      {
        name: mainAgent.name,
        role: mainAgent.purpose?.split(".")[0] || "Workflow coordinator",
        goal: mainAgent.purpose || "Orchestrate the workflow",
      },
      ...specialists.map((s) => ({
        name: s.name,
        role: s.purpose?.split(".")[0] || "Specialist",
        goal: s.purpose || "Handle specialized tasks",
      })),
    ];

    return {
      session_id: sessionId,
      reasoning: result.reasoning || "",
      agents,
    };
  }

  // Old schema (manager + workers)
  if (result.manager) {
    const agents = [
      {
        name: result.manager.name,
        role: result.manager.purpose?.split(".")[0] || "Workflow coordinator",
        goal: result.manager.purpose || "Orchestrate the workflow",
      },
      ...(result.workers || []).map((w) => ({
        name: w.name,
        role: w.purpose?.split(".")[0] || "Specialist",
        goal: w.purpose || "Handle specialized tasks",
      })),
    ];

    return {
      session_id: sessionId,
      reasoning: result.reasoning || "",
      agents,
    };
  }

  // Fallback - return as-is with empty agents
  return {
    session_id: sessionId,
    reasoning: result.reasoning || "",
    agents: [],
  };
}
