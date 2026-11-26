import { APIRequestContext, Page, expect } from '@playwright/test';

export const API = process.env.API_URL ?? 'http://localhost:5001/api';
export const ADMIN = { email: 'admin@leavedesk.in', password: 'admin1234' };

const iso = (d: Date) => d.toISOString().slice(0, 10);
export const addDays = (d: Date, n: number) => new Date(d.getTime() + n * 86_400_000);

/** First Monday of January next year: always in the future and never crosses a year boundary. */
export function janMonday(): Date {
  const d = new Date(Date.UTC(new Date().getUTCFullYear() + 1, 0, 1));
  while (d.getUTCDay() !== 1) d.setUTCDate(d.getUTCDate() + 1);
  return d;
}
export const day = (offset: number) => iso(addDays(janMonday(), offset));   // 0 = Monday

export interface Person { name: string; email: string; password: string; id: number; token: string }

let counter = 0;
/** Fresh employee per test -> isolated balance and requests, no dependence on seeded data. */
export async function registerEmployee(request: APIRequestContext, label: string): Promise<Person> {
  counter += 1;
  const stamp = `${Date.now()}${counter}`;
  const name = `E2E ${label} ${stamp}`;
  const email = `e2e.${label}.${stamp}@example.com`;
  const res = await request.post(`${API}/auth/register`, {
    data: { name, email, password: 'password123', department: 'QA Automation' },
  });
  expect(res.status(), 'register').toBe(201);
  const body = await res.json();
  return { name, email, password: 'password123', id: body.user.id, token: body.access_token };
}

export async function tokenFor(request: APIRequestContext, email: string, password: string): Promise<string> {
  const res = await request.post(`${API}/auth/login`, { data: { email, password } });
  expect(res.status(), 'login').toBe(200);
  return (await res.json()).access_token;
}

const auth = (token: string) => ({ Authorization: `Bearer ${token}` });

export async function apiApply(request: APIRequestContext, token: string, start: string, end: string, leaveTypeId = 1) {
  const res = await request.post(`${API}/leave-requests`, {
    headers: auth(token),
    data: { leave_type_id: leaveTypeId, start_date: start, end_date: end, reason: 'Automated E2E leave request' },
  });
  expect(res.status(), 'apply via API').toBe(201);
  return res.json();
}

export async function apiReview(request: APIRequestContext, adminToken: string, id: number, decision: 'approve' | 'reject', note?: string) {
  return request.post(`${API}/leave-requests/${id}/review`, { headers: auth(adminToken), data: { decision, note } });
}

export async function listRequests(request: APIRequestContext, token: string) {
  const res = await request.get(`${API}/leave-requests?per_page=50`, { headers: auth(token) });
  return res.json();
}

export async function casualUsedDays(request: APIRequestContext, token: string, year?: number) {
  const y = year ?? janMonday().getUTCFullYear();
  const res = await request.get(`${API}/leave-balances?year=${y}`, { headers: auth(token) });
  const body = await res.json();
  return body.balances.find((b: any) => b.leave_type.code === 'CASUAL').used_days as number;
}

export async function uiLogin(page: Page, email: string, password: string) {
  await page.goto('/login');
  await page.getByLabel('Work email').fill(email);
  await page.getByLabel('Password', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Sign in' }).click();
}

export async function openApplyDialog(page: Page) {
  await page.goto('/leave');
  await page.getByRole('button', { name: 'Request time off' }).first().click();
  const dialog = page.getByRole('dialog');
  await expect(dialog).toBeVisible();
  return dialog;
}

export async function fillApply(dialog: ReturnType<Page['getByRole']>, start: string, end: string, reason: string) {
  await dialog.getByLabel('Start date').fill(start);
  await dialog.getByLabel('End date').fill(end);
  await dialog.getByLabel('Reason').fill(reason);
}
