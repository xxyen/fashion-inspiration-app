import { defineConfig, devices } from "@playwright/test";
import { fileURLToPath } from "node:url";
import path from "node:path";

const configDir = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(configDir, "../..");
const runId = Date.now();
const databasePath = `/tmp/fashion-e2e-${runId}.db`;
const uploadDir = `/tmp/fashion-e2e-uploads-${runId}`;
const apiBaseUrl = "http://127.0.0.1:8010";
const appBaseUrl = "http://127.0.0.1:5174";

export default defineConfig({
  testDir: "e2e",
  timeout: 60_000,
  expect: {
    timeout: 10_000
  },
  webServer: [
    {
      command: `DATABASE_PATH=${databasePath} UPLOAD_DIR=${uploadDir} OPENAI_API_KEY= ./.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8010`,
      cwd: path.join(rootDir, "app/backend"),
      url: `${apiBaseUrl}/api/health`,
      reuseExistingServer: false
    },
    {
      command: `VITE_API_BASE_URL=${apiBaseUrl} npm run dev -- --host 127.0.0.1 --port 5174`,
      cwd: path.join(rootDir, "app/frontend"),
      url: appBaseUrl,
      reuseExistingServer: false
    }
  ],
  use: {
    baseURL: appBaseUrl,
    trace: "on-first-retry"
  },
  projects: [
    {
      name: "chrome",
      use: { ...devices["Desktop Chrome"], channel: "chrome" }
    }
  ]
});
