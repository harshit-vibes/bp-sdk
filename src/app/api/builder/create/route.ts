import { NextRequest, NextResponse } from "next/server";
import { getCredentialsFromCookies } from "@/lib/lyzr";

const AGENT_API_URL = "https://agent-prod.studio.lyzr.ai";
const BLUEPRINT_API_URL = "https://pagos-prod.studio.lyzr.ai";

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

interface CreateRequest {
  session_id: string;
  agent_specs?: AgentYAMLSpec[];
  readme?: string;
}

interface ManagedAgent {
  id: string;
  name: string;
  tool_usage_description: string;
}

export async function POST(request: NextRequest) {
  try {
    const body: CreateRequest = await request.json();
    const { session_id, agent_specs, readme } = body;

    if (!session_id) {
      return NextResponse.json(
        { error: "session_id is required" },
        { status: 400 }
      );
    }

    if (!agent_specs || agent_specs.length === 0) {
      return NextResponse.json(
        { error: "agent_specs are required" },
        { status: 400 }
      );
    }

    // Get credentials from cookies
    const cookieHeader = request.headers.get("cookie");
    const { apiKey, bearerToken, orgId } = getCredentialsFromCookies(cookieHeader);

    if (!apiKey || !bearerToken || !orgId) {
      return NextResponse.json(
        { error: "Missing credentials. Please set up API key, bearer token, and org ID." },
        { status: 401 }
      );
    }

    // Separate manager and workers
    const managerSpec = agent_specs.find((s) => s.is_manager);
    const workerSpecs = agent_specs.filter((s) => !s.is_manager);

    if (!managerSpec) {
      return NextResponse.json(
        { error: "Manager agent spec is required" },
        { status: 400 }
      );
    }

    // Track created agents for rollback
    const createdAgentIds: string[] = [];

    try {
      // 1. Create WORKERS FIRST (SDK pattern)
      const workerIds: string[] = [];
      const workersData: Array<{ id: string; spec: AgentYAMLSpec }> = [];

      for (const workerSpec of workerSpecs) {
        const workerId = await createAgent(apiKey, workerSpec, orgId);
        createdAgentIds.push(workerId);
        workerIds.push(workerId);
        workersData.push({ id: workerId, spec: workerSpec });
      }

      // 2. Build managed_agents list for manager
      // Use workersData (which has correct id-spec pairing) to avoid index mismatch bugs
      const managedAgents: ManagedAgent[] = workersData.map(({ id, spec }) => ({
        id,
        name: spec.name,
        tool_usage_description: spec.usage_description || `Use ${spec.name} for specialized tasks`,
      }));

      // 3. Create MANAGER with managed_agents
      const managerId = await createManagerAgent(apiKey, managerSpec, orgId, managedAgents);
      createdAgentIds.push(managerId);

      // 4. Build tree structure
      const tree = buildBlueprintTree(
        { id: managerId, spec: managerSpec },
        workersData,
        managedAgents
      );

      // 5. Create blueprint with unique name
      const timestamp = Date.now().toString(36).slice(-4);
      const blueprintName = managerSpec.name
        .replace("Coordinator", "Blueprint")
        .replace("Manager", "Blueprint") + `-${timestamp}`;

      // Build blueprint_data (matches SDK structure)
      const blueprintData = {
        name: blueprintName,
        orchestration_type: "Manager Agent",
        manager_agent_id: managerId,
        agents: tree.agents,
        nodes: tree.nodes,
        edges: tree.edges,
        tree_structure: {
          nodes: tree.nodes,
          edges: tree.edges,
        },
      };

      // Build payload (matches SDK's build_blueprint_payload)
      const blueprintPayload: Record<string, unknown> = {
        name: blueprintName,
        description: managerSpec.description,
        orchestration_type: "Manager Agent",
        orchestration_name: blueprintName,
        blueprint_data: blueprintData,
        share_type: "private",
        tags: [],
        is_template: false,
        category: "general",
      };

      // Add README documentation if provided (matches SDK structure)
      if (readme) {
        blueprintPayload.blueprint_info = {
          documentation_data: {
            markdown: readme,
          },
          type: "markdown",
        };
      }

      const blueprintResponse = await fetch(
        `${BLUEPRINT_API_URL}/api/v1/blueprints/blueprints?organization_id=${orgId}`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${bearerToken}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify(blueprintPayload),
        }
      );

      if (!blueprintResponse.ok) {
        const errorText = await blueprintResponse.text().catch(() => "Unknown error");
        throw new Error(`Failed to create blueprint: ${blueprintResponse.status} - ${errorText}`);
      }

      const blueprintResult = await blueprintResponse.json();
      const blueprintId = blueprintResult._id || blueprintResult.id;

      return NextResponse.json({
        session_id,
        blueprint_id: blueprintId,
        blueprint_name: blueprintName,
        studio_url: `https://studio.lyzr.ai/lyzr-manager?blueprint=${blueprintId}`,
        manager_id: managerId,
        worker_ids: workerIds,
        organization_id: orgId,
        created_at: new Date().toISOString(),
        share_type: "private",
      });
    } catch (error) {
      // Rollback: delete any created agents
      for (const agentId of createdAgentIds) {
        try {
          await deleteAgent(apiKey, agentId);
        } catch {
          // Ignore rollback errors
        }
      }
      throw error;
    }
  } catch (error) {
    console.error("Create API error:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Internal server error" },
      { status: 500 }
    );
  }
}

