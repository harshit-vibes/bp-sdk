import { NextRequest, NextResponse } from "next/server";
import { callAgentForJSON, getCredentialsFromCookies, AGENT_IDS } from "@/lib/lyzr";

interface CraftRequest {
  session_id: string;
  agent_name: string;
  agent_purpose: string;
  is_manager: boolean;
  agent_index: number;
  context: string;
  worker_names: string[];
}

interface AgentYAMLSpec {
  filename: string;
  is_manager: boolean;
  agent_index: number;
  name: string;
  description: string;
  model: string;
  temperature: number;
  role: string;
  goal: string;
  instructions: string;
  usage_description?: string;
  features: string[];
  sub_agents: string[];
}

interface CraftResult {
  agent_yaml?: AgentYAMLSpec;
  // Agent might return the spec directly without wrapper
  filename?: string;
  name?: string;
  instructions?: string;
}

export async function POST(request: NextRequest) {
  try {
    const body: CraftRequest = await request.json();
    const {
      session_id,
      agent_name,
      agent_purpose,
      is_manager,
      agent_index,
      context,
      worker_names,
    } = body;

    if (!session_id || !agent_name) {
      return NextResponse.json(
        { error: "session_id and agent_name are required" },
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
    if (!AGENT_IDS.crafter) {
      return NextResponse.json(
        { error: "Crafter agent not configured. Set CRAFTER_AGENT_ID env var." },
        { status: 500 }
      );
    }

    // Build prompt for crafter agent
    const agentType = is_manager ? "manager" : "worker";
    let workerList = "";
    if (is_manager && worker_names.length > 0) {
      const workerFilenames = worker_names.map(
        (name) => `${name.toLowerCase().replace(/\s+/g, "-")}.yaml`
      );
      workerList = `\n\nThis manager has the following workers: ${worker_names.join(", ")}`;
      workerList += `\nWorker filenames for sub_agents: ${JSON.stringify(workerFilenames)}`;
    }

    const prompt = `Create a detailed specification for a ${agentType} agent.

Agent Name: ${agent_name}
Agent Purpose: ${agent_purpose}
Agent Index: ${agent_index}
Is Manager: ${is_manager}

Context about the blueprint:
${context}${workerList}

Return ONLY valid JSON with the agent_yaml specification.`;

    // Call crafter agent
    const result = await callAgentForJSON<CraftResult>({
      agentId: AGENT_IDS.crafter,
      apiKey,
      sessionId: session_id,
      message: prompt,
    });

    // Extract agent_yaml from result (handle both wrapped and direct response)
    const agentYaml = (result.agent_yaml || result) as Partial<AgentYAMLSpec>;

    // Ensure required fields have defaults
    const normalizedYaml: AgentYAMLSpec = {
      filename: agentYaml.filename || `${agent_name.toLowerCase().replace(/\s+/g, "-")}.yaml`,
      is_manager: is_manager,
      agent_index: agent_index,
      name: agentYaml.name || agent_name,
      description: agentYaml.description || agent_purpose,
      model: agentYaml.model || "gpt-4o-mini",
      temperature: agentYaml.temperature ?? 0.3,
      role: agentYaml.role || agent_purpose.split(".")[0],
      goal: agentYaml.goal || agent_purpose,
      instructions: agentYaml.instructions || "",
      usage_description: is_manager ? undefined : (agentYaml.usage_description || `Use ${agent_name} for ${agent_purpose}`),
      features: agentYaml.features || (is_manager ? ["memory"] : []),
      sub_agents: agentYaml.sub_agents || [],
    };

    return NextResponse.json({
      session_id,
      agent_yaml: normalizedYaml,
    });
  } catch (error) {
    console.error("Craft API error:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Internal server error" },
      { status: 500 }
    );
  }
}
