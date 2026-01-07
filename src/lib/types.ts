// Types matching backend models (api/models/hitl.py)

export type HITLType = "confirm_architecture" | "review_agent" | "review_blueprint" | "confirm_create";

export type InfoItemType =
  | "text"
  | "choice"
  | "multi_choice"
  | "confirmation"
  | "textarea"    // Multi-line text with character counter
  | "number"      // Numeric input with optional slider
  | "model";      // Model selector with presets

export interface InfoItem {
  id: string;
  question: string;
  type: InfoItemType;
  choices?: string[];
  required: boolean;
  default?: string;
  // Extended properties for new field types
  placeholder?: string;
  minLength?: number;
  maxLength?: number;
  minValue?: number;
  maxValue?: number;
  step?: number;
  rows?: number;
}

export interface AgentYAMLSpec {
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

export interface ArchitecturePreview {
  agents: Array<{
    name: string;
    role: string;
    goal: string;
  }>;
}

export interface HITLSuggestion {
  type: HITLType;
  title: string;
  work_summary: string;
  info_items: InfoItem[];
  preview?: {
    // For confirm_architecture
    agents?: Array<{ name: string; role: string; goal: string }>;
    // For review_agent
    agent_yaml?: AgentYAMLSpec;
  };
}

export interface BlueprintYAMLSpec {
  name: string;
  description: string;
  category: string;
  tags: string[];
  visibility: string;
  readme?: string;
  root_agents: string[];
}

export type AgentAction = "hitl" | "create_blueprint" | "continue";

export interface StructuredOutput {
  action: AgentAction;
  hitl?: HITLSuggestion;
  blueprint_yaml?: BlueprintYAMLSpec;
}

// Chat types
export type MessageRole = "user" | "assistant" | "system";

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
}

export interface AgentSummary {
  name: string;
  filename: string;
  is_manager: boolean;
  agent_index: number;
}

export interface BlueprintResult {
  id: string;
  name: string;
  studio_url: string;
}

// SSE Event types
export type ChatEventType = "text" | "hitl" | "agent_saved" | "created" | "done" | "error";

export interface ChatEvent {
  type: ChatEventType;
  content?: string;
  hitl?: HITLSuggestion;
  agent?: AgentSummary;
  blueprint?: BlueprintResult;
  error?: string;
}

// Session state
export interface SessionState {
  session_id: string;
  step: number;
  agents_crafted: AgentSummary[];
  total_agents: number;
  blueprint_id?: string;
}

// API Request/Response
export interface ChatRequest {
  session_id?: string;
  message: string;
  hitl_response?: {
    action: "proceed" | "revise";
    info_answers?: Record<string, string>;
    feedback?: string;
  };
}

// === Stage-Based Builder API Types ===

export interface ArchitectRequest {
  session_id?: string;
  requirements: string;
}

export interface ArchitectResponse {
  session_id: string;
  reasoning: string;
  agents: Array<{
    name: string;
    role: string;
    goal: string;
  }>;
}

export interface CraftRequest {
  session_id: string;
  agent_name: string;
  agent_purpose: string;
  is_manager: boolean;
  agent_index: number;
  context: string;
  worker_names: string[];
}

export interface CraftResponse {
  session_id: string;
  agent_yaml: AgentYAMLSpec;
}

export interface CreateRequest {
  session_id: string;
  /** Agent specs to create - sent directly to avoid session state issues */
  agent_specs?: AgentYAMLSpec[];
}

export interface CreateResponse {
  session_id: string;
  blueprint_id: string;
  blueprint_name: string;
  studio_url: string;
  manager_id: string;
  worker_ids: string[];
  organization_id: string;
  created_at: string;
  share_type: string;
}

// Builder Stage (explicit stage tracking)
export type BuilderStage =
  | "define"           // User filling GuidedChat
  | "designing"        // Calling Architect Agent
  | "design-review"    // User reviewing architecture
  | "crafting"         // Calling Crafter Agent
  | "craft-review"     // User reviewing agent spec
  | "creating"         // Creating blueprint
  | "complete";        // Done
