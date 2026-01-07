/**
 * Lyzr API Client
 *
 * Direct client for calling Lyzr Agent API and Blueprint API.
 * Replaces the need for a separate Python backend.
 */

// API URLs
const AGENT_API_URL = "https://agent-prod.studio.lyzr.ai";
const BLUEPRINT_API_URL = "https://pagos-prod.studio.lyzr.ai";

/**
 * Stream response from a Lyzr agent
 */
export async function streamFromAgent(params: {
  agentId: string;
  apiKey: string;
  sessionId: string;
  message: string;
  userId?: string;
}): Promise<string> {
  const { agentId, apiKey, sessionId, message, userId = "builder-user" } = params;

  const response = await fetch(`${AGENT_API_URL}/v3/inference/stream/`, {
    method: "POST",
    headers: {
      "X-API-Key": apiKey,
      "Content-Type": "application/json",
      "Accept": "text/event-stream",
    },
    body: JSON.stringify({
      agent_id: agentId,
      session_id: sessionId,
      user_id: userId,
      message,
    }),
  });

  if (!response.ok) {
    const errorText = await response.text().catch(() => "Unknown error");
    throw new Error(`Agent API error: ${response.status} - ${errorText}`);
  }

  // Collect full response from SSE stream
  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error("No response body");
  }

  const decoder = new TextDecoder();
  let fullResponse = "";
  let buffer = ""; // Buffer for incomplete lines across chunks
  let isDone = false;

  while (!isDone) {
    const { done, value } = await reader.read();
    if (done) break;

    // Append new chunk to buffer
    buffer += decoder.decode(value, { stream: true });

    // Process complete lines from buffer
    const lines = buffer.split("\n");

    // Keep the last potentially incomplete line in the buffer
    buffer = lines.pop() || "";

    for (const line of lines) {
      const trimmedLine = line.trim();
      if (trimmedLine.startsWith("data: ")) {
        const content = trimmedLine.slice(6);
        if (content === "[DONE]") {
          isDone = true;
          break;
        }
        fullResponse += content;
      }
    }
  }

  // Process any remaining content in buffer
  if (buffer.trim().startsWith("data: ")) {
    const content = buffer.trim().slice(6);
    if (content !== "[DONE]") {
      fullResponse += content;
    }
  }

  return fullResponse;
}

/**
 * Call agent and parse JSON response (uses non-streaming endpoint)
 */
export async function callAgentForJSON<T = Record<string, unknown>>(params: {
  agentId: string;
  apiKey: string;
  sessionId: string;
  message: string;
  userId?: string;
}): Promise<T> {
  const { agentId, apiKey, sessionId, message, userId = "builder-user" } = params;

  // Use non-streaming endpoint for JSON responses
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
  });

  if (!response.ok) {
    const errorText = await response.text().catch(() => "Unknown error");
    throw new Error(`Agent API error: ${response.status} - ${errorText}`);
  }

  const data = await response.json();

  // Debug logging
  console.log("[callAgentForJSON] Raw API response keys:", Object.keys(data));
  console.log("[callAgentForJSON] Response length:", JSON.stringify(data).length);

  // Extract the response text from the API response structure
  // API returns: { response: "...", session_id: "...", ... }
  const responseText = data.response || data.message || data.content || JSON.stringify(data);

  console.log("[callAgentForJSON] Response text length:", responseText.length);
  console.log("[callAgentForJSON] Response text (first 500):", responseText.slice(0, 500));
  console.log("[callAgentForJSON] Response text (last 200):", responseText.slice(-200));

  return parseAgentJSON<T>(responseText);
}

/**
 * Fix control characters inside JSON strings (newlines, tabs, etc.)
 * These are invalid in JSON and must be escaped.
 */
function fixControlCharsInStrings(json: string): string {
  let result = '';
  let inString = false;
  let escape = false;

  for (let i = 0; i < json.length; i++) {
    const char = json[i];
    const code = char.charCodeAt(0);

    if (escape) {
      result += char;
      escape = false;
      continue;
    }

    if (char === '\\' && inString) {
      escape = true;
      result += char;
      continue;
    }

    if (char === '"') {
      inString = !inString;
      result += char;
      continue;
    }

    // If inside a string and it's a control character, escape it
    if (inString && code < 32) {
      switch (char) {
        case '\n': result += '\\n'; break;
        case '\r': result += '\\r'; break;
        case '\t': result += '\\t'; break;
        case '\b': result += '\\b'; break;
        case '\f': result += '\\f'; break;
        default: result += '\\u' + ('0000' + code.toString(16)).slice(-4);
      }
    } else {
      result += char;
    }
  }

  return result;
}

