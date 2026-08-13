import { defineConfig, devices } from "@playwright/test";

// 시험 표준(test-runner 스킬): frontend e2e = Playwright. `pnpm run test:e2e` — 개발 서버 자동 기동.
export default defineConfig({
  testDir: "./test/e2e",
  fullyParallel: true,
  reporter: "list",
  use: {
    baseURL: `http://127.0.0.1:${process.env.FRONT_PORT || 3000}`,
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: "pnpm dev",
    url: `http://127.0.0.1:${process.env.FRONT_PORT || 3000}`,
    reuseExistingServer: !process.env.CI,
    timeout: 30_000,
  },
});
