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

// Agent data fetched from API (matches SDK pattern)
interface AgentData {
  name: string;
  description: string;
  agent_instructions: string;
  agent_role?: string;
  agent_goal?: string;
  model: string;
  temperature: number;
  template_type: string;
  tool_usage_description?: string;
  features: Array<Record<string, unknown>>;
  managed_agents: ManagedAgent[];
  // Allow additional fields from API
  [key: string]: unknown;
}

interface ManagedAgent {
  id: string;
  name: string;
  tool_usage_description: string;
}

/**
 * Fetch agent data from Agent API (matches SDK pattern)
 * The SDK ALWAYS fetches fresh data after creating agents
 */
async function fetchAgent(apiKey: string, agentId: string): Promise<AgentData> {
  const response = await fetch(`${AGENT_API_URL}/v3/agents/${agentId}`, {
    headers: { "X-API-Key": apiKey },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch agent ${agentId}: ${response.status}`);
  }

  const data = await response.json();

  // Sanitize: ensure arrays are never null (matches SDK's sanitize_agent_data)
  return {
    ...data,
    managed_agents: data.managed_agents || [],
    tool_configs: data.tool_configs || [],
    features: data.features || [],
    tools: data.tools || [],
    files: data.files || [],
    artifacts: data.artifacts || [],
    personas: data.personas || [],
    messages: data.messages || [],
    a2a_tools: data.a2a_tools || [],
  };
}

export async function POST(request: NextRequest) {
  try {
    const body: CreateRequest = await request.json();
    const { session_id, agent_specs, readme } = body;

    console.log("[CREATE] ===== SIMPLIFIED SDK PATTERN =====");
    console.log("[CREATE] Received specs count:", agent_specs?.length);

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
      // ===== SDK PATTERN: Create agents then FETCH fresh data =====

      // 1. Create WORKERS FIRST
      const workerIds: string[] = [];

      console.log("[CREATE] Step 1: Creating workers. Count:", workerSpecs.length);
      for (let i = 0; i < workerSpecs.length; i++) {
        const workerSpec = workerSpecs[i];
        console.log(`[CREATE] Creating worker ${i}: "${workerSpec.name}"`);
        const workerId = await createAgent(apiKey, workerSpec, orgId);
        console.log(`[CREATE] Worker ${i} created: ${workerId}`);
        createdAgentIds.push(workerId);
        workerIds.push(workerId);
      }

      // 2. Build managed_agents list for manager (using worker specs for names)
      const managedAgents: ManagedAgent[] = workerSpecs.map((spec, i) => ({
        id: workerIds[i],
        name: spec.name,
        tool_usage_description: spec.usage_description || `Use ${spec.name} for specialized tasks`,
      }));

      // 3. Create MANAGER with managed_agents
      console.log(`[CREATE] Step 2: Creating manager: "${managerSpec.name}"`);
      const managerId = await createManagerAgent(apiKey, managerSpec, orgId, managedAgents);
      console.log(`[CREATE] Manager created: ${managerId}`);
      createdAgentIds.push(managerId);

      // ===== KEY FIX: FETCH fresh data from API (like SDK does) =====
      console.log("[CREATE] Step 3: Fetching fresh agent data from API...");

      // Fetch manager data
      const managerData = await fetchAgent(apiKey, managerId);
      console.log(`[CREATE] Fetched manager: name="${managerData.name}", instrLen=${managerData.agent_instructions?.length}`);

      // Fetch all workers data
      const workersData: AgentData[] = [];
      for (let i = 0; i < workerIds.length; i++) {
        const workerData = await fetchAgent(apiKey, workerIds[i]);
        console.log(`[CREATE] Fetched worker ${i}: name="${workerData.name}", instrLen=${workerData.agent_instructions?.length}`);
        workersData.push(workerData);
      }

      // 4. Build tree using FETCHED data (not specs!)
      console.log("[CREATE] Step 4: Building tree from fetched data...");
      const tree = buildTreeFromAgentData(managerId, managerData, workerIds, workersData);

      // Log tree contents
      console.log("[CREATE] Tree agents:", Object.keys(tree.agents).map(id => {
        const a = tree.agents[id];
        return `${id.slice(-6)}:${a.name}`;
      }).join(", "));

      // 5. Create blueprint
      const timestamp = Date.now().toString(36).slice(-4);
      const blueprintName = managerSpec.name
        .replace("Coordinator", "Blueprint")
        .replace("Manager", "Blueprint") + `-${timestamp}`;

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

      if (readme) {
        blueprintPayload.blueprint_info = {
          documentation_data: {
            markdown: readme,
          },
          type: "markdown",
        };
      }

      console.log("[CREATE] Step 5: Creating blueprint...");
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

      console.log("[CREATE] ✅ Blueprint created:", blueprintId);
      console.log("[CREATE] ===== COMPLETE =====");

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
      console.log("[CREATE] Rolling back, deleting agents:", createdAgentIds);
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

  console.log(`[createAgent] Creating agent: name="${spec.name}", model="${spec.model}"`);
  console.log(`[createAgent] Instructions first 100:`, spec.instructions?.substring(0, 100));

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

  console.log(`[createManagerAgent] Creating manager: name="${spec.name}", model="${spec.model}"`);
  console.log(`[createManagerAgent] Instructions first 100:`, spec.instructions?.substring(0, 100));
  console.log(`[createManagerAgent] Role: "${spec.role}"`);
  console.log(`[createManagerAgent] Goal: "${spec.goal}"`);
  console.log(`[createManagerAgent] Managed agents count:`, managedAgents.length);
  managedAgents.forEach((ma, i) => {
    console.log(`[createManagerAgent]   managed_agents[${i}]: id="${ma.id}", name="${ma.name}"`);
  });

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
 * Build the blueprint tree structure from FETCHED agent data (matches SDK's TreeBuilder)
 *
 * KEY INSIGHT: The SDK always fetches agent data from API AFTER creation,
 * then uses that fetched data to build the tree. This ensures the tree
 * contains the actual stored agent data, not our input specs.
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

/**
 * Build tree from fetched agent data (SDK pattern)
 * Uses the actual agent data from Agent API, not our input specs
 */
function buildTreeFromAgentData(
  managerId: string,
  managerData: AgentData,
  workerIds: string[],
  workersData: AgentData[]
): {
  nodes: Array<Record<string, unknown>>;
  edges: Array<Record<string, unknown>>;
  agents: Record<string, AgentData>;
} {
  const nodes: Array<Record<string, unknown>> = [];
  const edges: Array<Record<string, unknown>> = [];
  const agents: Record<string, AgentData> = {};

  // Store manager in agents dict (using fetched data!)
  agents[managerId] = managerData;

  // Build manager node
  nodes.push({
    id: managerId,
    type: "agent",
    position: { x: 0, y: 0 },
    data: {
      // Full agent data embedded (like SDK)
      ...managerData,
      // ReactFlow required fields
      label: managerData.name,
      template_type: "MANAGER",
      tool: "",
      agent_role: "Manager",
      agent_id: managerId,
    },
  });

  // Calculate worker positions
  const workerXPositions = calculateWorkerPositions(workersData.length);

  // Build worker nodes and edges
  for (let i = 0; i < workerIds.length; i++) {
    const workerId = workerIds[i];
    const workerData = workersData[i];

    // Store worker in agents dict (using fetched data!)
    agents[workerId] = workerData;

    // Build worker node
    nodes.push({
      id: workerId,
      type: "agent",
      position: { x: workerXPositions[i], y: LEVEL_SPACING },
      data: {
        // Full agent data embedded (like SDK)
        ...workerData,
        // ReactFlow required fields
        label: workerData.name,
        template_type: "STANDARD",
        tool: "",
        agent_role: "Worker",
        agent_id: workerId,
      },
    });

    // Edge from manager to worker
    const edge: Record<string, unknown> = {
      id: `edge-${managerId}-${workerId}`,
      source: managerId,
      target: workerId,
    };
    if (workerData.tool_usage_description) {
      edge.label = workerData.tool_usage_description;
      edge.data = { usageDescription: workerData.tool_usage_description };
    }
    edges.push(edge);
  }

  return { nodes, edges, agents };
}
