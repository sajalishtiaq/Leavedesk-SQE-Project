/**
 * Usability + accessibility automation.
 *  1) Keyboard navigation through the Apply-leave form (focus order + keyboard submit)
 *  2) Full axe-core scans of each use case's key screen -> docs/team/evidence/a11y/axe_<label>_<screen>.json
 * Run before/after a fix:  npm run a11y:before   /   npm run a11y:after
 */
import AxeBuilder from '@axe-core/playwright';
import { expect, test, Page } from '@playwright/test';
import { mkdirSync, writeFileSync } from 'node:fs';
import { ADMIN, apiApply, day, janMonday, openApplyDialog, registerEmployee, uiLogin } from './helpers';

const LABEL = process.env.A11Y_LABEL ?? 'before';
const OUT = '../docs/team/evidence/a11y';

async function tabUntilFocused(page: Page, target: ReturnType<Page['locator']>, max = 8) {
  for (let i = 0; i < max; i++) {
    if (await target.evaluate((el) => el === document.activeElement)) return i;
    await page.keyboard.press('Tab');
  }
  throw new Error('target never received focus via keyboard');
}

test('KB-1 keyboard: focus order through the apply form and keyboard submit', async ({ page, request }) => {
  const u = await registerEmployee(request, 'kb');
  await uiLogin(page, u.email, u.password);
  const dialog = await openApplyDialog(page);
  // Fill values programmatically (typing into native date segments is locale dependent) ...
  await dialog.getByLabel('Start date').fill(day(0));
  await dialog.getByLabel('End date').fill(day(0));
  await dialog.getByLabel('Reason').fill('Keyboard only submission test');

  // ... then prove the required fields and the submit button are reachable, in order, by keyboard.
  const order = [
    dialog.getByLabel('Leave type'), dialog.getByLabel('Start date'), dialog.getByLabel('End date'),
    dialog.getByLabel('Reason'), dialog.getByRole('button', { name: 'Send request' }),
  ];
  await order[0].focus();
  const reached: string[] = [];
  for (const [i, loc] of order.entries()) {
    if (i > 0) await tabUntilFocused(page, loc);
    reached.push(await loc.evaluate((el) => (el.getAttribute('aria-label') || el.closest('label')?.textContent || el.textContent || el.tagName).trim().slice(0, 20)));
  }
  expect(reached.length).toBe(5);                                    // all five stops reached in order
  await page.keyboard.press('Enter');                                // submit with the keyboard
  await expect(page.getByText('Request sent. Your manager will review it shortly.')).toBeVisible();
});

async function scan(page: Page, name: string) {
  const results = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'best-practice']).analyze();
  mkdirSync(OUT, { recursive: true });
  writeFileSync(`${OUT}/axe_${LABEL}_${name}.json`, JSON.stringify({ url: page.url(), violations: results.violations }, null, 2));
  test.info().annotations.push({ type: 'axe', description: `${name}: ${results.violations.length} violation(s)` });
}

test('AX-1 axe scan: login screen', async ({ page }) => {
  await page.goto('/login');
  await expect(page.getByRole('button', { name: 'Sign in' })).toBeVisible();
  await scan(page, 'login');
});

test('AX-2 axe scan: apply-leave screen (UC-1) with the form open', async ({ page, request }) => {
  const u = await registerEmployee(request, 'ax2');
  await uiLogin(page, u.email, u.password);
  await openApplyDialog(page);
  await scan(page, 'apply_leave');
});

test('AX-3 axe scan: my leave list and cancel (UC-3)', async ({ page, request }) => {
  const u = await registerEmployee(request, 'ax3');
  await apiApply(request, u.token, day(0), day(0));
  await uiLogin(page, u.email, u.password);
  await page.goto('/leave');
  await expect(page.getByRole('button', { name: 'View' }).first()).toBeVisible();
  await scan(page, 'my_leave');
});

test('AX-4 axe scan: approvals screen (UC-2)', async ({ page, request }) => {
  const u = await registerEmployee(request, 'ax4');
  await apiApply(request, u.token, day(0), day(0));
  await uiLogin(page, ADMIN.email, ADMIN.password);
  await page.goto('/approvals?status=pending');
  await expect(page.getByRole('heading', { name: 'Leave approvals' })).toBeVisible();
  await scan(page, 'approvals');
});
