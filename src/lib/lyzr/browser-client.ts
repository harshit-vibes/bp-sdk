/**
 * Browser-side Lyzr Agent Client
 *
 * Calls Lyzr Agent API directly from the browser.
 * Uses credentials stored in cookies by the setup screen.
 */

import { getStoredCredentials } from "@/components/screens/setup-screen";

// API URL
const AGENT_API_URL = "https://agent-prod.studio.lyzr.ai";

/**
 * Get stored API key from cookies
 */
export function getApiKey(): string | null {
  const credentials = getStoredCredentials();
  return credentials?.apiKey || null;
}

/**
 * Call agent and get text response (non-streaming)
 */
export async function callAgentForText(params: {
  agentId: string;
  sessionId: string;
  message: string;
  userId?: string;
  timeoutMs?: number;
}): Promise<string> {
  const { agentId, sessionId, message, userId = "builder-user", timeoutMs = 30000 } = params;

  const apiKey = getApiKey();
  if (!apiKey) {
    throw new Error("API key not found. Please set up your credentials.");
  }

  // Create abort controller for timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(`${AGENT_API_URL}/v3/inference/chat/`, {
      method: "POST",
      headers: {
        "X-API-Key": apiKey,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        agent_id: agentId,
        session_id: sessionId,
        user_id: userId,
        message,
      }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text().catch(() => "Unknown error");
      throw new Error(`Agent API error: ${response.status} - ${errorText}`);
    }

    const data = await response.json();

    // Extract the response text from the API response structure
    // API returns: { response: "...", session_id: "...", ... }
    const responseText = data.response || data.message || data.content || "";

    return responseText;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === "AbortError") {
      throw new Error(`Agent request timed out after ${timeoutMs / 1000} seconds.`);
    }
    throw error;
  }
}

/**
 * README generation prompt template
 */
export function buildReadmePrompt(params: {
  blueprintName: string;
  blueprintDescription: string;
  agents: Array<{
    name: string;
    role: string;
    goal: string;
    is_manager: boolean;
    instructions: string;
  }>;
}): string {
  const { blueprintName, blueprintDescription, agents } = params;

  // Build context about the blueprint
  const [coordinator, ...specialists] = agents;
  const agentSummary = agents
    .map((a, i) => {
      const type = i === 0 ? "Coordinator" : "Specialist";
      return `- **${a.name}** (${type}): ${a.role} - ${a.goal}`;
    })
    .join("\n");

  return `Generate a professional README for this AI agent blueprint.

Blueprint Name: ${blueprintName}
Blueprint Description: ${blueprintDescription}

Agents in this blueprint:
${agentSummary}

Coordinator Instructions:
${coordinator.instructions}

${
  specialists.length > 0
    ? `Specialist Details:
${specialists.map((s) => `${s.name}: ${s.instructions.substring(0, 200)}...`).join("\n\n")}`
    : ""
}

Generate a README following this EXACT structure (use markdown):

## The Problem

### The Situation
[Describe the current state without this solution - what do teams/users currently do? What tools do they use? What's the volume/scale?]

### The Challenge
[Explain why existing approaches fail - expertise required, consistency issues, resource constraints]

### What's At Stake
[Describe consequences of not solving this - business impact, customer impact, operational impact]

---

## The Approach

### The Key Insight
[One paragraph explaining the conceptual breakthrough that makes this approach work]

### The Method
[How the agents work together - describe the coordinator and specialists, the workflow/sequence, how they collaborate]

### Why This Works
[Why this approach succeeds - consistency benefits, specialization benefits, scale benefits]

---

## Capabilities

### Core Capabilities
[4-6 bullet points of main things this blueprint does - be specific with numbers/categories where possible]

### Extended Capabilities
[3-4 bullet points of additional features beyond the core]

### Boundaries
[3-4 bullet points of what this blueprint doesn't do - important for managing expectations]

---

## Getting Started

### Prerequisites
[What users need before starting - 2-3 items]

### Your First Run
[A concrete example input to try immediately - make it realistic and specific]

### Pro Tips
[3-4 tips for getting the best results]

Return ONLY the markdown README content. Do not wrap in JSON or code blocks.`;
}

/**
 * Generate README for a blueprint
 */
export async function generateReadme(params: {
  agentId: string;
  sessionId: string;
  blueprintName: string;
  blueprintDescription: string;
  agents: Array<{
    name: string;
    role: string;
    goal: string;
    is_manager: boolean;
    instructions: string;
  }>;
}): Promise<string> {
  const { agentId, sessionId, blueprintName, blueprintDescription, agents } = params;

  const prompt = buildReadmePrompt({
    blueprintName,
    blueprintDescription,
    agents,
  });

  const response = await callAgentForText({
    agentId,
    sessionId,
    message: prompt,
    timeoutMs: 60000, // 60 seconds for README generation (longer content)
  });

  // Clean up response if needed
  let readme = response.trim();

  // Remove any markdown code blocks if the agent wrapped the response
  if (readme.startsWith("```markdown")) {
    readme = readme.slice(11);
  } else if (readme.startsWith("```")) {
    readme = readme.slice(3);
  }
  if (readme.endsWith("```")) {
    readme = readme.slice(0, -3);
  }

  return readme.trim();
}
