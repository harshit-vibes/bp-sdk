import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for Blueprint Builder UI E2E tests
 *
 * Run with:
 *   npm run test:e2e              # Run unit/mock tests
 *   npm run test:e2e:integration  # Run real API integration tests
 *   npm run test:e2e:ui           # Run with UI mode
 *   npm run test:e2e:debug        # Debug mode
 */
export default defineConfig({
  testDir: './e2e',

  /* Run tests in parallel */
  fullyParallel: true,

  /* Fail the build on CI if you accidentally left test.only in the source code */
  forbidOnly: !!process.env.CI,

  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,

  /* Opt out of parallel tests on CI */
  workers: process.env.CI ? 1 : undefined,

  /* Reporter to use */
  reporter: [
    ['html', { open: 'never' }],
    ['list'],
  ],

  /* Shared settings for all projects */
  use: {
    /* Base URL for all tests */
    baseURL: process.env.TEST_BASE_URL || 'http://localhost:3000',

    /* Collect trace when retrying the failed test */
    trace: 'on-first-retry',

    /* Screenshot on failure */
    screenshot: 'only-on-failure',

    /* Video recording */
    video: 'retain-on-failure',
  },

  /* Configure projects for different browsers */
  projects: [
    // Primary browser tests
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
      testIgnore: ['**/integration/**'],
    },

    // Mobile viewport test (using Chromium)
    {
      name: 'mobile',
      use: { ...devices['Pixel 5'] },
      testIgnore: ['**/integration/**'],
    },

    // Integration tests with real API (slow, for manual runs)
    {
      name: 'integration',
      use: {
        ...devices['Desktop Chrome'],
      },
      testMatch: '**/integration/**/*.spec.ts',
      timeout: 180000, // 3 minutes per test
    },
  ],

  /* Run your local dev server before starting the tests */
  webServer: process.env.TEST_BASE_URL ? undefined : {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
});
