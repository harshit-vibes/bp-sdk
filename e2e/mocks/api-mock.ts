import { Page } from '@playwright/test';

/**
 * SSE Event types that the backend sends
 */
export interface SSEEvent {
  type: 'text' | 'session' | 'hitl' | 'agent_saved' | 'created' | 'error';
  content?: string;
  session_id?: string;
  hitl?: HITLSuggestion;
  agent?: AgentSummary;
  blueprint?: BlueprintResult;
  error?: string;
}

export interface HITLSuggestion {
  type: 'confirm_architecture' | 'review_agent' | 'review_blueprint';
  title: string;
  work_summary: string;
  preview?: {
    pattern?: string;
    manager?: { name: string; purpose: string };
    workers?: Array<{ name: string; purpose: string }>;
    agent_yaml?: AgentYaml;
  };
}

export interface AgentYaml {
  name: string;
  role: string;
  goal: string;
  instructions: string;
  model: string;
  temperature: number;
  is_manager: boolean;
  usage_description?: string;
}

export interface AgentSummary {
  id: string;
  name: string;
  role: string;
  is_manager: boolean;
}

export interface BlueprintResult {
  id: string;
  name: string;
  studio_url: string;
}

/**
 * Convert events to SSE format string
 */
export function toSSE(events: SSEEvent[]): string {
  return events.map(event => `data: ${JSON.stringify(event)}\n\n`).join('') + 'data: [DONE]\n\n';
}

/**
 * Create a mock streaming response
 */
export function createStreamResponse(events: SSEEvent[]): Response {
  const sseData = toSSE(events);
  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    start(controller) {
      // Simulate streaming by sending chunks with delays
      const chunks = sseData.split('\n\n').filter(Boolean);
      let index = 0;

      function sendNextChunk() {
        if (index < chunks.length) {
          controller.enqueue(encoder.encode(chunks[index] + '\n\n'));
          index++;
          setTimeout(sendNextChunk, 50); // 50ms between chunks
        } else {
          controller.close();
        }
      }

      sendNextChunk();
    }
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
    }
  });
}

/**
 * Mock API responses for different journey stages
 */
