import { defineConfig, devices } from '@playwright/test';

const proxy = process.env.PW_PROXY ? { server: process.env.PW_PROXY, bypass: '<-loopback>' } : undefined;   // ZAP passive scan (bypass '<-loopback>' so localhost traffic is proxied too)

export default defineConfig({
  testDir: './tests',
  workers: 1,                       // one shared SQLite DB -> run serially
  fullyParallel: false,
  retries: 0,
  timeout: 30_000,
  reporter: [['list'], ['html', { outputFolder: '../docs/team/evidence/playwright-report', open: 'never' }],
             ['json', { outputFile: '../docs/team/evidence/playwright-results.json' }]],
  use: {
    baseURL: process.env.UI_URL ?? 'http://localhost:5173',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    proxy,
    ignoreHTTPSErrors: !!proxy,
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: [
    {
      command: 'bash -c "cd ../backend && . .venv/bin/activate && flask --app run:app run -p 5001 --no-debugger --no-reload"',
      url: 'http://localhost:5001/api/health',
      reuseExistingServer: true,
      timeout: 60_000,
    },
    {
      command: 'bash -c "cd ../frontend && npm run dev -- --port 5173 --host 127.0.0.1"',
      url: 'http://localhost:5173',
      reuseExistingServer: true,
      timeout: 60_000,
    },
  ],
});
