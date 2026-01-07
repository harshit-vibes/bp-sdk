/**
 * Real Integration Tests for Blueprint Builder Journey (Stage-Based API)
 *
 * These tests use the real API and create actual blueprints.
 * They require:
 * - The FastAPI backend running on port 8000
 * - The Next.js frontend running on port 3000
 * - Valid Lyzr credentials in environment variables
 *
 * Run with: npm run test:e2e:integration
 *
 * Note: These tests are slower due to LLM API calls (~30-60 seconds per journey)
 *
 * Flow (stage-based, no SSE):
 * 1. Define: User fills GuidedChat statement
 * 2. Design Review: POST /api/builder/architect → user approves architecture
 * 3. Build: POST /api/builder/craft (per agent) → user approves each agent
 * 4. Complete: POST /api/builder/create → success with Studio URL
 */

import { test, expect, type Page } from '@playwright/test';

// Increase timeout for real API calls (LLM responses take time)
test.setTimeout(300000); // 5 minutes per test

// Cookie names (must match setup-screen.tsx)
const COOKIE_NAMES = {
  API_KEY: "bp_builder_api_key",
  BEARER_TOKEN: "bp_builder_bearer_token",
  ORG_ID: "bp_builder_org_id",
};

// Load credentials from environment
const CREDENTIALS = {
  apiKey: process.env.LYZR_API_KEY || '',
  bearerToken: process.env.BLUEPRINT_BEARER_TOKEN || '',
  orgId: process.env.LYZR_ORG_ID || '',
};

// Helper to fill the statement builder
async function fillStatementBuilder(page: Page) {
  // Fill role
  await page.locator('button').filter({ hasText: 'role' }).first().click();
  await page.getByRole('button', { name: /Product Manager/i }).click();

  // Fill problem
  await page.locator('button').filter({ hasText: 'problem to solve' }).first().click();
  await page.getByRole('button', { name: /Automate Repetitive Work/i }).click();

  // Fill domain
  await page.locator('button').filter({ hasText: 'area' }).first().click();
  await page.getByRole('button', { name: /Customer Support/i }).first().click();
}

// Helper to wait for loading to complete
async function waitForLoading(page: Page, timeout = 60000) {
  const spinner = page.locator('[class*="animate-spin"]');
  try {
    await spinner.waitFor({ state: 'visible', timeout: 5000 });
    await spinner.waitFor({ state: 'hidden', timeout });
  } catch {
    // Spinner might not appear if response is fast
  }
}

// Helper to set credentials cookies
async function setCredentialsCookies(page: Page) {
  if (!CREDENTIALS.apiKey || !CREDENTIALS.bearerToken || !CREDENTIALS.orgId) {
    throw new Error('Missing credentials. Set LYZR_API_KEY, BLUEPRINT_BEARER_TOKEN, and LYZR_ORG_ID environment variables.');
  }

  await page.context().addCookies([
    { name: COOKIE_NAMES.API_KEY, value: CREDENTIALS.apiKey, path: '/', domain: 'localhost' },
    { name: COOKIE_NAMES.BEARER_TOKEN, value: CREDENTIALS.bearerToken, path: '/', domain: 'localhost' },
    { name: COOKIE_NAMES.ORG_ID, value: CREDENTIALS.orgId, path: '/', domain: 'localhost' },
  ]);
}

