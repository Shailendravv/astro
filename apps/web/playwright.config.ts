import { defineConfig } from "@playwright/test";

// E2E runs against the Docker Compose stack (docs/deployment.md section 3, PRs only).
// Start it first:  docker compose -p jyotish-dev up --build -d
export default defineConfig({
  testDir: "./e2e",
  retries: 0,
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://127.0.0.1:3000",
    trace: "retain-on-failure",
  },
});
