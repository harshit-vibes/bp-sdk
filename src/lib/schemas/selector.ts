/**
 * Selector Schema Definitions
 *
 * Defines the structure for statement slots and selector options
 */

import { z } from "zod";

/**
 * Option schema - a single selectable option
 */
export const SelectorOptionSchema = z.object({
  /** Value stored when selected */
  value: z.string().min(1),

  /** Display label shown to user */
  label: z.string().min(1).max(50),

  /** Optional description shown below label */
  description: z.string().max(100).optional(),

  /** Optional icon identifier */
  icon: z.string().optional(),

  /** Whether this option is disabled */
  disabled: z.boolean().optional(),
});

export type SelectorOption = z.infer<typeof SelectorOptionSchema>;

/**
 * Statement slot schema - a single fillable slot in the statement
 */
export const StatementSlotSchema = z.object({
  /** Unique slot identifier */
  id: z.string().min(1).max(20),

  /** Placeholder text shown when empty */
  placeholder: z.string().min(1).max(30),

  /** Dialog title when selecting */
  title: z.string().min(1).max(50),

  /** Optional description in dialog */
  description: z.string().max(100).optional(),

  /** Available options for this slot */
  options: z.array(SelectorOptionSchema).min(1).max(20),

  /** Whether custom input is allowed */
  allowCustom: z.boolean().optional().default(true),

  /** Custom input placeholder */
  customPlaceholder: z.string().max(100).optional(),

  /** Custom input label */
  customLabel: z.string().max(50).optional(),
});

export type StatementSlot = z.infer<typeof StatementSlotSchema>;

/**
 * Statement template schema - the complete statement structure
 */
export const StatementTemplateSchema = z.object({
  /** Template string with {slot_id} placeholders */
  template: z.string().min(1),

  /** Ordered list of slots */
  slots: z.array(StatementSlotSchema).min(1).max(10),
});

export type StatementTemplate = z.infer<typeof StatementTemplateSchema>;

/**
 * Default problem-focused statement template
 */
export const DEFAULT_STATEMENT_TEMPLATE: StatementTemplate = {
  template: "As a {role}, I need to {problem} in {domain}.",
  slots: [
    {
      id: "role",
      placeholder: "role",
      title: "What's your role?",
      description: "This helps us understand your perspective",
      allowCustom: true,
      customPlaceholder: "Describe your role...",
      customLabel: "Or describe in your own words",
      options: [
        { value: "product manager", label: "Product Manager", description: "Building and shipping products" },
        { value: "customer success lead", label: "Customer Success", description: "Ensuring customer satisfaction" },
        { value: "sales leader", label: "Sales Leader", description: "Growing revenue and closing deals" },
        { value: "marketing director", label: "Marketing Director", description: "Driving awareness and demand" },
        { value: "operations manager", label: "Operations Manager", description: "Streamlining processes" },
        { value: "engineering lead", label: "Engineering Lead", description: "Building technical solutions" },
        { value: "HR manager", label: "HR Manager", description: "Managing people and culture" },
        { value: "founder", label: "Founder / Executive", description: "Leading the organization" },
      ],
    },
    {
      id: "problem",
      placeholder: "problem to solve",
      title: "What problem are you solving?",
      description: "Describe what you're trying to accomplish",
      allowCustom: true,
      customPlaceholder: "Describe your problem...",
      customLabel: "Or describe in your own words",
      options: [
        { value: "automate repetitive tasks that consume my team's time", label: "Automate Repetitive Work", description: "Free up time from manual tasks" },
        { value: "respond to customer inquiries faster and more consistently", label: "Faster Customer Response", description: "Improve response time and quality" },
        { value: "qualify and prioritize incoming leads efficiently", label: "Lead Qualification", description: "Focus on high-value prospects" },
        { value: "generate and optimize content at scale", label: "Content at Scale", description: "Create more content, faster" },
        { value: "extract insights from documents and data", label: "Extract Insights", description: "Make sense of information" },
        { value: "onboard and train team members effectively", label: "Team Onboarding", description: "Get people up to speed" },
        { value: "research and synthesize information quickly", label: "Research & Synthesis", description: "Gather and summarize knowledge" },
        { value: "coordinate work across multiple processes", label: "Process Coordination", description: "Orchestrate complex workflows" },
      ],
    },
    {
      id: "domain",
      placeholder: "area",
      title: "In what area?",
      description: "The domain or function this applies to",
      allowCustom: true,
      customPlaceholder: "Describe your area...",
      customLabel: "Or describe in your own words",
      options: [
        { value: "customer support", label: "Customer Support", description: "Tickets, inquiries, help desk" },
        { value: "sales", label: "Sales", description: "Leads, deals, pipeline" },
        { value: "marketing", label: "Marketing", description: "Campaigns, content, demand gen" },
        { value: "human resources", label: "Human Resources", description: "Recruiting, policies, L&D" },
        { value: "product development", label: "Product", description: "Features, roadmap, feedback" },
        { value: "operations", label: "Operations", description: "Processes, efficiency, logistics" },
        { value: "finance", label: "Finance", description: "Accounting, reporting, analysis" },
        { value: "legal and compliance", label: "Legal & Compliance", description: "Contracts, policies, risk" },
      ],
    },
  ],
};

/**
 * Validate selector options
 */
export function validateOptions(options: unknown): SelectorOption[] {
  return z.array(SelectorOptionSchema).parse(options);
}

/**
 * Validate statement template
 */
export function validateStatementTemplate(template: unknown): StatementTemplate {
  return StatementTemplateSchema.parse(template);
}

/**
 * Build statement from template and selections
 */
export function buildStatement(
  template: StatementTemplate,
  selections: Record<string, string | null>
): string | null {
  let result = template.template;

  for (const slot of template.slots) {
    const value = selections[slot.id];
    if (!value) {
      return null; // Statement incomplete
    }
    result = result.replace(`{${slot.id}}`, value);
  }

  return result;
}

/**
 * Check if all slots are filled
 */
export function isStatementComplete(
  template: StatementTemplate,
  selections: Record<string, string | null>
): boolean {
  return template.slots.every((slot) => !!selections[slot.id]);
}
