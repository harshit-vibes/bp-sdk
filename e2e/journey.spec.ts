import { test, expect } from './fixtures';
import { setupBuilderApiMock, mockBuilderResponses } from './mocks/builder-api-mock';

/**
 * Stage-Based Blueprint Building Journey Tests
 *
 * Tests the complete flow from Define to Launch using mocked API responses.
 * Flow: Define (1) → Design Review (3) → Agent Review (4) → Complete (5)
 */

test.describe('Stage-Based Blueprint Building Journey', () => {
  test('should complete the entire journey from Define to Launch', async ({ page }) => {
    // Setup mock API responses for all builder endpoints
    const mockApi = await setupBuilderApiMock(page);

    // Navigate to the app
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // === STAGE 1: DEFINE ===
    // Verify we're on the Define stage
    const header = page.locator('header');
    await expect(header.getByRole('heading', { name: 'Define Your Problem' })).toBeVisible();

    // Fill all statement slots
    await page.locator('button').filter({ hasText: 'role' }).first().click();
    await page.getByText('Product Manager').click();

    await page.locator('button').filter({ hasText: 'problem to solve' }).first().click();
    await page.getByText('Automate Repetitive Work').click();

    await page.locator('button').filter({ hasText: 'area' }).first().click();
    await page.getByText('Customer Support').click();

    // Submit the statement - triggers architect API call
    const submitButton = page.getByRole('button', { name: /start building/i });
    await expect(submitButton).toBeEnabled();
    await submitButton.click();

    // === STAGE 3: DESIGN REVIEW ===
    // Wait for architect API response and transition to design review
    await expect(header.getByRole('heading', { name: 'Review Architecture' })).toBeVisible({ timeout: 10000 });

    // Should show architecture preview from mock
    const main = page.locator('main');
    await expect(main.getByText('Support Coordinator')).toBeVisible();
    await expect(main.getByText('Ticket Classifier')).toBeVisible();

    // Should show HITL buttons
    const approveArchButton = page.getByRole('button', { name: /approve architecture/i });
    await expect(approveArchButton).toBeVisible();
    await expect(page.getByRole('button', { name: /request changes/i })).toBeVisible();

    // Approve the architecture - triggers craft API call for manager
    await approveArchButton.click();

    // === STAGE 4: BUILD - Manager Agent Review ===
    // Wait for craft API response and agent review
    await expect(page.getByRole('button', { name: /approve agent.*1\/4/i })).toBeVisible({ timeout: 10000 });

    // Should show manager agent details (use heading role to be specific)
    await expect(main.getByRole('heading', { name: 'Support Coordinator' })).toBeVisible();

    // Approve the manager agent - wait for enabled state
    const approveBtn1 = page.getByRole('button', { name: /approve agent.*1\/4/i });
    await expect(approveBtn1).toBeEnabled({ timeout: 15000 });
    await approveBtn1.click();

    // === Worker 1 Review ===
    const approveBtn2 = page.getByRole('button', { name: /approve agent.*2\/4/i });
    await expect(approveBtn2).toBeEnabled({ timeout: 15000 });
    await approveBtn2.click();

    // === Worker 2 Review ===
    const approveBtn3 = page.getByRole('button', { name: /approve agent.*3\/4/i });
    await expect(approveBtn3).toBeEnabled({ timeout: 15000 });
    await approveBtn3.click();

    // === Worker 3 Review ===
    const approveBtn4 = page.getByRole('button', { name: /approve agent.*4\/4/i });
    await expect(approveBtn4).toBeEnabled({ timeout: 15000 });
    await approveBtn4.click();

    // === STAGE 5: LAUNCH ===
    // Wait for create API response and blueprint creation
    await expect(header.getByRole('heading', { name: 'Blueprint Ready' })).toBeVisible({ timeout: 10000 });

    // Should show success content (blueprint name appears multiple times)
    await expect(main.getByText('bp-test-12345').first()).toBeVisible();

    // Should show complete mode actions
    await expect(page.getByRole('button', { name: /create another/i })).toBeVisible();

    // Verify API calls were made:
    // 4 craft calls (1 manager + 3 workers)
    expect(mockApi.getCraftCallCount()).toBe(4);
  });

  test('should handle Create Another action', async ({ page }) => {
    await setupBuilderApiMock(page);
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Quick journey through all stages
    await page.locator('button').filter({ hasText: 'role' }).first().click();
    await page.getByText('Product Manager').click();
    await page.locator('button').filter({ hasText: 'problem to solve' }).first().click();
    await page.getByText('Automate Repetitive Work').click();
    await page.locator('button').filter({ hasText: 'area' }).first().click();
    await page.getByText('Customer Support').click();
    await page.getByRole('button', { name: /start building/i }).click();

    // Approve architecture
    await page.getByRole('button', { name: /approve architecture/i }).click({ timeout: 15000 });

    // Approve all agents - wait for each to be enabled before clicking
    const approveBtn1 = page.getByRole('button', { name: /approve agent.*1\/4/i });
    await expect(approveBtn1).toBeEnabled({ timeout: 15000 });
    await approveBtn1.click();

    const approveBtn2 = page.getByRole('button', { name: /approve agent.*2\/4/i });
    await expect(approveBtn2).toBeEnabled({ timeout: 15000 });
    await approveBtn2.click();

    const approveBtn3 = page.getByRole('button', { name: /approve agent.*3\/4/i });
    await expect(approveBtn3).toBeEnabled({ timeout: 15000 });
    await approveBtn3.click();

    const approveBtn4 = page.getByRole('button', { name: /approve agent.*4\/4/i });
    await expect(approveBtn4).toBeEnabled({ timeout: 15000 });
    await approveBtn4.click();

    // Wait for complete state
    const header = page.locator('header');
    await expect(header.getByRole('heading', { name: 'Blueprint Ready' })).toBeVisible({ timeout: 15000 });

    // Click Create Another
    await page.getByRole('button', { name: /create another/i }).click();

    // Should reset to stage 1
    await expect(header.getByRole('heading', { name: 'Define Your Problem' })).toBeVisible();
    const main = page.locator('main');
    await expect(main.getByText('As a')).toBeVisible();
  });
});

