/**
 * Defensive security: automated access-decision checks (role x action) through the real API + UI.
 * Each check records role, action, expected, observed, evidence -> docs/team/evidence/access_matrix_results.json
 */
import { expect, test } from '@playwright/test';
import { writeFileSync, mkdirSync } from 'node:fs';
import { ADMIN, API, apiApply, day, registerEmployee, tokenFor, uiLogin } from './helpers';

const rows: any[] = [];
const bearer = (t: string) => ({ Authorization: `Bearer ${t}` });

function record(role: string, action: string, expected: string, observed: string, evidence: string) {
  rows.push({ role, action, expected, observed, evidence, result: expected === observed ? 'PASS' : 'FAIL' });
  expect(observed, `${role}: ${action}`).toBe(expected);
}

test.afterAll(() => {
  mkdirSync('../docs/team/evidence', { recursive: true });
  writeFileSync('../docs/team/evidence/access_matrix_results.json', JSON.stringify(rows, null, 2));
});

test('ACC access decisions across roles', async ({ request, page }) => {
  const alice = await registerEmployee(request, 'accA');
  const bob = await registerEmployee(request, 'accB');
  const admin = await tokenFor(request, ADMIN.email, ADMIN.password);
  const aliceReq = await apiApply(request, alice.token, day(0), day(0));
  const url = `${API}/leave-requests/${aliceReq.id}`;

  let r = await request.post(`${url}/review`, { headers: bearer(bob.token), data: { decision: 'approve' } });
  record('employee (other)', 'review someone else\'s request', '403', String(r.status()), `POST ${url}/review`);

  r = await request.post(`${url}/review`, { headers: bearer(alice.token), data: { decision: 'approve' } });
  record('employee (owner)', 'approve own request', '403', String(r.status()), `POST ${url}/review`);

  r = await request.get(url, { headers: bearer(bob.token) });
  record('employee (other)', 'view someone else\'s request', '404', String(r.status()), `GET ${url}`);

  r = await request.get(`${API}/leave-balances?user_id=${alice.id}`, { headers: bearer(bob.token) });
  record('employee (other)', 'read someone else\'s balances', '403', String(r.status()), 'GET /leave-balances?user_id=');

  r = await request.get(`${API}/leave-requests`);
  record('anonymous', 'list requests without token', '401', String(r.status()), 'GET /leave-requests (no Authorization)');

  r = await request.post(`${url}/cancel`, { headers: bearer(admin) });
  record('admin', 'cancel an employee\'s request', '403', String(r.status()), `POST ${url}/cancel`);

  r = await request.get(url, { headers: bearer(alice.token) });
  record('employee (owner)', 'view own request', '200', String(r.status()), `GET ${url}`);

  r = await request.post(`${url}/review`, { headers: bearer(admin), data: { decision: 'approve' } });
  record('admin', 'approve employee request', '200', String(r.status()), `POST ${url}/review`);

  await uiLogin(page, alice.email, alice.password);
  await page.goto('/approvals');
  record('employee (UI)', 'open admin approvals screen', 'redirected', /approvals/.test(page.url()) ? 'shown' : 'redirected', page.url());
});
