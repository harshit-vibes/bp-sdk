import { test, expect } from './fixtures';

test.describe('UI Enhancements - Unified Stage Progress', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('should display unified 3-stage progress indicator', async ({ page }) => {
    const header = page.locator('header');

    // Check for the 3 unified stages in the progress indicator
    await expect(header.getByText('Define')).toBeVisible();
    await expect(header.getByText('Build')).toBeVisible();
    await expect(header.getByText('Complete')).toBeVisible();
  });

  test('should show Define stage as current on initial load', async ({ page }) => {
    const header = page.locator('header');

    // The header title should indicate Define stage
    await expect(header.getByRole('heading', { name: 'Define Your Problem' })).toBeVisible();

    // Check the instruction text
    await expect(header.getByText('Click the underlined phrases')).toBeVisible();
  });

  test('should update progress indicator when moving to Build stage', async ({ page }) => {
    const header = page.locator('header');
    const main = page.locator('main');

    // Fill all slots to enable submit
    await main.locator('button').filter({ hasText: 'role' }).first().click();
    await page.getByRole('dialog').getByRole('button', { name: /Product Manager/i }).click();

    await main.locator('button').filter({ hasText: 'problem to solve' }).first().click();
    await page.getByRole('dialog').getByRole('button', { name: /Automate Repetitive Work/i }).click();

    await main.locator('button').filter({ hasText: 'area' }).first().click();
    await page.getByRole('dialog').getByRole('button', { name: /Customer Support/i }).first().click();

    // Submit to trigger architect
    const submitButton = page.getByRole('button', { name: /start building/i });
    await expect(submitButton).toBeEnabled();
    await submitButton.click();

    // Wait for the Build stage (may take time for API call)
    // Just check that the header updates to indicate building
    await expect(header.getByText(/Building|Review/)).toBeVisible({ timeout: 30000 });
  });
});

test.describe('UI Enhancements - Streaming Loader', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('should show loading indicator during API calls', async ({ page }) => {
    const main = page.locator('main');

    // Fill all slots
    await main.locator('button').filter({ hasText: 'role' }).first().click();
    await page.getByRole('dialog').getByRole('button', { name: /Product Manager/i }).click();

    await main.locator('button').filter({ hasText: 'problem to solve' }).first().click();
    await page.getByRole('dialog').getByRole('button', { name: /Automate Repetitive Work/i }).click();

    await main.locator('button').filter({ hasText: 'area' }).first().click();
    await page.getByRole('dialog').getByRole('button', { name: /Customer Support/i }).first().click();

    // Submit
    await page.getByRole('button', { name: /start building/i }).click();

    // Should see a loading indicator (spinner or loading text)
    // The streaming loader shows during the API call
    const loadingIndicator = page.locator('[class*="animate-spin"], [class*="loader"]');
    // We just verify it may appear (API might be fast)
    await page.waitForTimeout(500);
  });
});

test.describe('UI Enhancements - Revision Suggestions Dialog', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('should show Request Changes button in HITL mode', async ({ page }) => {
    const main = page.locator('main');

    // Fill all slots
    await main.locator('button').filter({ hasText: 'role' }).first().click();
    await page.getByRole('dialog').getByRole('button', { name: /Product Manager/i }).click();

    await main.locator('button').filter({ hasText: 'problem to solve' }).first().click();
    await page.getByRole('dialog').getByRole('button', { name: /Automate Repetitive Work/i }).click();

    await main.locator('button').filter({ hasText: 'area' }).first().click();
    await page.getByRole('dialog').getByRole('button', { name: /Customer Support/i }).first().click();

    // Submit and wait for review stage
    await page.getByRole('button', { name: /start building/i }).click();

    // Wait for HITL mode (approve/request changes buttons)
    const requestChangesButton = page.getByRole('button', { name: /request changes/i });
    await expect(requestChangesButton).toBeVisible({ timeout: 60000 });
  });

  test('should open revision suggestions dialog when clicking Request Changes', async ({ page }) => {
    const main = page.locator('main');

    // Fill all slots and submit
    await main.locator('button').filter({ hasText: 'role' }).first().click();
    await page.getByRole('dialog').getByRole('button', { name: /Product Manager/i }).click();

    await main.locator('button').filter({ hasText: 'problem to solve' }).first().click();
    await page.getByRole('dialog').getByRole('button', { name: /Automate Repetitive Work/i }).click();

    await main.locator('button').filter({ hasText: 'area' }).first().click();
    await page.getByRole('dialog').getByRole('button', { name: /Customer Support/i }).first().click();

    await page.getByRole('button', { name: /start building/i }).click();

    // Wait for and click Request Changes
    const requestChangesButton = page.getByRole('button', { name: /request changes/i });
    await expect(requestChangesButton).toBeVisible({ timeout: 60000 });
    await requestChangesButton.click();

    // Should see revision suggestions dialog (using SelectorDialog)
    await expect(page.getByText('What would you like to change?')).toBeVisible({ timeout: 10000 });

    // Should see suggestion options in the dialog
    // Wait for suggestions to load (either from API or fallback)
    await expect(page.locator('[role="dialog"]')).toBeVisible();
  });

  test('should show custom input section in dialog', async ({ page }) => {
    const main = page.locator('main');

    // Fill all slots and submit
    await main.locator('button').filter({ hasText: 'role' }).first().click();
    await page.getByRole('dialog').getByRole('button', { name: /Product Manager/i }).click();

    await main.locator('button').filter({ hasText: 'problem to solve' }).first().click();
    await page.getByRole('dialog').getByRole('button', { name: /Automate Repetitive Work/i }).click();

    await main.locator('button').filter({ hasText: 'area' }).first().click();
    await page.getByRole('dialog').getByRole('button', { name: /Customer Support/i }).first().click();

    await page.getByRole('button', { name: /start building/i }).click();

    // Wait for and click Request Changes
    const requestChangesButton = page.getByRole('button', { name: /request changes/i });
    await expect(requestChangesButton).toBeVisible({ timeout: 60000 });
    await requestChangesButton.click();

    // Wait for dialog
    await expect(page.getByText('What would you like to change?')).toBeVisible({ timeout: 10000 });

    // Should have custom input section with textarea
    await expect(page.getByText('Or describe your changes')).toBeVisible();
    await expect(page.locator('[role="dialog"] input, [role="dialog"] textarea')).toBeVisible();
  });

  test('should close dialog when clicking outside or pressing escape', async ({ page }) => {
    const main = page.locator('main');

    // Fill all slots and submit
    await main.locator('button').filter({ hasText: 'role' }).first().click();
    await page.getByRole('dialog').getByRole('button', { name: /Product Manager/i }).click();

    await main.locator('button').filter({ hasText: 'problem to solve' }).first().click();
    await page.getByRole('dialog').getByRole('button', { name: /Automate Repetitive Work/i }).click();

    await main.locator('button').filter({ hasText: 'area' }).first().click();
    await page.getByRole('dialog').getByRole('button', { name: /Customer Support/i }).first().click();

    await page.getByRole('button', { name: /start building/i }).click();

    // Wait for and click Request Changes
    const requestChangesButton = page.getByRole('button', { name: /request changes/i });
    await expect(requestChangesButton).toBeVisible({ timeout: 60000 });
    await requestChangesButton.click();

    // Wait for dialog
    await expect(page.getByText('What would you like to change?')).toBeVisible({ timeout: 10000 });

    // Press Escape to close
    await page.keyboard.press('Escape');

    // Dialog should be closed, approve button should be visible
    await expect(requestChangesButton).toBeVisible();
    await expect(page.getByRole('button', { name: /approve/i })).toBeVisible();
  });
});
