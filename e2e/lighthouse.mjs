// Lighthouse (accessibility, best-practices, SEO) on each use case's key screen, logged in.
// Chromium is launched by Playwright with a debugging port; Lighthouse attaches to the SAME browser,
// so the session created by the Playwright login is reused.   Usage: npm run lighthouse   (LABEL=before|after)
import { chromium } from '@playwright/test';
import lighthouse from 'lighthouse';
import { mkdirSync, writeFileSync } from 'node:fs';

const UI = process.env.UI_URL ?? 'http://localhost:5173';
const API = process.env.API_URL ?? 'http://localhost:5001/api';
const LABEL = process.env.LABEL ?? 'before';
const OUT = '../docs/team/evidence/lighthouse';
mkdirSync(OUT, { recursive: true });

const stamp = Date.now();
const email = `lh.${stamp}@example.com`;
const reg = await fetch(`${API}/auth/register`, {
  method: 'POST', headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ name: `LH ${stamp}`, email, password: 'password123' }),
});
if (!reg.ok) throw new Error('could not register Lighthouse user');

const browser = await chromium.launch({ args: ['--remote-debugging-port=9222'] });
const page = await browser.newPage();
await page.goto(`${UI}/login`);
await page.getByLabel('Work email').fill(email);
await page.getByLabel('Password', { exact: true }).fill('password123');
await page.getByRole('button', { name: 'Sign in' }).click();
await page.waitForURL(/\/$/);

const screens = { login_after_signin_dashboard: '/', my_leave_uc1_uc3: '/leave' };
for (const [name, path] of Object.entries(screens)) {
  const result = await lighthouse(`${UI}${path}`, {
    port: 9222, output: 'json', onlyCategories: ['accessibility', 'best-practices', 'seo'], disableStorageReset: true,
  });
  writeFileSync(`${OUT}/lighthouse_${LABEL}_${name}.json`, result.report);
  const c = result.lhr.categories;
  console.log(name, Object.fromEntries(Object.entries(c).map(([k, v]) => [k, Math.round(v.score * 100)])));
}
await browser.close();
