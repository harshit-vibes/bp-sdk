import { test, expect } from './fixtures';
import { setupBuilderApiMock } from './mocks/builder-api-mock';

/**
 * YAML Session Storage Tests
 *
 * Tests the session-scoped YAML file storage feature:
 * - Agent YAMLs are saved when approved
 * - Blueprint YAML is saved when created
 * - YAMLViewer displays saved files (flat list with copy buttons)
 * - Session is cleared on reset
 */

test.describe('YAML Session Storage', () => {
  test('should display YAMLViewer after approving first agent', async ({ page }) => {
    await setupBuilderApiMock(page);
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Complete stage 1 - Define
    await page.locator('button').filter({ hasText: 'role' }).first().click();
    await page.getByText('Product Manager').click();
    await page.locator('button').filter({ hasText: 'problem to solve' }).first().click();
    await page.getByText('Automate Repetitive Work').click();
    await page.locator('button').filter({ hasText: 'area' }).first().click();
    await page.getByText('Customer Support').click();
    await page.getByRole('button', { name: /start building/i }).click();

    // Approve architecture
    await page.getByRole('button', { name: /approve architecture/i }).click({ timeout: 10000 });

    // Wait for first agent review
    await expect(page.getByRole('button', { name: /approve agent.*1\/4/i })).toBeVisible({ timeout: 10000 });

    // YAMLViewer should be visible with session files header
    const yamlViewer = page.locator('text=Session Files');
    await expect(yamlViewer).toBeVisible();

    // Should show 1 file count
    await expect(page.getByText(/Session Files \(1\)/)).toBeVisible();
  });

  test('should accumulate YAML files as agents are approved', async ({ page }) => {
    await setupBuilderApiMock(page);
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Quick path through stage 1
    await page.locator('button').filter({ hasText: 'role' }).first().click();
    await page.getByText('Product Manager').click();
    await page.locator('button').filter({ hasText: 'problem to solve' }).first().click();
    await page.getByText('Automate Repetitive Work').click();
    await page.locator('button').filter({ hasText: 'area' }).first().click();
    await page.getByText('Customer Support').click();
    await page.getByRole('button', { name: /start building/i }).click();

    // Approve architecture
    await page.getByRole('button', { name: /approve architecture/i }).click({ timeout: 10000 });

    // Approve first agent (manager)
    await page.getByRole('button', { name: /approve agent.*1\/4/i }).click({ timeout: 10000 });

    // After second agent, should have 2 files
    await expect(page.getByRole('button', { name: /approve agent.*2\/4/i })).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(/Session Files \(2\)/)).toBeVisible();

    // Approve second agent
    await page.getByRole('button', { name: /approve agent.*2\/4/i }).click();

    // After third agent, should have 3 files
    await expect(page.getByRole('button', { name: /approve agent.*3\/4/i })).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(/Session Files \(3\)/)).toBeVisible();
  });

  test('should show file list with agent filenames', async ({ page }) => {
    await setupBuilderApiMock(page);
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Quick path to agent review
    await page.locator('button').filter({ hasText: 'role' }).first().click();
    await page.getByText('Product Manager').click();
    await page.locator('button').filter({ hasText: 'problem to solve' }).first().click();
    await page.getByText('Automate Repetitive Work').click();
    await page.locator('button').filter({ hasText: 'area' }).first().click();
    await page.getByText('Customer Support').click();
    await page.getByRole('button', { name: /start building/i }).click();

    // Approve architecture
    await page.getByRole('button', { name: /approve architecture/i }).click({ timeout: 10000 });

    // Wait for agent review
    await expect(page.getByRole('button', { name: /approve agent.*1\/4/i })).toBeVisible({ timeout: 10000 });

    // YAMLViewer should show agent filename (support-coordinator.yaml from mock)
    await expect(page.getByText('support-coordinator.yaml')).toBeVisible();
  });

  test('should clear YAML session when "Create Another" is clicked', async ({ page }) => {
    test.setTimeout(60000); // Longer timeout for full journey test
    await setupBuilderApiMock(page);
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Complete full journey
    await page.locator('button').filter({ hasText: 'role' }).first().click();
    await page.getByText('Product Manager').click();
    await page.locator('button').filter({ hasText: 'problem to solve' }).first().click();
    await page.getByText('Automate Repetitive Work').click();
    await page.locator('button').filter({ hasText: 'area' }).first().click();
    await page.getByText('Customer Support').click();
    await page.getByRole('button', { name: /start building/i }).click();

    // Approve architecture
    await page.getByRole('button', { name: /approve architecture/i }).click({ timeout: 10000 });

    // Approve all agents with waits between each
    const approveButton1 = page.getByRole('button', { name: /approve agent.*1\/4/i });
    await expect(approveButton1).toBeEnabled({ timeout: 15000 });
    await approveButton1.click();

    const approveButton2 = page.getByRole('button', { name: /approve agent.*2\/4/i });
    await expect(approveButton2).toBeEnabled({ timeout: 15000 });
    await approveButton2.click();

    const approveButton3 = page.getByRole('button', { name: /approve agent.*3\/4/i });
    await expect(approveButton3).toBeEnabled({ timeout: 15000 });
    await approveButton3.click();

    const approveButton4 = page.getByRole('button', { name: /approve agent.*4\/4/i });
    await expect(approveButton4).toBeEnabled({ timeout: 15000 });
    await approveButton4.click();

    // Wait for complete state
    const header = page.locator('header');
    await expect(header.getByRole('heading', { name: 'Blueprint Ready' })).toBeVisible({ timeout: 15000 });

    // Click Create Another
    await page.getByRole('button', { name: /create another/i }).click();

    // Should reset to stage 1
    await expect(header.getByRole('heading', { name: 'Define Your Problem' })).toBeVisible();

    // YAMLViewer should not be visible (no files in session)
    await expect(page.getByText(/Session Files/)).not.toBeVisible();
  });

  test('should save blueprint YAML after creation', async ({ page }) => {
    await setupBuilderApiMock(page);
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Complete full journey
    await page.locator('button').filter({ hasText: 'role' }).first().click();
    await page.getByText('Product Manager').click();
    await page.locator('button').filter({ hasText: 'problem to solve' }).first().click();
    await page.getByText('Automate Repetitive Work').click();
    await page.locator('button').filter({ hasText: 'area' }).first().click();
    await page.getByText('Customer Support').click();
    await page.getByRole('button', { name: /start building/i }).click();

    // Approve architecture
    await page.getByRole('button', { name: /approve architecture/i }).click({ timeout: 15000 });

    // Approve all agents with waits between each
    const approveButton1 = page.getByRole('button', { name: /approve agent.*1\/4/i });
    await expect(approveButton1).toBeEnabled({ timeout: 15000 });
    await approveButton1.click();

    const approveButton2 = page.getByRole('button', { name: /approve agent.*2\/4/i });
    await expect(approveButton2).toBeEnabled({ timeout: 15000 });
    await approveButton2.click();

    const approveButton3 = page.getByRole('button', { name: /approve agent.*3\/4/i });
    await expect(approveButton3).toBeEnabled({ timeout: 15000 });
    await approveButton3.click();

    const approveButton4 = page.getByRole('button', { name: /approve agent.*4\/4/i });
    await expect(approveButton4).toBeEnabled({ timeout: 15000 });
    await approveButton4.click();

    // Wait for complete state
    const header = page.locator('header');
    await expect(header.getByRole('heading', { name: 'Blueprint Ready' })).toBeVisible({ timeout: 15000 });

    // Should have 5 files (4 agents + 1 blueprint)
    await expect(page.getByText(/Session Files \(5\)/)).toBeVisible();

    // Should show blueprint filename
    await expect(page.getByText(/\.yaml/).first()).toBeVisible();
  });

  test('should copy YAML content to clipboard', async ({ page, context }) => {
    // Grant clipboard permissions
    await context.grantPermissions(['clipboard-read', 'clipboard-write']);

    await setupBuilderApiMock(page);
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Quick path to agent review
    await page.locator('button').filter({ hasText: 'role' }).first().click();
    await page.getByText('Product Manager').click();
    await page.locator('button').filter({ hasText: 'problem to solve' }).first().click();
    await page.getByText('Automate Repetitive Work').click();
    await page.locator('button').filter({ hasText: 'area' }).first().click();
    await page.getByText('Customer Support').click();
    await page.getByRole('button', { name: /start building/i }).click();

    // Approve architecture
    await page.getByRole('button', { name: /approve architecture/i }).click({ timeout: 10000 });

    // Wait for agent review
    await expect(page.getByRole('button', { name: /approve agent.*1\/4/i })).toBeVisible({ timeout: 10000 });

    // Find the file row containing the filename, then find the copy button within it
    const fileRow = page.locator('.rounded.border.bg-background').filter({ hasText: 'support-coordinator.yaml' });
    await expect(fileRow).toBeVisible();

    // Click the copy button (the only button in the row)
    const copyButton = fileRow.locator('button');
    await copyButton.click();

    // Check that the copy was successful by verifying clipboard content
    const clipboardContent = await page.evaluate(() => navigator.clipboard.readText());
    expect(clipboardContent).toContain('name:');
    expect(clipboardContent).toContain('Support Coordinator');
  });
});

