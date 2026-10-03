import { defineConfig } from "@playwright/test";
import path from "node:path";

const python = process.env.E2E_PYTHON || path.resolve("../backend/.venv/Scripts/python.exe");
// Opt in against an already running production API/UI with real model weights.
const realModels = process.env.E2E_REAL_NLP === "1";
export default defineConfig({
  testDir: "./tests/e2e", workers: 1, timeout: 120000,
  use: { baseURL: realModels ? "http://localhost:3000" : "http://localhost:3001", channel: "chrome", trace: "retain-on-failure", screenshot: "only-on-failure" },
  webServer: realModels ? undefined : [
    { command: `"${python}" -m tests.e2e_server`, cwd: "../backend", url: "http://127.0.0.1:8001/api/v1/health", timeout: 120000, reuseExistingServer: false,
      env: { DATABASE_URL: "sqlite:///../.verification/e2e.db", UPLOAD_DIR: "../.verification/e2e-uploads", CORS_ORIGINS: '["http://localhost:3001"]' } },
    { command: "npm run dev -- --port 3001", url: "http://localhost:3001", timeout: 120000, reuseExistingServer: false,
      env: { NEXT_PUBLIC_API_URL: "http://127.0.0.1:8001/api/v1", NEXT_DIST_DIR: ".next-e2e" } },
  ],
});