/**
 * Provider mapping: model -> (provider_name, credential_id)
 */
const PROVIDER_MAP: Record<string, [string, string]> = {
  // OpenAI models
  "gpt-4o": ["OpenAI", "lyzr_openai"],
  "gpt-4o-mini": ["OpenAI", "lyzr_openai"],
  "o3": ["OpenAI", "lyzr_openai"],
  "o3-mini": ["OpenAI", "lyzr_openai"],
  "o4-mini": ["OpenAI", "lyzr_openai"],
  "o1-preview": ["OpenAI", "lyzr_openai"],
  "o1-mini": ["OpenAI", "lyzr_openai"],
  // Anthropic models
  "claude-sonnet-4-0": ["Anthropic", "lyzr_anthropic"],
  "claude-opus-4-0": ["Anthropic", "lyzr_anthropic"],
  "claude-3-5-sonnet-latest": ["Anthropic", "lyzr_anthropic"],
  // Google models
  "gemini-2.0-flash": ["Google", "lyzr_google"],
  "gemini-2.0-flash-exp": ["Google", "lyzr_google"],
  "gemini-1.5-pro": ["Google", "lyzr_google"],
  "gemini-1.5-flash": ["Google", "lyzr_google"],
  // Groq models
  "llama-3.3-70b-versatile": ["Groq", "lyzr_groq"],
  "llama-3.1-8b-instant": ["Groq", "lyzr_groq"],
  "mixtral-8x7b-32768": ["Groq", "lyzr_groq"],
  // Perplexity models
  "sonar-pro": ["Perplexity", "lyzr_perplexity"],
  "sonar": ["Perplexity", "lyzr_perplexity"],
  "sonar-reasoning-pro": ["Perplexity", "lyzr_perplexity"],
  "sonar-reasoning": ["Perplexity", "lyzr_perplexity"],
  // DeepSeek models
  "deepseek-reasoner": ["DeepSeek", "lyzr_deepseek"],
};

function getProviderInfo(model: string): [string, string] {
  // Check exact match first
  if (PROVIDER_MAP[model]) {
    return PROVIDER_MAP[model];
  }
  // Check prefixed models (legacy support)
  if (model.startsWith("anthropic/") || model.startsWith("claude")) {
    return ["Anthropic", "lyzr_anthropic"];
  } else if (model.startsWith("gemini/")) {
    return ["Google", "lyzr_google"];
  } else if (model.startsWith("groq/")) {
    return ["Groq", "lyzr_groq"];
  } else if (model.startsWith("bedrock/")) {
    return ["Aws-Bedrock", "lyzr_aws-bedrock"];
  } else if (model.startsWith("perplexity/")) {
    return ["Perplexity", "lyzr_perplexity"];
  } else if (model.startsWith("deepseek/")) {
    return ["DeepSeek", "lyzr_deepseek"];
  }
  // Default to OpenAI
  return ["OpenAI", "lyzr_openai"];
}

