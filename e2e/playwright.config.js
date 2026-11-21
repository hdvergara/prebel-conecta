// @ts-check
const { defineConfig, devices } = require("@playwright/test");

// Per CONSTITUTION.md "Harness": e2e serves dist/ with a plain static server
// (python's stdlib http.server -- no Flask, no ML models needed) and never
// starts the real rrhh_api.py backend. Every test that touches MODEL_API
// intercepts it explicitly via page.route().
module.exports = defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:4173",
    trace: "retain-on-failure",
  },
  webServer: {
    command: "python -m http.server 4173 --directory ../dist",
    url: "http://127.0.0.1:4173/index.html",
    reuseExistingServer: !process.env.CI,
    timeout: 20_000,
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],
});
