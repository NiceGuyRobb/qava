export default {
  testDir: './frontend/e2e/tests',
  webServer: [
    {
      command: 'uv run --project backend uvicorn qava.main:app --host 127.0.0.1 --port 8000',
      url: 'http://127.0.0.1:8000/openapi.json',
      reuseExistingServer: true,
      timeout: 30_000,
    },
    {
      command: 'npm --prefix frontend run dev -- --host 127.0.0.1 --port 5173',
      url: 'http://127.0.0.1:5173',
      reuseExistingServer: true,
      timeout: 30_000,
    },
  ],
  use: {
    baseURL: 'http://127.0.0.1:5173',
    trace: 'retain-on-failure',
  },
  projects: [
    {
      name: 'desktop-chromium',
      use: { browserName: 'chromium', viewport: { width: 1440, height: 900 } },
    },
    {
      name: 'mobile-chromium',
      use: { browserName: 'chromium', viewport: { width: 390, height: 844 } },
    },
    {
      name: 'reduced-motion',
      use: {
        browserName: 'chromium',
        reducedMotion: 'reduce',
        viewport: { width: 1440, height: 900 },
      },
    },
  ],
}