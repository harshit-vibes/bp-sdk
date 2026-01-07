import { test, expect } from './fixtures';

/**
 * Review Screen and ActionGroup Tests
 *
 * Tests the main UI components on the Define stage (GuidedChat).
 * Note: Preview navigation is not implemented in the current version,
 * so we test the components that are visible on initial load.
 */

test.describe('ActionGroup - Footer Buttons', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('should show "Start Building" button on Define stage', async ({ page }) => {
    // On stage 1, should see the submit button
    await expect(page.getByRole('button', { name: /start building/i })).toBeVisible();
  });

  test('should disable submit button when statement incomplete', async ({ page }) => {
    const submitButton = page.getByRole('button', { name: /start building/i });
    await expect(submitButton).toBeDisabled();
  });

  test('should enable submit button when statement complete', async ({ page }) => {
    // Fill all slots
    await page.locator('button').filter({ hasText: 'role' }).first().click();
    await page.getByRole('button', { name: /Product Manager/i }).click();

    await page.locator('button').filter({ hasText: 'problem to solve' }).first().click();
    await page.getByRole('button', { name: /Automate Repetitive Work/i }).click();

    await page.locator('button').filter({ hasText: 'area' }).first().click();
    await page.getByRole('button', { name: /Customer Support/i }).first().click();

    // Submit button should be enabled
    const submitButton = page.getByRole('button', { name: /start building/i });
    await expect(submitButton).toBeEnabled();
  });

  test('should show sparkles icon on submit button', async ({ page }) => {
    // Check for Sparkles icon (SVG element within button)
    const submitButton = page.getByRole('button', { name: /start building/i });
    const icon = submitButton.locator('svg');
    await expect(icon).toBeVisible();
  });

  test('should show orange background on footer', async ({ page }) => {
    // Check footer has orange background class
    const footer = page.locator('.bg-orange-50').first();
    await expect(footer).toBeVisible();
  });
});

test.describe('Layout and Spacing', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('should have consistent layout structure', async ({ page }) => {
    // Check main layout elements exist
    await expect(page.locator('header').first()).toBeVisible();
    await expect(page.locator('main')).toBeVisible();
    await expect(page.locator('[class*="border-t"]').first()).toBeVisible(); // Footer
  });

  test('should fill available height', async ({ page }) => {
    // Main content area should take full height
    const main = page.locator('main');
    const boundingBox = await main.boundingBox();

    // Should have significant height
    expect(boundingBox?.height).toBeGreaterThan(200);
  });
});

test.describe('Mobile Responsiveness', () => {
  test.beforeEach(async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('should display correctly on mobile viewport', async ({ page }) => {
    // All main elements should still be visible
    await expect(page.getByText('As a')).toBeVisible();
    await expect(page.getByRole('button', { name: '1' })).toBeVisible();
    await expect(page.getByRole('button', { name: /start building/i })).toBeVisible();
  });

  test('should show all stage indicators on mobile', async ({ page }) => {
    // All 5 stage buttons should be visible
    for (let i = 1; i <= 5; i++) {
      await expect(page.getByRole('button', { name: String(i) })).toBeVisible();
    }
  });

  test('should open dialogs correctly on mobile', async ({ page }) => {
    // Click role slot
    await page.locator('button').filter({ hasText: 'role' }).first().click();

    // Dialog should open and be usable
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByText('Product Manager')).toBeVisible();
  });
});