export const mockResponses = {
  /**
   * Initial response after statement submission - goes to Explore stage
   */
  exploreStage: (sessionId: string = 'test-session-123'): SSEEvent[] => [
    { type: 'session', session_id: sessionId },
    { type: 'text', content: "Thank you for sharing your requirements. I'd like to understand your needs better.\n\n" },
    { type: 'text', content: "**A few clarifying questions:**\n\n" },
    { type: 'text', content: "1. How many customer inquiries do you typically receive per day?\n" },
    { type: 'text', content: "2. What channels do customers use to reach you (email, chat, phone)?\n" },
    { type: 'text', content: "3. Are there specific types of inquiries that take the most time?\n" },
  ],

  /**
   * Response after exploration - HITL for architecture confirmation
   */
  architectureHITL: (): SSEEvent[] => [
    { type: 'text', content: "Based on your requirements, I've designed the following architecture:\n\n" },
    {
      type: 'hitl',
      hitl: {
        type: 'confirm_architecture',
        title: 'Review Proposed Architecture',
        work_summary: 'I recommend a multi-agent system with a Manager coordinating specialized workers.',
        preview: {
          pattern: 'manager_workers',
          manager: { name: 'Support Coordinator', purpose: 'Orchestrates the customer support workflow and delegates tasks to specialized workers.' },
          workers: [
            { name: 'Ticket Classifier', purpose: 'Classifies incoming support tickets by type and priority.' },
            { name: 'Response Generator', purpose: 'Generates appropriate responses for customer inquiries.' },
            { name: 'Escalation Handler', purpose: 'Handles complex cases that need human escalation.' },
          ],
        },
      },
    },
  ],

  /**
   * Response after architecture approval - HITL for agent review (manager)
   */
  managerAgentHITL: (): SSEEvent[] => [
    { type: 'text', content: "I've created the manager agent. Please review:\n\n" },
    {
      type: 'hitl',
      hitl: {
        type: 'review_agent',
        title: 'Review Manager Agent',
        work_summary: 'The Support Coordinator will orchestrate the workflow and delegate tasks.',
        preview: {
          agent_yaml: {
            name: 'Support Coordinator',
            role: 'Customer Support Orchestrator',
            goal: 'Efficiently coordinate customer support requests by delegating to specialized workers',
            instructions: 'You are the Support Coordinator. Your job is to:\n1. Receive customer inquiries\n2. Classify the type of request\n3. Delegate to the appropriate worker\n4. Synthesize responses\n5. Handle escalations',
            model: 'gpt-4o',
            temperature: 0.3,
            is_manager: true,
          },
        },
      },
    },
  ],

  /**
   * Response after manager approval - save agent and show worker HITL
   */
  workerAgentHITL: (agentNumber: number = 1): SSEEvent[] => [
    {
      type: 'agent_saved',
      agent: {
        id: `agent-${agentNumber}`,
        name: agentNumber === 1 ? 'Ticket Classifier' : `Worker ${agentNumber}`,
        role: 'Support Specialist',
        is_manager: agentNumber === 1 ? false : false,
      },
    },
    { type: 'text', content: `Worker agent ${agentNumber} created. Please review:\n\n` },
    {
      type: 'hitl',
      hitl: {
        type: 'review_agent',
        title: `Review Worker Agent ${agentNumber}`,
        work_summary: `This worker handles ${agentNumber === 1 ? 'ticket classification' : 'specific tasks'}.`,
        preview: {
          agent_yaml: {
            name: agentNumber === 1 ? 'Ticket Classifier' : `Worker ${agentNumber}`,
            role: agentNumber === 1 ? 'Request Classifier' : 'Support Specialist',
            goal: 'Accurately classify incoming support requests',
            instructions: 'You classify customer support tickets into categories.',
            model: 'gpt-4o-mini',
            temperature: 0.2,
            is_manager: false,
            usage_description: 'Use this worker to classify incoming tickets',
          },
        },
      },
    },
  ],

  /**
   * Final response - blueprint created
   */
  blueprintCreated: (): SSEEvent[] => [
    {
      type: 'agent_saved',
      agent: {
        id: 'agent-final',
        name: 'Response Generator',
        role: 'Response Specialist',
        is_manager: false,
      },
    },
    { type: 'text', content: "All agents created successfully!\n\n" },
    { type: 'text', content: "Creating your blueprint...\n\n" },
    {
      type: 'created',
      blueprint: {
        id: 'bp-test-12345',
        name: 'Customer Support Automation',
        studio_url: 'https://studio.lyzr.ai/lyzr-manager?blueprint=bp-test-12345',
      },
    },
  ],

  /**
   * Error response
   */
  error: (message: string = 'An error occurred'): SSEEvent[] => [
    { type: 'error', error: message },
  ],

  /**
   * Conversational response (no HITL)
   */
  conversational: (text: string): SSEEvent[] => [
    { type: 'text', content: text },
  ],
};

/**
 * Setup API mock for a page
 */
export async function setupApiMock(page: Page, responseSequence: SSEEvent[][]) {
  let callIndex = 0;

  await page.route('**/api/chat', async (route) => {
    const events = responseSequence[callIndex] || responseSequence[responseSequence.length - 1];
    callIndex++;

    const sseData = toSSE(events);

    await route.fulfill({
      status: 200,
      contentType: 'text/event-stream',
      headers: {
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
      body: sseData,
    });
  });

  return {
    getCallCount: () => callIndex,
    reset: () => { callIndex = 0; },
  };
}

/**
 * Setup a single response mock
 */
export async function setupSingleMock(page: Page, events: SSEEvent[]) {
  await page.route('**/api/chat', async (route) => {
    const sseData = toSSE(events);

    await route.fulfill({
      status: 200,
      contentType: 'text/event-stream',
      headers: {
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
      body: sseData,
    });
  });
}
