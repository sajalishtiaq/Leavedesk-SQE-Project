# 02. Test Plan (living document, update weekly)

## 2.1 Scope
**In scope:** Leave Requests module - Workflow A (apply) and Workflow B (review / cancel), shared record `LeaveBalance.used_days`;
server code `backend/app/{services,utils}.py`, `backend/app/api/leaves.py`; API; React UI screens for both workflows; security,
accessibility and performance of these workflows.
**Out of scope:** registration/dashboard/team pages (used only as helpers), MySQL/production deployment, email notifications (none exist),
upstream tests (earn no marks), cross-browser testing (Chromium only), load beyond 5 virtual users.

## 2.2 Approach by risk level (see 03-risk-register.md)
| Level (L x I) | Areas | Techniques and depth |
|---|---|---|
| Very High (>= 15) | PR1 balance integrity, PR6 auth configuration | Full MCC + MC/DC on balance/approval logic, API read-back, recovery test, mutation + custom operators, source/config review, ZAP passive |
| High (10-14) | PR2 authorization, PR3 working-day calc, PR4 state machine, PR5 validation | Decision tables, full state-transition matrix, EP + 3-point BVA on every input (generated), Playwright access matrix |
| Medium (5-9) | PR7 persistence, PR8 accessibility, PR9 performance | Failure-recovery test, axe + Lighthouse + keyboard test, k6 (1 and 5 VUs) |
| Low (<= 4) | Cosmetic UI text | Covered incidentally by use-case tests |

Test levels: **Unit/white-box** (`tests/team/unit`), **API/integration** (`tests/team/api`), **Browser E2E** (`e2e/tests`), **Static** (SonarQube, radon),
**Mutation** (mutmut + `tools/custom_mutation.py`), **Security**, **Performance**, **Accessibility**.

## 2.3 Roles
| Area | Owner (fill names/roll numbers) | Scope |
|---|---|---|
| 1 | Member 1 | static analysis, white-box unit tests, mutation, CI |
| 2 | Member 2 | OpenAPI, data generator, API/integration tests |
| 3 | Member 3 (or split in pairs) | use cases, usability, accessibility, security, performance |
| All | everyone | test plan, risk register, defects, reports |

## 2.4 Environment and test data
Ubuntu/Windows + Python 3.12, Node 20, Chromium (Playwright), k6 0.55, SonarQube Community (Docker), OWASP ZAP (Docker).
Application started with `scripts/reset_db.sh` + `python run.py` (or `flask run --no-debugger`). Test data: synthetic users/requests only;
unit/API tests use an in-memory SQLite database and a frozen date (2027-03-10, Wednesday) so results never depend on the calendar;
E2E tests register a fresh employee per test; k6 uses unique future dates per iteration. Reset: `scripts/reset_db.sh`.

## 2.5 Schedule (example - adapt to your deadline)
| Week | Deliverables |
|---|---|
| 1 | Registration, baseline, test basis, risk register, plan; unit tests + coverage |
| 2 | OpenAPI + generator + API tests; mutation analysis; CI pipeline + blocked PR + fix PR |
| 3 | Playwright use cases, accessibility fix + before/after, security checks, k6 runs |
| 4 | Defect RCA, completion report, AI-use record, viva rehearsal |

## 2.6 Entry / exit / suspension / resumption criteria
**Entry:** repo forked, baseline tagged, app starts and resets from scripts, test basis approved, tools installed.
**Exit:** all criteria in 03-risk-register.md section "Exit criteria" met or the deviation is recorded with residual risk.
**Suspension:** application will not start or reset; baseline suite red on a clean checkout; > 30 % of tests blocked by one defect; CI infrastructure down.
**Resumption:** environment restored and `scripts/reset_db.sh` + full suite green on a clean checkout; blocking defect fixed or worked around and recorded.

## 2.7 Three-point estimation (person-hours)  O = optimistic, M = most likely, P = pessimistic, E = (O + 4M + P) / 6
| Area | O | M | P | Estimate E | Actual (fill at the end) |
|---|---|---|---|---|---|
| Test basis, plan, risk register | 4 | 6 | 10 | 6.3 | |
| Static analysis + CC hand calc | 2 | 3 | 5 | 3.2 | |
| Unit / white-box tests + MCC/MC-DC | 8 | 12 | 20 | 12.7 | |
| OpenAPI + generator + API tests | 8 | 12 | 20 | 12.7 | |
| Mutation analysis + custom operators | 5 | 8 | 14 | 8.5 | |
| CI quality gate + PRs | 3 | 5 | 9 | 5.3 | |
| Playwright use cases (4 UCs) | 6 | 10 | 16 | 10.3 | |
| Usability / accessibility + fix | 4 | 6 | 10 | 6.3 | |
| Security assessment | 3 | 5 | 8 | 5.2 | |
| Performance + recovery | 3 | 5 | 8 | 5.2 | |
| Defects, RCA, reports | 5 | 8 | 12 | 8.2 | |
| **Total** | 51 | 80 | 132 | **83.9** | |
Estimates are the team's starting assumptions; replace "Actual" with logged hours and explain variances in the completion report.

## 2.9 Project-level risks
See PJ1-PJ3 in the risk register.
