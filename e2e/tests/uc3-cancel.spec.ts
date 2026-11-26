/**
 * UC-3  Cancel leave (Workflow B, employee)
 * Actor: employee (owner).  Pre: a pending/approved request starting after today.
 * Main flow  : My leave -> View -> Cancel request -> confirm -> status cancelled.
 * Alternative: A1 cancel an APPROVED request (days returned to balance) | A2 choose "Keep it" (nothing changes)
 * Exception  : E1 rejected request has no Cancel action | E2 leave that already started cannot be cancelled
 */
import { expect, test } from '@playwright/test';
import { ADMIN, apiApply, apiReview, casualUsedDays, day, listRequests, registerEmployee, tokenFor, uiLogin } from './helpers';

async function openDetail(page) {
  await page.goto('/leave');
  await page.getByRole('button', { name: 'View' }).first().click();
  const dialog = page.getByRole('dialog');
  await expect(dialog).toBeVisible();
  return dialog;
}

test.describe('UC-3 Cancel leave', () => {
  test('UC3-MAIN cancel a pending request', async ({ page, request }) => {
    const u = await registerEmployee(request, 'uc3main');
    await apiApply(request, u.token, day(0), day(1));
    await uiLogin(page, u.email, u.password);
    const dialog = await openDetail(page);
    await dialog.getByRole('button', { name: 'Cancel request' }).click();
    await page.getByRole('button', { name: 'Yes, cancel request' }).click();
    await expect(page.getByText('Request withdrawn. You can apply again any time.')).toBeVisible();
    expect((await listRequests(request, u.token)).items[0].status).toBe('cancelled');
  });

  test('UC3-A1 cancelling an approved request returns the days', async ({ page, request }) => {
    const u = await registerEmployee(request, 'uc3a1');
    const created = await apiApply(request, u.token, day(0), day(2));
    const admin = await tokenFor(request, ADMIN.email, ADMIN.password);
    expect((await apiReview(request, admin, created.id, 'approve')).status()).toBe(200);
    expect(await casualUsedDays(request, u.token)).toBe(3);
    await uiLogin(page, u.email, u.password);
    const dialog = await openDetail(page);
    await dialog.getByRole('button', { name: 'Cancel request' }).click();
    await page.getByRole('button', { name: 'Yes, cancel request' }).click();
    await expect(page.getByText('Request cancelled. Those days are back in your balance.')).toBeVisible();
    expect(await casualUsedDays(request, u.token)).toBe(0);                   // shared record restored
  });

  test('UC3-A2 "Keep it" leaves the request pending', async ({ page, request }) => {
    const u = await registerEmployee(request, 'uc3a2');
    await apiApply(request, u.token, day(0), day(0));
    await uiLogin(page, u.email, u.password);
    const dialog = await openDetail(page);
    await dialog.getByRole('button', { name: 'Cancel request' }).click();
    await page.getByRole('button', { name: 'Keep it' }).click();
    expect((await listRequests(request, u.token)).items[0].status).toBe('pending');
  });

  test('UC3-E1 a rejected request cannot be cancelled', async ({ page, request }) => {
    const u = await registerEmployee(request, 'uc3e1');
    const created = await apiApply(request, u.token, day(0), day(0));
    const admin = await tokenFor(request, ADMIN.email, ADMIN.password);
    await apiReview(request, admin, created.id, 'reject', 'No cover available');
    await uiLogin(page, u.email, u.password);
    const dialog = await openDetail(page);
    await expect(dialog.getByRole('button', { name: 'Cancel request' })).toHaveCount(0);
    expect((await listRequests(request, u.token)).items[0].status).toBe('rejected');
  });

  test('UC3-E2 leave starting today cannot be cancelled', async ({ page, request }) => {
    const today = new Date().toISOString().slice(0, 10);
    const dow = new Date().getUTCDay();
    test.skip(dow === 0 || dow === 6, 'today is a weekend: a request starting today has no working days');
    const u = await registerEmployee(request, 'uc3e2');
    const created = await apiApply(request, u.token, today, today);
    const admin = await tokenFor(request, ADMIN.email, ADMIN.password);
    expect((await apiReview(request, admin, created.id, 'approve')).status()).toBe(200);
    await uiLogin(page, u.email, u.password);
    const dialog = await openDetail(page);
    await expect(dialog.getByRole('button', { name: 'Cancel request' })).toHaveCount(0);
    expect((await listRequests(request, u.token)).items[0].status).toBe('approved');
  });
});
