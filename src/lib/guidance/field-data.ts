/**
 * Field Guidance Data
 *
 * Tooltips, examples, and warnings for agent configuration fields.
 * Used to provide inline guidance during agent editing.
 */

export interface FieldGuidance {
  /** Short tooltip description */
  tooltip: string;
  /** Example value or format */
  example?: string;
  /** Warning about common mistakes */
  warning?: string;
  /** Best practice tips */
  tips?: string[];
}

/**
 * Guidance data for each agent field
 */
export const FIELD_GUIDANCE: Record<string, FieldGuidance> = {
  name: {
    tooltip: "A unique, memorable name for this agent. Use clear, descriptive names.",
    example: "Customer Support Specialist",
    warning: "Avoid generic names like 'Agent 1' or 'Helper'",
    tips: [
      "Use role-based names (e.g., 'Sales Analyst')",
      "Keep it concise but descriptive",
      "Avoid special characters",
    ],
  },

  description: {
    tooltip: "A comprehensive description of what this agent does and its capabilities.",
    example: "Handles customer inquiries, resolves support tickets, and escalates complex issues to human agents when needed.",
    warning: "Descriptions under 20 characters are too vague",
    tips: [
      "Include the agent's primary responsibilities",
      "Mention key capabilities and limitations",
      "Describe the domain of expertise",
    ],
  },

  role: {
    tooltip: "The professional role or persona this agent embodies. Think job title + expertise level.",
    example: "Senior Customer Success Manager with 10+ years experience in SaaS",
    warning: "Roles should be 15-80 characters for optimal clarity",
    tips: [
      "Include seniority level (Junior, Senior, Lead)",
      "Specify the domain (Sales, Engineering, Support)",
      "Add relevant expertise qualifiers",
    ],
  },

  goal: {
    tooltip: "The primary objective this agent strives to achieve in every interaction.",
    example: "Ensure customer satisfaction by providing accurate, helpful responses and resolving issues efficiently while maintaining a friendly, professional tone.",
    warning: "Goals under 50 characters are usually too vague to guide behavior",
    tips: [
      "Make it specific and measurable",
      "Include quality criteria (accurate, timely, etc.)",
      "Align with business objectives",
    ],
  },

  instructions: {
    tooltip: "Detailed step-by-step instructions for how the agent should behave, respond, and handle various situations.",
    example: "1. Greet the customer warmly\\n2. Identify their issue\\n3. Provide solution or escalate\\n4. Confirm resolution\\n5. Thank them for their patience",
    warning: "Instructions under 50 characters rarely provide enough guidance",
    tips: [
      "Use numbered steps for complex processes",
      "Include edge case handling",
      "Specify tone and communication style",
      "Add constraints and boundaries",
      "Include examples of good responses",
    ],
  },

  model: {
    tooltip: "The AI model powering this agent. Different models have different capabilities, costs, and speeds.",
    tips: [
      "GPT-4o: Best for complex reasoning, highest cost",
      "GPT-4o-mini: Good balance of capability and cost",
      "Claude Sonnet: Excellent for nuanced conversations",
      "Claude Haiku: Fast and cost-effective",
      "Gemini: Strong at multimodal tasks",
    ],
  },

  temperature: {
    tooltip: "Controls randomness in responses. Lower = more focused and deterministic. Higher = more creative and varied.",
    example: "0.3 for factual tasks, 0.7 for creative tasks",
    warning: "Very high temperatures (>0.9) can produce inconsistent results",
    tips: [
      "0.0-0.3: Factual, consistent (support, data analysis)",
      "0.4-0.6: Balanced (general assistance)",
      "0.7-1.0: Creative (content generation, brainstorming)",
    ],
  },

  usage_description: {
    tooltip: "Explains when the manager agent should delegate tasks to this worker. Critical for proper task routing.",
    example: "Use this agent when the customer has a technical question about API integration, authentication, or error troubleshooting.",
    warning: "Vague usage descriptions lead to poor task delegation",
    tips: [
      "Be specific about trigger conditions",
      "List the types of tasks this worker handles",
      "Include keywords the manager can match on",
      "Mention what this worker should NOT handle",
    ],
  },
};

/**
 * Get guidance for a specific field
 */
export function getFieldGuidance(fieldId: string): FieldGuidance | null {
  return FIELD_GUIDANCE[fieldId] || null;
}

/**
 * Quality indicators for detecting weak/placeholder content
 */
export const WEAK_PATTERNS = {
  /** Patterns that indicate placeholder or low-effort content */
  generic: [
    /^(todo|tbd|fixme|placeholder|test|example|sample)/i,
    /^(agent|assistant|helper|bot)\s*\d*$/i,
    /^(untitled|unnamed|new)/i,
    /lorem ipsum/i,
    /xxx+/i,
    /\.\.\./,
  ],

  /** Patterns indicating incomplete content */
  incomplete: [
    /\[.*\]/,  // [placeholder]
    /<.*>/,   // <fill in>
    /\{.*\}/, // {variable}
    /TODO/i,
    /FIXME/i,
  ],

  /** Patterns indicating copy-paste without customization */
  boilerplate: [
    /^you are (a|an) (helpful|friendly|professional) (assistant|agent)/i,
    /^i am (a|an) (helpful|friendly|professional) (assistant|agent)/i,
    /^as an ai/i,
  ],
};

/**
 * Check if content matches any weak patterns
 */
export function hasWeakPatterns(content: string): boolean {
  const allPatterns = [
    ...WEAK_PATTERNS.generic,
    ...WEAK_PATTERNS.incomplete,
    ...WEAK_PATTERNS.boilerplate,
  ];

  return allPatterns.some((pattern) => pattern.test(content));
}

/**
 * Get specific warning if content matches weak patterns
 */
export function getWeakPatternWarning(content: string): string | null {
  for (const pattern of WEAK_PATTERNS.generic) {
    if (pattern.test(content)) {
      return "This looks like placeholder content. Please provide a real value.";
    }
  }

  for (const pattern of WEAK_PATTERNS.incomplete) {
    if (pattern.test(content)) {
      return "This contains unfilled placeholders. Please complete all values.";
    }
  }

  for (const pattern of WEAK_PATTERNS.boilerplate) {
    if (pattern.test(content)) {
      return "This is generic boilerplate. Please customize for your specific use case.";
    }
  }

  return null;
}