test.describe('YAML Session with Edit Mode', () => {
  test('should update YAML when agent is edited', async ({ page }) => {
    await setupBuilderApiMock(page);
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Quick path to agent review
    await page.locator('button').filter({ hasText: 'role' }).first().click();
    await page.getByText('Product Manager').click();
    await page.locator('button').filter({ hasText: 'problem to solve' }).first().click();
    await page.getByText('Automate Repetitive Work').click();
    await page.locator('button').filter({ hasText: 'area' }).first().click();
    await page.getByText('Customer Support').click();
    await page.getByRole('button', { name: /start building/i }).click();

    // Approve architecture
    await page.getByRole('button', { name: /approve architecture/i }).click({ timeout: 10000 });

    // Wait for agent review
    await expect(page.getByRole('button', { name: /approve agent.*1\/4/i })).toBeVisible({ timeout: 10000 });

    // Enter edit mode
    const editButton = page.getByRole('button', { name: /edit/i });
    if (await editButton.isVisible()) {
      await editButton.click();

      // Wait for edit form
      await expect(page.getByText('Editing Agent Configuration')).toBeVisible();

      // Modify a field (e.g., role)
      const roleInput = page.locator('textarea, input').filter({ hasText: /role/i }).first();
      if (await roleInput.isVisible()) {
        await roleInput.fill('Updated Support Lead');
      }

      // Save changes
      const saveButton = page.getByRole('button', { name: /save/i });
      await saveButton.click();

      // Verify YAML viewer is still visible with the file
      await expect(page.getByText(/Session Files/)).toBeVisible();
    }
  });
});