test.describe('HITL Interactions', () => {
  test('should handle architecture revision request', async ({ page }) => {
    let architectCallCount = 0;

    // Custom mock that returns updated architecture on second call
    await page.route('**/api/builder/architect', async (route) => {
      architectCallCount++;

      const response = architectCallCount === 1
        ? mockBuilderResponses.architect('test-session-123')
        : {
            ...mockBuilderResponses.architect('test-session-123'),
            workers: [
              ...mockBuilderResponses.architect('test-session-123').workers,
              { name: 'Escalation Handler', purpose: 'Handles complex cases requiring human escalation.' },
            ],
          };

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(response),
      });
    });

    await page.route('**/api/builder/craft', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockBuilderResponses.craftManager('test-session-123')),
      });
    });

    await page.route('**/api/builder/create', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockBuilderResponses.create('test-session-123')),
      });
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Complete stage 1
    await page.locator('button').filter({ hasText: 'role' }).first().click();
    await page.getByText('Product Manager').click();
    await page.locator('button').filter({ hasText: 'problem to solve' }).first().click();
    await page.getByText('Automate Repetitive Work').click();
    await page.locator('button').filter({ hasText: 'area' }).first().click();
    await page.getByText('Customer Support').click();
    await page.getByRole('button', { name: /start building/i }).click();

    // Wait for architecture HITL
    const main = page.locator('main');
    await expect(main.getByText('Support Coordinator')).toBeVisible({ timeout: 10000 });

    // Click Request Changes
    await page.getByRole('button', { name: /request changes/i }).click();

    // Enter revision feedback
    await expect(page.locator('textarea')).toBeVisible();
    await page.locator('textarea').fill('Please add an escalation handler worker');
    await page.getByRole('button', { name: /submit feedback/i }).click();

    // Should show updated architecture with new worker
    await expect(main.getByText('Escalation Handler')).toBeVisible({ timeout: 10000 });

    // Verify architect was called twice
    expect(architectCallCount).toBe(2);
  });

  test('should handle agent revision request', async ({ page }) => {
    let craftCallCount = 0;

    await page.route('**/api/builder/architect', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockBuilderResponses.architect('test-session-123')),
      });
    });

    await page.route('**/api/builder/craft', async (route) => {
      craftCallCount++;

      // On second call (revision), return updated agent
      const response = craftCallCount === 1
        ? mockBuilderResponses.craftManager('test-session-123')
        : {
            ...mockBuilderResponses.craftManager('test-session-123'),
            agent_yaml: {
              ...mockBuilderResponses.craftManager('test-session-123').agent_yaml,
              temperature: 0.1, // Lower temperature after revision
              role: 'Senior Support Lead', // Updated role
            },
          };

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(response),
      });
    });

    await page.route('**/api/builder/create', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockBuilderResponses.create('test-session-123')),
      });
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Quick path to agent HITL
    await page.locator('button').filter({ hasText: 'role' }).first().click();
    await page.getByText('Product Manager').click();
    await page.locator('button').filter({ hasText: 'problem to solve' }).first().click();
    await page.getByText('Automate Repetitive Work').click();
    await page.locator('button').filter({ hasText: 'area' }).first().click();
    await page.getByText('Customer Support').click();
    await page.getByRole('button', { name: /start building/i }).click();

    // Approve architecture
    await page.getByRole('button', { name: /approve architecture/i }).click({ timeout: 10000 });

    // Wait for manager agent HITL
    await expect(page.getByRole('button', { name: /approve agent.*1\/4/i })).toBeVisible({ timeout: 10000 });

    // Request changes to the agent
    await page.getByRole('button', { name: /request changes/i }).click();
    await page.locator('textarea').fill('Please lower the temperature for more consistent responses');
    await page.getByRole('button', { name: /submit feedback/i }).click();

    // Should show updated agent - check for new role
    const main = page.locator('main');
    await expect(main.getByText('Senior Support Lead')).toBeVisible({ timeout: 10000 });

    // Verify craft was called twice
    expect(craftCallCount).toBe(2);
  });
});