/**
 * Parse JSON from agent response (handles markdown code blocks, control chars, etc.)
 */
export function parseAgentJSON<T = Record<string, unknown>>(response: string): T {
  let text = response.trim();

  // Remove markdown code blocks first
  if (text.includes("```json")) {
    const start = text.indexOf("```json") + 7;
    const end = text.indexOf("```", start);
    if (end > start) {
      text = text.slice(start, end).trim();
    }
  } else if (text.includes("```")) {
    const start = text.indexOf("```") + 3;
    const end = text.indexOf("```", start);
    if (end > start) {
      text = text.slice(start, end).trim();
    }
  }

  // Extract JSON object/array if there's extra text
  const objectStart = text.indexOf("{");
  const objectEnd = text.lastIndexOf("}") + 1;
  const arrayStart = text.indexOf("[");
  const arrayEnd = text.lastIndexOf("]") + 1;

  if (objectStart !== -1 && objectEnd > objectStart) {
    text = text.slice(objectStart, objectEnd);
  } else if (arrayStart !== -1 && arrayEnd > arrayStart) {
    text = text.slice(arrayStart, arrayEnd);
  }

  // Try to parse directly first
  try {
    return JSON.parse(text);
  } catch (firstError) {
    // Fix control characters inside strings and retry
    try {
      const fixed = fixControlCharsInStrings(text);
      return JSON.parse(fixed);
    } catch (secondError) {
      const parseError = secondError instanceof Error ? secondError.message : 'Unknown parse error';
      throw new Error(`Failed to parse agent JSON: ${parseError}\nText (first 300): ${text.slice(0, 300)}`);
    }
  }
}

/**
 * Create an agent via Lyzr Agent API
 */
export async function createAgent(params: {
  apiKey: string;
  agentConfig: Record<string, unknown>;
}): Promise<{ agent_id: string }> {
  const { apiKey, agentConfig } = params;

  const response = await fetch(`${AGENT_API_URL}/v3/agents/`, {
    method: "POST",
    headers: {
      "X-API-Key": apiKey,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(agentConfig),
  });

  if (!response.ok) {
    const errorText = await response.text().catch(() => "Unknown error");
    throw new Error(`Failed to create agent: ${response.status} - ${errorText}`);
  }

  return response.json();
}

/**
 * Create a blueprint via Lyzr Blueprint API (Pagos)
 */
export async function createBlueprint(params: {
  bearerToken: string;
  orgId: string;
  blueprintData: Record<string, unknown>;
}): Promise<Record<string, unknown>> {
  const { bearerToken, orgId, blueprintData } = params;

  const response = await fetch(`${BLUEPRINT_API_URL}/blueprints/`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${bearerToken}`,
      "Content-Type": "application/json",
      "x-organization-id": orgId,
    },
    body: JSON.stringify(blueprintData),
  });

  if (!response.ok) {
    const errorText = await response.text().catch(() => "Unknown error");
    throw new Error(`Failed to create blueprint: ${response.status} - ${errorText}`);
  }

  return response.json();
}

/**
 * Get credentials from request cookies
 */
export function getCredentialsFromCookies(cookieHeader: string | null): {
  apiKey: string | null;
  bearerToken: string | null;
  orgId: string | null;
} {
  if (!cookieHeader) {
    return { apiKey: null, bearerToken: null, orgId: null };
  }

  const cookies = Object.fromEntries(
    cookieHeader.split("; ").map((c) => {
      const [key, ...rest] = c.split("=");
      return [key, decodeURIComponent(rest.join("="))];
    })
  );

  return {
    apiKey: cookies["bp_builder_api_key"] || null,
    bearerToken: cookies["bp_builder_bearer_token"] || null,
    orgId: cookies["bp_builder_org_id"] || null,
  };
}
