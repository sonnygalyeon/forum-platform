
import { defineConfig, devices } from "@playwright/test";

const baseURL =
  process.env.PLAYWRIGHT_BASE_URL ??
  "http://127.0.0.1:3000";

const manageLocalWebServer =
  !process.env.CI &&
  process.env.PLAYWRIGHT_MANAGE_WEBSERVER !== "0";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 2 : 1,
  reporter: process.env.CI
    ? [
        ["html", { open: "never" }],
        ["github"],
      ]
    : "list",
  use: {
    baseURL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  webServer: manageLocalWebServer
    ? {
        command: "sh ../scripts/e2e_webserver.sh",
        url: baseURL,
        reuseExistingServer: true,
        timeout: 180_000,
      }
    : undefined,
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "mobile-chromium",
      use: { ...devices["Pixel 7"] },
    },
  ],
  outputDir: "test-results/playwright",
});