test.describe('Error Handling', () => {
  test('should display error message when architect API fails', async ({ page }) => {
    await page.route('**/api/builder/architect', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Failed to design architecture. Please try again.' }),
      });
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Complete stage 1 and submit
    await page.locator('button').filter({ hasText: 'role' }).first().click();
    await page.getByText('Product Manager').click();
    await page.locator('button').filter({ hasText: 'problem to solve' }).first().click();
    await page.getByText('Automate Repetitive Work').click();
    await page.locator('button').filter({ hasText: 'area' }).first().click();
    await page.getByText('Customer Support').click();
    await page.getByRole('button', { name: /start building/i }).click();

    // Should show error message
    await expect(page.getByText('Failed to design architecture')).toBeVisible({ timeout: 10000 });

    // After error, verify we can still see the page (error state visible)
    // The UI transitions to show error, button may change to "Try Again" or similar
    const header = page.locator('header');
    await expect(header.getByRole('heading', { name: 'Define Your Problem' })).toBeVisible();
  });

  test('should display error message when craft API fails', async ({ page }) => {
    await page.route('**/api/builder/architect', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockBuilderResponses.architect('test-session-123')),
      });
    });

    await page.route('**/api/builder/craft', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Failed to craft agent. Please try again.' }),
      });
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Complete stage 1 and submit
    await page.locator('button').filter({ hasText: 'role' }).first().click();
    await page.getByText('Product Manager').click();
    await page.locator('button').filter({ hasText: 'problem to solve' }).first().click();
    await page.getByText('Automate Repetitive Work').click();
    await page.locator('button').filter({ hasText: 'area' }).first().click();
    await page.getByText('Customer Support').click();
    await page.getByRole('button', { name: /start building/i }).click();

    // Approve architecture
    await page.getByRole('button', { name: /approve architecture/i }).click({ timeout: 10000 });

    // Should show error message
    await expect(page.getByText('Failed to craft agent')).toBeVisible({ timeout: 10000 });
  });

  test('should display error message when create API fails', async ({ page }) => {
    await setupBuilderApiMock(page, {
      createError: 'Failed to create blueprint. Please try again.',
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Quick journey through all stages
    await page.locator('button').filter({ hasText: 'role' }).first().click();
    await page.getByText('Product Manager').click();
    await page.locator('button').filter({ hasText: 'problem to solve' }).first().click();
    await page.getByText('Automate Repetitive Work').click();
    await page.locator('button').filter({ hasText: 'area' }).first().click();
    await page.getByText('Customer Support').click();
    await page.getByRole('button', { name: /start building/i }).click();

    // Approve architecture
    await page.getByRole('button', { name: /approve architecture/i }).click({ timeout: 10000 });

    // Approve all agents
    await page.getByRole('button', { name: /approve agent.*1\/4/i }).click({ timeout: 10000 });
    await page.getByRole('button', { name: /approve agent.*2\/4/i }).click({ timeout: 10000 });
    await page.getByRole('button', { name: /approve agent.*3\/4/i }).click({ timeout: 10000 });
    await page.getByRole('button', { name: /approve agent.*4\/4/i }).click({ timeout: 10000 });

    // Should show error message
    await expect(page.getByText('Failed to create blueprint')).toBeVisible({ timeout: 10000 });
  });
});

