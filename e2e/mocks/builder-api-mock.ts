import { Page } from '@playwright/test';

/**
 * Mock responses for the stage-based builder API
 */

export interface ArchitectResponse {
  session_id: string;
  pattern: 'single_agent' | 'manager_workers';
  reasoning: string;
  manager: { name: string; purpose: string };
  workers: Array<{ name: string; purpose: string }>;
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

export interface CraftResponse {
  session_id: string;
  agent_yaml: AgentYAMLSpec;
}

export interface CreateResponse {
  session_id: string;
  blueprint_id: string;
  studio_url: string;
  manager_id: string;
  worker_ids: string[];
}

/**
 * Mock API responses for the builder endpoints
 */
export const mockBuilderResponses = {
  /**
   * Architect response - returns architecture JSON
   */
  architect: (sessionId: string = 'test-session-123'): ArchitectResponse => ({
    session_id: sessionId,
    pattern: 'manager_workers',
    reasoning: 'Customer support requires multiple specialized skills: classification, prioritization, and response drafting. A manager-workers pattern allows each phase to be handled by a focused agent.',
    manager: {
      name: 'Support Coordinator',
      purpose: 'Orchestrates the customer support workflow by routing tickets through classification, prioritization, and response drafting stages.',
    },
    workers: [
      { name: 'Ticket Classifier', purpose: 'Categorizes incoming tickets by type: billing, technical, general inquiry.' },
      { name: 'Priority Assessor', purpose: 'Determines ticket urgency based on sentiment, keywords, and customer tier.' },
      { name: 'Response Drafter', purpose: 'Generates initial response drafts based on ticket category and priority.' },
    ],
  }),

  /**
   * Craft response - returns agent spec JSON
   */
  craftManager: (sessionId: string = 'test-session-123'): CraftResponse => ({
    session_id: sessionId,
    agent_yaml: {
      filename: 'support-coordinator.yaml',
      is_manager: true,
      agent_index: 0,
      name: 'Support Coordinator',
      description: 'Orchestrates the customer support workflow by coordinating specialized workers for classification, prioritization, and response drafting.',
      model: 'gpt-4o-mini',
      temperature: 0.3,
      role: 'Senior Support Workflow Coordinator',
      goal: 'Coordinate specialized workers to efficiently classify, prioritize, and draft responses for incoming support tickets.',
      instructions: `You are the Support Coordinator. You manage the support ticket triage workflow.

## Your Team
1. **Ticket Classifier** - Categorizes tickets by type
2. **Priority Assessor** - Determines urgency level
3. **Response Drafter** - Creates initial responses

## Workflow
1. Receive input from user
2. Delegate to Ticket Classifier for categorization
3. Delegate to Priority Assessor for urgency
4. Delegate to Response Drafter with category and priority
5. Return the complete triage result`,
      features: ['memory'],
      sub_agents: ['ticket-classifier.yaml', 'priority-assessor.yaml', 'response-drafter.yaml'],
    },
  }),

  craftWorker: (sessionId: string, workerIndex: number): CraftResponse => {
    const workers = [
      {
        filename: 'ticket-classifier.yaml',
        name: 'Ticket Classifier',
        description: 'Categorizes incoming support tickets by type using advanced pattern recognition, keyword analysis, and contextual understanding.',
        role: 'Support Ticket Classification Specialist',
        goal: 'Accurately categorize each incoming ticket into exactly one of the predefined categories based on content analysis and context.',
        instructions: `You are a specialized ticket classification agent responsible for categorizing incoming support tickets.

## Your Task
Analyze each incoming ticket and assign it to one of these categories:
- **billing**: Payment issues, subscription problems, invoice questions
- **technical**: Product bugs, feature requests, integration issues
- **general**: General questions, feedback, other inquiries

## Process
1. Read the ticket content carefully
2. Identify key indicators and keywords
3. Consider the customer's intent
4. Assign the most appropriate category`,
        usage_description: 'Use this worker to categorize incoming tickets before priority assessment.',
      },
      {
        filename: 'priority-assessor.yaml',
        name: 'Priority Assessor',
        description: 'Determines ticket urgency based on sentiment analysis, keyword detection, customer tier information, and historical patterns.',
        role: 'Ticket Priority Assessment Specialist',
        goal: 'Assess urgency level (high/medium/low) for each ticket based on multiple signals including sentiment, keywords, and customer context.',
        instructions: `You are a specialized priority assessment agent responsible for determining ticket urgency.

## Priority Levels
- **High**: Urgent issues affecting business operations, security concerns, major bugs
- **Medium**: Moderate impact issues, feature questions, non-critical bugs
- **Low**: General inquiries, feedback, minor issues

## Assessment Criteria
1. Analyze ticket sentiment (frustrated, neutral, positive)
2. Check for urgency keywords (urgent, asap, critical, etc.)
3. Consider customer tier if available
4. Evaluate business impact`,
        usage_description: 'Use this worker to determine ticket priority after classification.',
      },
      {
        filename: 'response-drafter.yaml',
        name: 'Response Drafter',
        description: 'Generates appropriate, professional response drafts for customer inquiries based on ticket category, priority, and context.',
        role: 'Customer Response Specialist',
        goal: 'Draft helpful, professional, and empathetic responses for customer tickets that address their concerns effectively.',
        instructions: `You are a specialized response drafting agent responsible for creating initial customer responses.

## Response Guidelines
1. Start with a warm, professional greeting
2. Acknowledge the customer's concern
3. Provide clear, helpful information
4. Offer next steps or additional assistance
5. Close with a positive note

## Tone
- Professional but friendly
- Empathetic and understanding
- Clear and concise
- Solution-focused`,
        usage_description: 'Use this worker to draft ticket responses after priority assessment.',
      },
    ];

    const worker = workers[workerIndex] || workers[0];

    return {
      session_id: sessionId,
      agent_yaml: {
        filename: worker.filename,
        is_manager: false,
        agent_index: workerIndex + 1,
        name: worker.name,
        description: worker.description,
        model: 'gpt-4o-mini',
        temperature: 0.2,
        role: worker.role,
        goal: worker.goal,
        instructions: worker.instructions,
        usage_description: worker.usage_description,
        features: [],
        sub_agents: [],
      },
    };
  },

  /**
   * Create response - returns blueprint result
   */
  create: (sessionId: string = 'test-session-123'): CreateResponse => ({
    session_id: sessionId,
    blueprint_id: 'bp-test-12345',
    studio_url: 'https://studio.lyzr.ai/blueprints/bp-test-12345',
    manager_id: 'agent-manager-123',
    worker_ids: ['agent-worker-1', 'agent-worker-2', 'agent-worker-3'],
  }),

  /**
   * Error response
   */
  error: (message: string = 'An error occurred') => ({
    error: message,
  }),
};

/**
 * Setup builder API mocks for a page
 */
export async function setupBuilderApiMock(page: Page, options: {
  architectResponse?: ArchitectResponse;
  craftResponses?: CraftResponse[];
  createResponse?: CreateResponse;
  architectError?: string;
  craftError?: string;
  createError?: string;
} = {}) {
  const sessionId = 'test-session-123';
  let craftCallIndex = 0;

  // Mock architect endpoint
  await page.route('**/api/builder/architect', async (route) => {
    if (options.architectError) {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: options.architectError }),
      });
    } else {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(options.architectResponse || mockBuilderResponses.architect(sessionId)),
      });
    }
  });

  // Mock craft endpoint
  await page.route('**/api/builder/craft', async (route) => {
    if (options.craftError) {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: options.craftError }),
      });
    } else {
      const response = options.craftResponses?.[craftCallIndex]
        || (craftCallIndex === 0
          ? mockBuilderResponses.craftManager(sessionId)
          : mockBuilderResponses.craftWorker(sessionId, craftCallIndex - 1));
      craftCallIndex++;

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(response),
      });
    }
  });

  // Mock create endpoint
  await page.route('**/api/builder/create', async (route) => {
    if (options.createError) {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: options.createError }),
      });
    } else {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(options.createResponse || mockBuilderResponses.create(sessionId)),
      });
    }
  });

  return {
    getCraftCallCount: () => craftCallIndex,
    reset: () => { craftCallIndex = 0; },
  };
}
