import { test, expect } from './fixtures';

/**
 * Stage Navigation Tests
 *
 * Tests the stage progress indicator in the header.
 * Note: Stage navigation (clicking to preview) is not implemented in current version.
 * The UI flow is: Define (1) → Design (3) → Build (4) → Launch (5)
 * Stage 2 (Explore) is skipped in the current implementation.
 */

test.describe('Stage Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('should display 5 stage indicators', async ({ page }) => {
    // Find all stage buttons (numbered 1-5)
    const stage1 = page.getByRole('button', { name: '1' });
    const stage2 = page.getByRole('button', { name: '2' });
    const stage3 = page.getByRole('button', { name: '3' });
    const stage4 = page.getByRole('button', { name: '4' });
    const stage5 = page.getByRole('button', { name: '5' });

    await expect(stage1).toBeVisible();
    await expect(stage2).toBeVisible();
    await expect(stage3).toBeVisible();
    await expect(stage4).toBeVisible();
    await expect(stage5).toBeVisible();
  });

  test('should show stage names below indicators', async ({ page }) => {
    // Check for stage labels in the header progress area
    const header = page.locator('header');
    await expect(header.getByText('Define', { exact: true })).toBeVisible();
    await expect(header.getByText('Explore', { exact: true })).toBeVisible();
    await expect(header.getByText('Design', { exact: true })).toBeVisible();
    await expect(header.getByText('Build', { exact: true })).toBeVisible();
    await expect(header.getByText('Launch', { exact: true })).toBeVisible();
  });

  test('should highlight stage 1 (Define) as current on initial load', async ({ page }) => {
    // Stage 1 button should have the current/active styling
    const stage1 = page.getByRole('button', { name: '1' });

    // Check it has the orange/active border (current stage has orange border)
    await expect(stage1).toHaveClass(/border-orange/);
  });

  test('should show stages 2-5 as future on initial load', async ({ page }) => {
    // Stages 2-5 should not have the active/completed styling
    const stage2 = page.getByRole('button', { name: '2' });
    const stage3 = page.getByRole('button', { name: '3' });
    const stage4 = page.getByRole('button', { name: '4' });
    const stage5 = page.getByRole('button', { name: '5' });

    // Future stages have muted styling, not orange background
    await expect(stage2).toHaveClass(/bg-muted/);
    await expect(stage3).toHaveClass(/bg-muted/);
    await expect(stage4).toHaveClass(/bg-muted/);
    await expect(stage5).toHaveClass(/bg-muted/);
  });

  test('should show connectors between stage indicators', async ({ page }) => {
    // Check for connector lines (these are divs with h-0.5 class)
    const connectors = page.locator('[class*="h-0.5"]');
    // At least 4 horizontal connector lines should exist
    await expect(connectors.first()).toBeVisible();
  });
});

test.describe('Stage Header', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('should display stage title in header', async ({ page }) => {
    // Check for the Define stage title in the header
    const header = page.locator('header');
    await expect(header.getByRole('heading', { name: 'Define Your Problem' })).toBeVisible();
  });

  test('should display stage instruction in header', async ({ page }) => {
    // Check for the instruction text in header area
    const header = page.locator('header');
    await expect(header.getByText('Click the underlined phrases to describe your problem')).toBeVisible();
  });
});
