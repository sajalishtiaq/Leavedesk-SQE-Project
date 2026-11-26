/**
 * UC-1  Apply for leave (Workflow A)
 * Actor: employee.  Pre: logged in, balance 12 casual days.  Post (main): request stored as pending, balance NOT consumed.
 * Main flow  : open form -> fill type/dates/reason -> send -> confirmation shown -> request listed as pending.
 * Alternative: A1 different leave type (Sick)  | A2 range spanning a weekend (only Mon-Fri counted)
 * Exception  : E1 reason too short (client message, then corrected)  | E2 exceeds balance (server message, then corrected)
 *              E3 overlaps an existing request (server message)
 */
import { expect, test } from '@playwright/test';
import { casualUsedDays, apiApply, day, fillApply, listRequests, openApplyDialog, registerEmployee, uiLogin } from './helpers';

const SENT = 'Request sent. Your manager will review it shortly.';

test.describe('UC-1 Apply for leave', () => {
  test('UC1-MAIN valid single-day request is created as pending', async ({ page, request }) => {
    const u = await registerEmployee(request, 'uc1main');
    await uiLogin(page, u.email, u.password);
    const dialog = await openApplyDialog(page);
    await fillApply(dialog, day(0), day(0), 'Family wedding in Lahore');
    await dialog.getByRole('button', { name: 'Send request' }).click();

    await expect(page.getByText(SENT)).toBeVisible();                 // confirmation
    await expect(dialog).toBeHidden();
    const list = await listRequests(request, u.token);                // postconditions
    expect(list.total).toBe(1);
    expect(list.items[0]).toMatchObject({ status: 'pending', days: 1, start_date: day(0) });
    expect(await casualUsedDays(request, u.token)).toBe(0);           // apply never consumes balance
  });

  test('UC1-A1 sick leave type', async ({ page, request }) => {
    const u = await registerEmployee(request, 'uc1a1');
    await uiLogin(page, u.email, u.password);
    const dialog = await openApplyDialog(page);
    await dialog.getByLabel('Leave type').selectOption({ index: 1 });
    await fillApply(dialog, day(1), day(1), 'Doctor appointment follow-up');
    await dialog.getByRole('button', { name: 'Send request' }).click();
    await expect(page.getByText(SENT)).toBeVisible();
    const list = await listRequests(request, u.token);
    expect(list.items[0].leave_type.code).toBe('SICK');
  });

  test('UC1-A2 range spanning a weekend counts only working days', async ({ page, request }) => {
    const u = await registerEmployee(request, 'uc1a2');
    await uiLogin(page, u.email, u.password);
    const dialog = await openApplyDialog(page);
    await fillApply(dialog, day(4), day(7), 'Long weekend trip to the north');     // Fri .. Mon
    await dialog.getByRole('button', { name: 'Send request' }).click();
    await expect(page.getByText(SENT)).toBeVisible();
    expect((await listRequests(request, u.token)).items[0].days).toBe(2);
  });

  test('UC1-E1 reason too short is rejected, then corrected', async ({ page, request }) => {
    const u = await registerEmployee(request, 'uc1e1');
    await uiLogin(page, u.email, u.password);
    const dialog = await openApplyDialog(page);
    await fillApply(dialog, day(0), day(0), 'short');
    await dialog.getByRole('button', { name: 'Send request' }).click();
    await expect(dialog.getByText('Add a little more detail (at least 10 characters).')).toBeVisible();
    expect((await listRequests(request, u.token)).total).toBe(0);               // nothing saved

    await dialog.getByLabel('Reason').fill('Family wedding in Lahore');         // correct the value
    await dialog.getByRole('button', { name: 'Send request' }).click();
    await expect(page.getByText(SENT)).toBeVisible();
    expect((await listRequests(request, u.token)).total).toBe(1);
  });

  test('UC1-E2 more days than the balance: server explains, then corrected', async ({ page, request }) => {
    const u = await registerEmployee(request, 'uc1e2');
    await uiLogin(page, u.email, u.password);
    const dialog = await openApplyDialog(page);
    await fillApply(dialog, day(0), day(16), 'Extended family visit abroad');   // Mon .. Wed of week 3 = 13 days > 12
    await dialog.getByRole('button', { name: 'Send request' }).click();
    await expect(dialog.getByText(/Only 12 day\(s\) of Casual Leave remain/)).toBeVisible();
    expect((await listRequests(request, u.token)).total).toBe(0);

    await dialog.getByLabel('End date').fill(day(15));                          // Tue of week 3 = 12 days = limit
    await dialog.getByRole('button', { name: 'Send request' }).click();
    await expect(page.getByText(SENT)).toBeVisible();
    expect((await listRequests(request, u.token)).items[0].days).toBe(12);
  });

  test('UC1-E3 overlapping request is refused, no duplicate created', async ({ page, request }) => {
    const u = await registerEmployee(request, 'uc1e3');
    await apiApply(request, u.token, day(0), day(2));
    await uiLogin(page, u.email, u.password);
    const dialog = await openApplyDialog(page);
    await fillApply(dialog, day(1), day(1), 'Second request for same dates');
    await dialog.getByRole('button', { name: 'Send request' }).click();
    await expect(dialog.getByText(/overlaps these dates/)).toBeVisible();
    expect((await listRequests(request, u.token)).total).toBe(1);
  });
});
