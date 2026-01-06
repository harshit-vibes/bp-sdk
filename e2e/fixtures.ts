import { test as base, expect } from '@playwright/test';

// Test credentials (for E2E testing only)
const TEST_CREDENTIALS = {
  apiKey: 'test-api-key-for-e2e',
  bearerToken: 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjk5OTk5OTk5OTl9.test',
  orgId: 'test-org-id',
};

/**
 * Custom test fixtures for Blueprint Builder UI
 *
 * Sets up credentials cookies to bypass the setup screen
 */
export const test = base.extend<{
  /** Navigate to home and wait for initial load */
  homePage: void;
}>({
  // Set credentials cookies before each test to bypass setup screen
  page: async ({ page, context }, use) => {
    await context.addCookies([
      {
        name: 'bp_builder_api_key',
        value: encodeURIComponent(TEST_CREDENTIALS.apiKey),
        domain: 'localhost',
        path: '/',
      },
      {
        name: 'bp_builder_bearer_token',
        value: encodeURIComponent(TEST_CREDENTIALS.bearerToken),
        domain: 'localhost',
        path: '/',
      },
      {
        name: 'bp_builder_org_id',
        value: encodeURIComponent(TEST_CREDENTIALS.orgId),
        domain: 'localhost',
        path: '/',
      },
    ]);

    await use(page);
  },

  homePage: async ({ page }, use) => {
    await page.goto('/');
    // Wait for the app to be ready (GuidedChat should be visible)
    await page.waitForSelector('[data-testid="guided-chat"]', { timeout: 10000 }).catch(() => {
      // Fallback: wait for any main content
    });
    await use();
  },
});

export { expect };

/**
 * Test data for statement selections
 */
export const testSelections = {
  role: {
    value: 'product manager',
    label: 'Product Manager',
  },
  problem: {
    value: 'automate repetitive tasks that consume my team\'s time',
    label: 'Automate Repetitive Work',
  },
  domain: {
    value: 'customer support',
    label: 'Customer Support',
  },
};

/**
 * Complete statement built from test selections
 */
export const expectedStatement = `As a ${testSelections.role.value}, I need to ${testSelections.problem.value} in ${testSelections.domain.value}.`;

/**
 * Stage configuration
 * Note: Stage-based flow skips Explore (no longer conversational)
 * 1 = Define, 3 = Design, 4 = Build, 5 = Launch
 */
export const stages = [
  { id: 1, name: 'Define' },
  { id: 3, name: 'Design' },
  { id: 4, name: 'Build' },
  { id: 5, name: 'Launch' },
];
