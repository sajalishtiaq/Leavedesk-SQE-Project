// k6 workload: Workflow A - POST /api/leave-requests (state-changing).
// Limits (decided BEFORE testing, see docs/team/05-performance-plan.md):
//   p95 response time <= 500 ms   and   unexpected failures < 1 %
// A "warmup" scenario reaches the target VUs for 10 s; the "measure" scenario then runs 60 s at the
// same VU count and only its samples (tag phase:measure) are judged.
import http from 'k6/http';
import exec from 'k6/execution';
import { check } from 'k6';
import { Rate } from 'k6/metrics';

const BASE = __ENV.BASE_URL || 'http://localhost:5001';
const VUS = parseInt(__ENV.VUS || '1', 10);
const unexpected = new Rate('unexpected_failures');

export const options = {
  scenarios: {
    warmup: { executor: 'constant-vus', vus: VUS, duration: '10s', exec: 'warmup', tags: { phase: 'warmup' } },
    measure: { executor: 'constant-vus', vus: VUS, duration: '60s', startTime: '10s', exec: 'measure', tags: { phase: 'measure' } },
  },
  thresholds: {
    'http_req_duration{phase:measure}': ['p(95)<=500'],
    'unexpected_failures{phase:measure}': ['rate<0.01'],
    'http_reqs{phase:measure}': ['count>0'],
  },
  summaryTrendStats: ['avg', 'min', 'med', 'p(90)', 'p(95)', 'max'],
};

export function setup() {
  const res = http.post(`${BASE}/api/auth/login`, JSON.stringify({ email: 'demo@leavedesk.in', password: 'demo1234' }),
    { headers: { 'Content-Type': 'application/json' } });
  if (res.status !== 200) throw new Error(`login failed: ${res.status}`);
  return { token: res.json('access_token') };
}

// Each iteration uses a unique Mon-Fri date (different years per scenario) so requests never overlap.
function uniqueDay(baseYear, i) {
  const year = baseYear + Math.floor(i / 250);
  const k = i % 250;
  const d = new Date(Date.UTC(year, 0, 1));
  while (d.getUTCDay() !== 1) d.setUTCDate(d.getUTCDate() + 1);   // first Monday
  d.setUTCDate(d.getUTCDate() + Math.floor(k / 5) * 7 + (k % 5));
  return d.toISOString().slice(0, 10);
}

function apply(data, baseYear) {
  const day = uniqueDay(baseYear, exec.scenario.iterationInTest);
  const res = http.post(`${BASE}/api/leave-requests`,
    JSON.stringify({ leave_type_id: 1, start_date: day, end_date: day, reason: 'Load test leave request' }),
    { headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${data.token}` } });
  const ok = check(res, { 'created (201)': (r) => r.status === 201 });
  unexpected.add(!ok);
}

export function warmup(data) { apply(data, 2100); }
export function measure(data) { apply(data, 2400); }

export function handleSummary(data) {
  return { [__ENV.OUT || 'summary.json']: JSON.stringify(data, null, 2) };
}
