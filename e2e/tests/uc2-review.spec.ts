/**
 * UC-2  Review leave request (Workflow B, admin)
 * Actor: admin.  Pre: a pending request exists.  Post (main): status approved, employee used_days increased.
 * Main flow  : open approvals -> Review -> Approve -> request approved, balance consumed.
 * Alternative: A1 reject with a note (balance unchanged) | A2 approved request appears under the Approved tab
 * Exception  : E1 reject without a note (error, still pending) | E2 approval fails when balance no longer covers it
 */
import { expect, test } from '@playwright/test';
import { ADMIN, apiApply, casualUsedDays, day, listRequests, registerEmployee, uiLogin } from './helpers';

async function openReview(page, name: string) {
  await page.goto('/approvals?status=pending');
  const row = page.getByRole('row', { name: new RegExp(name) });
  await expect(row).toBeVisible();
  await row.getByRole('button', { name: 'Review' }).click();
  const dialog = page.getByRole('dialog');
  await expect(dialog).toBeVisible();
  return dialog;
}

test.describe('UC-2 Review leave', () => {
  test('UC2-MAIN approve pending request consumes balance', async ({ page, request }) => {
    const u = await registerEmployee(request, 'uc2main');
    await apiApply(request, u.token, day(0), day(2));                         // 3 days
    await uiLogin(page, ADMIN.email, ADMIN.password);
    const dialog = await openReview(page, u.name);
    await dialog.getByRole('button', { name: 'Approve' }).click();
    await expect(dialog).toBeHidden();
    expect((await listRequests(request, u.token)).items[0].status).toBe('approved');
    expect(await casualUsedDays(request, u.token)).toBe(3);                   // shared record changed
  });

  test('UC2-A1 reject with a note leaves balance unchanged', async ({ page, request }) => {
    const u = await registerEmployee(request, 'uc2a1');
    await apiApply(request, u.token, day(0), day(2));
    await uiLogin(page, ADMIN.email, ADMIN.password);
    const dialog = await openReview(page, u.name);
    await dialog.getByLabel('Decision note').fill('Team is short staffed that week');
    await dialog.getByRole('button', { name: 'Reject' }).click();
    await expect(dialog).toBeHidden();
    const item = (await listRequests(request, u.token)).items[0];
    expect(item.status).toBe('rejected');
    expect(item.review_note).toBe('Team is short staffed that week');
    expect(await casualUsedDays(request, u.token)).toBe(0);
  });

  test('UC2-A2 approved request is listed under the Approved tab', async ({ page, request }) => {
    const u = await registerEmployee(request, 'uc2a2');
    await apiApply(request, u.token, day(0), day(0));
    await uiLogin(page, ADMIN.email, ADMIN.password);
    const dialog = await openReview(page, u.name);
    await dialog.getByRole('button', { name: 'Approve' }).click();
    await expect(dialog).toBeHidden();
    await page.goto('/approvals?status=approved');
    await expect(page.getByRole('row', { name: new RegExp(u.name) })).toBeVisible();
  });

  test('UC2-E1 reject without a note shows what to correct', async ({ page, request }) => {
    const u = await registerEmployee(request, 'uc2e1');
    await apiApply(request, u.token, day(0), day(0));
    await uiLogin(page, ADMIN.email, ADMIN.password);
    const dialog = await openReview(page, u.name);
    await dialog.getByRole('button', { name: 'Reject' }).click();
    await expect(dialog.getByText('Add a short note before rejecting this request.')).toBeVisible();
    expect((await listRequests(request, u.token)).items[0].status).toBe('pending');
    await dialog.getByLabel('Decision note').fill('Not possible this week');   // correct and succeed
    await dialog.getByRole('button', { name: 'Reject' }).click();
    await expect(dialog).toBeHidden();
    expect((await listRequests(request, u.token)).items[0].status).toBe('rejected');
  });

  test('UC2-E2 second approval fails when balance is exhausted', async ({ page, request }) => {
    const u = await registerEmployee(request, 'uc2e2');
    await apiApply(request, u.token, day(0), day(8));          // Mon..Tue next week = 7 days
    await apiApply(request, u.token, day(14), day(22));        // Mon..Tue two weeks later = 7 days (total 14 > 12)
    await uiLogin(page, ADMIN.email, ADMIN.password);
    await page.goto('/approvals?status=pending');
    const rows = page.getByRole('row', { name: new RegExp(u.name) });
    await rows.last().getByRole('button', { name: 'Review' }).click();          // oldest first approved
    await page.getByRole('dialog').getByRole('button', { name: 'Approve' }).click();
    await expect(page.getByRole('dialog')).toBeHidden();

    await page.goto('/approvals?status=pending');
    await page.getByRole('row', { name: new RegExp(u.name) }).getByRole('button', { name: 'Review' }).click();
    const dialog = page.getByRole('dialog');
    await dialog.getByRole('button', { name: 'Approve' }).click();
    await expect(dialog.getByText(/exceeds the available balance|Only 5 day/)).toBeVisible();
    const items = (await listRequests(request, u.token)).items;
    expect(items.filter((i: any) => i.status === 'approved')).toHaveLength(1);
    expect(items.filter((i: any) => i.status === 'pending')).toHaveLength(1);
    expect(await casualUsedDays(request, u.token)).toBe(7);                      // not double counted
  });
});
