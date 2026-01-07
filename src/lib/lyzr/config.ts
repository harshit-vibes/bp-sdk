/**
 * Lyzr Agent Configuration
 *
 * Agent IDs for the builder workflow.
 * These should be set as environment variables in production.
 */

export const AGENT_IDS = {
  // Core builder agents (required)
  architect: process.env.ARCHITECT_AGENT_ID || "",
  crafter: process.env.CRAFTER_AGENT_ID || "",

  // Optional enhancement agents
  loader: process.env.LOADER_AGENT_ID || "",
  options: process.env.OPTIONS_AGENT_ID || "",
  suggest: process.env.SUGGEST_AGENT_ID || "",
  replySuggester: process.env.REPLY_SUGGESTER_AGENT_ID || "",
  ideaSuggester: process.env.IDEA_SUGGESTER_AGENT_ID || "",
  readmeBuilder: process.env.README_BUILDER_AGENT_ID || "",
};

/**
 * Check if required agents are configured
 */
export function validateAgentConfig(): { valid: boolean; missing: string[] } {
  const required = ["architect", "crafter"] as const;
  const missing = required.filter((key) => !AGENT_IDS[key]);

  return {
    valid: missing.length === 0,
    missing,
  };
}
