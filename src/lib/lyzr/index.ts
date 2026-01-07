export {
  streamFromAgent,
  callAgentForJSON,
  parseAgentJSON,
  createAgent,
  createBlueprint,
  getCredentialsFromCookies,
} from "./client";

export { AGENT_IDS, validateAgentConfig } from "./config";

// Browser-side client (can be used directly in React components)
export {
  callAgentForText,
  generateReadme,
  buildReadmePrompt,
  getApiKey,
} from "./browser-client";