/**
 * Build features list from feature names (matches SDK implementation)
 */
function buildFeatures(features: string[]): Array<Record<string, unknown>> {
  const result: Array<Record<string, unknown>> = [];
  let priority = 0;

  for (const feature of features) {
    if (feature === "memory") {
      result.push({
        type: "MEMORY",
        config: {
          provider: "lyzr",
          max_messages_context_count: 10,
        },
        priority: priority++,
      });
    } else if (feature === "voice") {
      result.push({
        type: "VOICE",
        config: {},
        priority: priority++,
      });
    } else if (feature === "context") {
      result.push({
        type: "CONTEXT",
        config: {
          context_id: "",
          context_name: "",
        },
        priority: priority++,
      });
    } else if (feature === "file_output") {
      result.push({
        type: "FILEASOUTPUT",
        config: {},
        priority: priority++,
      });
    } else if (feature === "reflection") {
      result.push({
        type: "REFLECTION",
        config: {},
        priority: priority++,
      });
    }
  }

  return result;
}

/**
 * Create a worker agent via Agent API
 */
async function createAgent(
  apiKey: string,
  spec: AgentYAMLSpec,
  orgId: string
): Promise<string> {
  const [providerId, credentialId] = getProviderInfo(spec.model);

  const payload: Record<string, unknown> = {
    name: spec.name,
    description: spec.description,
    agent_instructions: spec.instructions,
    provider_id: providerId,
    model: spec.model,
    llm_credential_id: credentialId,
    temperature: spec.temperature,
    top_p: 1.0,
    response_format: { type: "text" },
    store_messages: true,
    file_output: false,
    template_type: "STANDARD",
    features: buildFeatures(spec.features || []),
    tool_configs: [],
    managed_agents: [],
    a2a_tools: [],
    examples: null,
    tools: [],
    files: [],
    artifacts: [],
    personas: [],
    messages: [],
    organization_id: orgId,
  };

  // Add persona fields
  if (spec.role) {
    payload.agent_role = spec.role;
  }
  if (spec.goal) {
    payload.agent_goal = spec.goal;
  }

  // Add usage_description for workers
  if (spec.usage_description) {
    payload.tool_usage_description = spec.usage_description;
  }

  const response = await fetch(`${AGENT_API_URL}/v3/agents/`, {
    method: "POST",
    headers: {
      "X-API-Key": apiKey,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorText = await response.text().catch(() => "Unknown error");
    throw new Error(`Failed to create agent ${spec.name}: ${response.status} - ${errorText}`);
  }

  const data = await response.json();
  return data.agent_id || data._id || data.id;
}

/**
 * Create manager agent with managed_agents list
 */
async function createManagerAgent(
  apiKey: string,
  spec: AgentYAMLSpec,
  orgId: string,
  managedAgents: ManagedAgent[]
): Promise<string> {
  const [providerId, credentialId] = getProviderInfo(spec.model);

  const payload: Record<string, unknown> = {
    name: spec.name,
    description: spec.description,
    agent_instructions: spec.instructions,
    provider_id: providerId,
    model: spec.model,
    llm_credential_id: credentialId,
    temperature: spec.temperature,
    top_p: 1.0,
    response_format: { type: "text" },
    store_messages: true,
    file_output: false,
    template_type: "MANAGER",
    features: buildFeatures(spec.features || []),
    tool_configs: [],
    managed_agents: managedAgents, // Include worker references
    a2a_tools: [],
    examples: null,
    tools: [],
    files: [],
    artifacts: [],
    personas: [],
    messages: [],
    organization_id: orgId,
  };

  // Add persona fields
  if (spec.role) {
    payload.agent_role = spec.role;
  }
  if (spec.goal) {
    payload.agent_goal = spec.goal;
  }

  const response = await fetch(`${AGENT_API_URL}/v3/agents/`, {
    method: "POST",
    headers: {
      "X-API-Key": apiKey,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorText = await response.text().catch(() => "Unknown error");
    throw new Error(`Failed to create manager ${spec.name}: ${response.status} - ${errorText}`);
  }

  const data = await response.json();
  return data.agent_id || data._id || data.id;
}

/**
 * Delete an agent (for rollback)
 */
async function deleteAgent(apiKey: string, agentId: string): Promise<void> {
  await fetch(`${AGENT_API_URL}/v3/agents/${agentId}`, {
    method: "DELETE",
    headers: {
      "X-API-Key": apiKey,
    },
  });
}

/**
 * Build the blueprint tree structure (ReactFlow format) - matches SDK
 */
const LEVEL_SPACING = 300;
const HORIZONTAL_SPACING = 500;

function calculateWorkerPositions(numWorkers: number): number[] {
  if (numWorkers === 0) return [];
  if (numWorkers === 1) return [0];

  const totalWidth = (numWorkers - 1) * HORIZONTAL_SPACING;
  const startX = -(totalWidth / 2);
  return Array.from({ length: numWorkers }, (_, i) => Math.floor(startX + i * HORIZONTAL_SPACING));
}

function buildAgentNode(
  agentId: string,
  spec: AgentYAMLSpec,
  position: { x: number; y: number },
  agentRole: "Manager" | "Worker",
  managedAgents: ManagedAgent[] = []
): Record<string, unknown> {
  return {
    id: agentId,
    type: "agent",
    position,
    data: {
      // Agent fields
      name: spec.name,
      description: spec.description,
      agent_instructions: spec.instructions,
      agent_role: spec.role,
      agent_goal: spec.goal,
      model: spec.model,
      temperature: spec.temperature,
      features: buildFeatures(spec.features || []),
      tool_usage_description: spec.usage_description || "",
      managed_agents: managedAgents,
      // ReactFlow required fields
      label: spec.name,
      template_type: agentRole === "Manager" ? "MANAGER" : "STANDARD",
      tool: "",
      agent_id: agentId,
    },
  };
}

function buildEdge(
  sourceId: string,
  targetId: string,
  usageDescription?: string
): Record<string, unknown> {
  const edge: Record<string, unknown> = {
    id: `edge-${sourceId}-${targetId}`,
    source: sourceId,
    target: targetId,
  };
  if (usageDescription) {
    edge.label = usageDescription;
    edge.data = { usageDescription };
  }
  return edge;
}

function buildBlueprintTree(
  manager: { id: string; spec: AgentYAMLSpec },
  workers: Array<{ id: string; spec: AgentYAMLSpec }>,
  managedAgents: ManagedAgent[]
) {
  const nodes: Array<Record<string, unknown>> = [];
  const edges: Array<Record<string, unknown>> = [];
  const agents: Record<string, Record<string, unknown>> = {};

  // Build manager node at center
  const managerNode = buildAgentNode(
    manager.id,
    manager.spec,
    { x: 0, y: 0 },
    "Manager",
    managedAgents
  );
  nodes.push(managerNode);

  // Store manager in agents dict
  agents[manager.id] = {
    name: manager.spec.name,
    description: manager.spec.description,
    agent_instructions: manager.spec.instructions,
    agent_role: manager.spec.role,
    agent_goal: manager.spec.goal,
    model: manager.spec.model,
    temperature: manager.spec.temperature,
    features: buildFeatures(manager.spec.features || []),
    template_type: "MANAGER",
    managed_agents: managedAgents,
  };

  // Calculate worker positions
  const workerXPositions = calculateWorkerPositions(workers.length);

  // Build worker nodes and edges
  workers.forEach((worker, index) => {
    const workerNode = buildAgentNode(
      worker.id,
      worker.spec,
      { x: workerXPositions[index], y: LEVEL_SPACING },
      "Worker"
    );
    nodes.push(workerNode);

    // Edge from manager to worker with usage description
    edges.push(buildEdge(manager.id, worker.id, worker.spec.usage_description));

    // Store worker in agents dict
    agents[worker.id] = {
      name: worker.spec.name,
      description: worker.spec.description,
      agent_instructions: worker.spec.instructions,
      agent_role: worker.spec.role,
      agent_goal: worker.spec.goal,
      model: worker.spec.model,
      temperature: worker.spec.temperature,
      features: buildFeatures(worker.spec.features || []),
      tool_usage_description: worker.spec.usage_description,
      template_type: "STANDARD",
      managed_agents: [],
    };
  });

  return {
    nodes,
    edges,
    agents,
  };
}
