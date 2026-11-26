/**
 * UC-4  Sign in and role-based access (supports both workflows)
 * Main flow  : employee signs in -> lands on the dashboard.
 * Alternative: A1 submit the form with the Enter key | A2 reveal the password with the toggle
 * Exception  : E1 wrong password -> clear message | E2 employee opens /approvals -> sent back (no admin screen)
 *              E3 signed-out visitor opens /leave -> redirected to sign in
 */
import { expect, test } from '@playwright/test';
import { ADMIN, registerEmployee, uiLogin } from './helpers';

test.describe('UC-4 Sign in and access', () => {
  test('UC4-MAIN employee signs in', async ({ page, request }) => {
    const u = await registerEmployee(request, 'uc4main');
    await uiLogin(page, u.email, u.password);
    await expect(page).toHaveURL(/\/$/);
    await expect(page.getByRole('link', { name: /my leave/i }).first()).toBeVisible();
  });

  test('UC4-A1 sign in with the Enter key', async ({ page, request }) => {
    const u = await registerEmployee(request, 'uc4a1');
    await page.goto('/login');
    await page.getByLabel('Work email').fill(u.email);
    await page.getByLabel('Password', { exact: true }).fill(u.password);
    await page.keyboard.press('Enter');
    await expect(page).toHaveURL(/\/$/);
  });

  test('UC4-A2 password visibility toggle', async ({ page }) => {
    await page.goto('/login');
    const field = page.getByLabel('Password', { exact: true });
    await expect(field).toHaveAttribute('type', 'password');
    await page.getByRole('button', { name: 'Show password' }).click();
    await expect(field).toHaveAttribute('type', 'text');
  });

  test('UC4-E1 wrong password explains the problem', async ({ page, request }) => {
    const u = await registerEmployee(request, 'uc4e1');
    await uiLogin(page, u.email, 'wrong-password');
    await expect(page.getByText('Incorrect email or password.')).toBeVisible();
    await expect(page).toHaveURL(/\/login/);
  });

  test('UC4-E2 employee cannot open the admin approvals screen', async ({ page, request }) => {
    const u = await registerEmployee(request, 'uc4e2');
    await uiLogin(page, u.email, u.password);
    await page.goto('/approvals');
    await expect(page).not.toHaveURL(/approvals/);
    await expect(page.getByRole('heading', { name: 'Leave approvals' })).toHaveCount(0);
  });

  test('UC4-E3 signed-out visitor is redirected to sign in', async ({ page }) => {
    await page.goto('/leave');
    await expect(page).toHaveURL(/\/login/);
  });

  test('UC4-ADMIN admin reaches the approvals screen', async ({ page }) => {
    await uiLogin(page, ADMIN.email, ADMIN.password);
    await page.goto('/approvals');
    await expect(page.getByRole('heading', { name: 'Leave approvals' })).toBeVisible();
  });
});