test.describe('Session Management', () => {
  test('should send session_id in subsequent API calls', async ({ page }) => {
    const capturedRequests: { endpoint: string; body: Record<string, unknown> }[] = [];
    const sessionId = 'test-session-123';

    await page.route('**/api/builder/architect', async (route, request) => {
      const body = request.postDataJSON() as Record<string, unknown>;
      capturedRequests.push({ endpoint: 'architect', body });

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockBuilderResponses.architect(sessionId)),
      });
    });

    await page.route('**/api/builder/craft', async (route, request) => {
      const body = request.postDataJSON() as Record<string, unknown>;
      capturedRequests.push({ endpoint: 'craft', body });

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockBuilderResponses.craftManager(sessionId)),
      });
    });

    await page.route('**/api/builder/create', async (route, request) => {
      const body = request.postDataJSON() as Record<string, unknown>;
      capturedRequests.push({ endpoint: 'create', body });

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockBuilderResponses.create(sessionId)),
      });
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Complete stage 1 and submit
    await page.locator('button').filter({ hasText: 'role' }).first().click();
    await page.getByText('Product Manager').click();
    await page.locator('button').filter({ hasText: 'problem to solve' }).first().click();
    await page.getByText('Automate Repetitive Work').click();
    await page.locator('button').filter({ hasText: 'area' }).first().click();
    await page.getByText('Customer Support').click();
    await page.getByRole('button', { name: /start building/i }).click();

    // Wait for architect response
    await page.getByRole('button', { name: /approve architecture/i }).click({ timeout: 10000 });

    // Wait for craft response
    await expect(page.getByRole('button', { name: /approve agent.*1\/4/i })).toBeVisible({ timeout: 10000 });

    // Verify requests
    expect(capturedRequests.length).toBeGreaterThanOrEqual(2);

    // First architect call should have requirements but no session_id
    const architectCall = capturedRequests.find(r => r.endpoint === 'architect');
    expect(architectCall?.body.requirements).toBeDefined();

    // Craft call should have session_id from architect response
    const craftCall = capturedRequests.find(r => r.endpoint === 'craft');
    expect(craftCall?.body.session_id).toBe(sessionId);
  });
});