test.describe('Real Stage-Based Blueprint Building Journey', () => {
  test.beforeEach(async ({ page }) => {
    // Capture browser console logs for debugging (only errors)
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log(`[browser error] ${msg.text()}`);
      }
    });

    // Set credentials cookies to skip setup screen
    await setCredentialsCookies(page);

    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('should complete a full blueprint creation journey', async ({ page }) => {
    const header = page.locator('header');
    const main = page.locator('main');

    // === STAGE 1: DEFINE ===
    await expect(header.getByRole('heading', { name: 'Define Your Problem' })).toBeVisible();
    console.log('Stage 1: Define - Filling statement');

    // Fill the statement
    await fillStatementBuilder(page);

    // Submit - triggers architect API call
    const submitButton = page.getByRole('button', { name: /start building/i });
    await expect(submitButton).toBeEnabled();
    await submitButton.click();

    // === STAGE 3: DESIGN REVIEW ===
    // Wait for architect API response (can take 10-30 seconds)
    await expect(header.getByRole('heading', { name: 'Review Architecture' })).toBeVisible({ timeout: 120000 });
    console.log('Stage 3: Design Review - Architecture received');

    // Verify architecture content
    await expect(main.getByText('manager', { exact: false })).toBeVisible();

    // Approve architecture - triggers craft API call for manager
    const approveArchBtn = page.getByRole('button', { name: /approve architecture/i });
    await expect(approveArchBtn).toBeVisible();
    await approveArchBtn.click();
    await waitForLoading(page, 120000);
    console.log('Architecture approved');

    // === STAGE 4: BUILD - Agent Reviews ===
    // The number of agents depends on the architecture
    // We'll loop until we reach the Complete stage
    let agentCount = 0;
    const maxAgents = 10;

    while (agentCount < maxAgents) {
      const currentHeader = await header.locator('h1').textContent().catch(() => '');

      // Check if we've reached the complete stage
      if (currentHeader === 'Blueprint Ready') {
        console.log(`Reached Blueprint Ready after reviewing ${agentCount} agents`);
        break;
      }

      // Look for agent approval button
      const approveAgentBtn = page.getByRole('button', { name: /approve agent/i });
      const hasApproveAgent = await approveAgentBtn.isVisible().catch(() => false);

      if (hasApproveAgent) {
        agentCount++;
        console.log(`Approving agent ${agentCount}`);
        await approveAgentBtn.click();
        await waitForLoading(page, 120000);
      } else {
        // Wait a bit and check again
        await page.waitForTimeout(2000);
      }
    }

    // === STAGE 5: COMPLETE ===
    await expect(header.getByRole('heading', { name: 'Blueprint Ready' })).toBeVisible({ timeout: 60000 });
    console.log('Stage 5: Complete - Blueprint created');

    // Verify success elements
    const viewBlueprintLink = page.getByRole('link', { name: /open in lyzr/i });
    await expect(viewBlueprintLink).toBeVisible();

    // Get the blueprint URL for logging
    const blueprintUrl = await viewBlueprintLink.getAttribute('href');
    console.log('Created blueprint:', blueprintUrl);

    // Should show Create Another button
    await expect(page.getByRole('button', { name: /create another/i })).toBeVisible();
  });

  test('should handle architecture revision request', async ({ page }) => {
    const header = page.locator('header');

    // Fill and submit
    await fillStatementBuilder(page);
    await page.getByRole('button', { name: /start building/i }).click();

    // Wait for design review stage
    await expect(header.getByRole('heading', { name: 'Review Architecture' })).toBeVisible({ timeout: 120000 });
    console.log('Received initial architecture');

    // Request changes instead of approving
    const requestChangesBtn = page.getByRole('button', { name: /request changes/i });
    await expect(requestChangesBtn).toBeVisible();
    await requestChangesBtn.click();

    // Enter feedback
    const textarea = page.locator('textarea');
    await expect(textarea).toBeVisible();
    await textarea.fill('Please add a priority analyzer worker to categorize tickets by urgency level (high/medium/low).');
    await page.getByRole('button', { name: /submit feedback/i }).click();
    console.log('Submitted revision feedback');

    // Wait for loading to complete
    await waitForLoading(page, 120000);

    // Should still be at architecture review with revised content
    await expect(header.getByRole('heading', { name: 'Review Architecture' })).toBeVisible({ timeout: 120000 });
    console.log('Received revised architecture');

    // Now approve the revised architecture
    const approveBtn = page.getByRole('button', { name: /approve architecture/i });
    await expect(approveBtn).toBeVisible();
    await approveBtn.click();
    await waitForLoading(page, 120000);
    console.log('Approved revised architecture');

    // Should proceed to agent review
    await expect(page.getByRole('button', { name: /approve agent/i })).toBeVisible({ timeout: 120000 });
  });
});

test.describe('Create Another Flow', () => {
  test('should reset and start new journey', async ({ page }) => {
    const header = page.locator('header');

    // Set credentials cookies to skip setup screen
    await setCredentialsCookies(page);

    // First, complete a journey
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    await fillStatementBuilder(page);
    await page.getByRole('button', { name: /start building/i }).click();

    // Approve architecture
    await expect(header.getByRole('heading', { name: 'Review Architecture' })).toBeVisible({ timeout: 120000 });
    await page.getByRole('button', { name: /approve architecture/i }).click();
    await waitForLoading(page, 120000);

    // Approve all agents until complete
    const maxAgents = 10;
    let agentCount = 0;

    while (agentCount < maxAgents) {
      const currentHeader = await header.locator('h1').textContent().catch(() => '');

      if (currentHeader === 'Blueprint Ready') {
        break;
      }

      const approveAgentBtn = page.getByRole('button', { name: /approve agent/i });
      const hasApprove = await approveAgentBtn.isVisible().catch(() => false);

      if (hasApprove) {
        agentCount++;
        await approveAgentBtn.click();
        await waitForLoading(page, 120000);
      } else {
        await page.waitForTimeout(2000);
      }
    }

    // Should be at complete stage
    await expect(header.getByRole('heading', { name: 'Blueprint Ready' })).toBeVisible({ timeout: 60000 });

    // Click Create Another
    await page.getByRole('button', { name: /create another/i }).click();

    // Should reset to Define stage
    await expect(header.getByRole('heading', { name: 'Define Your Problem' })).toBeVisible({ timeout: 10000 });
    await expect(page.locator('main').getByText('As a')).toBeVisible();

    console.log('Successfully reset to new journey');
  });
});
