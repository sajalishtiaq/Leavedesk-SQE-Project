# 03. Risk Register and Exit Criteria

Scale: Likelihood (L) and Impact (I) each 1-5. Score = L x I. Very High >= 15, High 10-14, Medium 5-9, Low <= 4.

## 3.1 Register
| ID | Type | Risk | L | I | Score | Level | Technique / depth | Evidence |
|---|---|---|---|---|---|---|---|---|
| PR1 | Product | Balance integrity: approval/cancel miscounts `used_days`, or two approvals overdraw the balance (no row lock) | 3 | 5 | 15 | Very High | MCC + MC/DC, read-back after success and rejection, recovery test, mutation (USED, BALANCE operators) | unit + API tests, mutation report |
| PR6 | Product | Weak authentication configuration (hard-coded fallback secret, debug server, token in localStorage, no login throttling) | 3 | 5 | 15 | Very High | Source/config review, ZAP passive, pip-audit/npm audit | 07-security-assessment.md |
| PR2 | Product | Authorization bypass: employee reviews / reads another employee's data | 2 | 5 | 10 | High | Decision tables (review, cancel), access matrix in Playwright, mutation (ROLE, OWNER) | access matrix |
| PR3 | Product | Wrong working-day or date-limit calculation (weekends, year end, today) | 3 | 4 | 12 | High | EP + 3-point BVA, loop testing of `working_days` | unit + generated tests |
| PR4 | Product | Illegal state transition corrupts the request lifecycle | 3 | 4 | 12 | High | Full state-transition matrix (4 allowed + 8 disallowed), mutation (STATUS) | `test_state_transition_matrix` |
| PR5 | Product | Input validation gaps crash the API (HTTP 500) or accept malformed data | 4 | 3 | 12 | High | Generated EP + BVA on every input, one invalid value per test | DEF-001, DEF-002 |
| PR7 | Product | Persistence failure leaves partial state or duplicates on retry | 2 | 4 | 8 | Medium | Failure-and-recovery tests (3 operations) | `test_recovery.py` |
| PR8 | Product | UI not usable by keyboard / assistive technology | 3 | 3 | 9 | Medium | Keyboard test, axe-core, Lighthouse, before/after fix | 08-usability-accessibility.md |
| PR9 | Product | Slow responses or failures under concurrent apply requests | 2 | 3 | 6 | Medium | k6, 1 and 5 VUs, 2 runs each | 05-performance-plan.md |
| PJ1 | Project | Team members unfamiliar with tools; schedule compression before the deadline | 4 | 3 | 12 | High | Scripts automate setup; area ownership; weekly review; viva rehearsal | weekly reports |
| PJ2 | Project | Heavy tools (SonarQube/Docker, ZAP, browsers) fail on student laptops | 3 | 3 | 9 | Medium | Document fallbacks, use CI runners, keep evidence screenshots | CI logs |
| PJ3 | Project | Upstream repository changes or disappears | 1 | 3 | 3 | Low | Pinned commit hash, forked repo | baseline tag |

## 3.2 5 x 5 matrix (IDs placed at their L, I cell)
```
Impact 5 |      |  PR2 |  PR1 PR6 |      |      |
Impact 4 |      | PR7  | PR3 PR4  |      |      |
Impact 3 | PJ3  | PR9  | PR8 PJ2  | PR5 PJ1 |   |
Impact 2 |      |      |          |      |      |
Impact 1 |      |      |          |      |      |
         | L=1  | L=2  |   L=3    | L=4  | L=5  |
```
(PR1, PR6 at L=3; PR2 at L=2; PR3, PR4 at L=3; PR5, PJ1 at L=4.)

## 3.3 Exit criteria (measurable)
| ID | Criterion | Tied to | Measure | Target |
|---|---|---|---|---|
| EC1 | **Balance integrity:** all unit/API tests on approval, cancel and balance rules pass; mutmut score and custom-operator score on the business-rule modules | PR1 (highest) | `coverage report`, mutmut | 100 % statement + branch; mutation >= 95 %; 0 killable custom mutants alive |
| EC2 | **Authentication configuration:** no hard-coded production secret, debug disabled in the run command, dependency audit clean of High/Critical | PR6 (highest) | source review, pip-audit, npm audit | 0 High/Critical; DEF-003/004 fixed or formally accepted |
| EC3 | **Access control:** all access-matrix checks pass | PR2 | Playwright `access.spec.ts` | 100 % pass |
| EC4 | **Functional:** no open Critical/Major defect in the two workflows | PR3-PR5 | GitHub Issues | 0 open |
| EC5 | **Performance:** p95 and unexpected failures at 1 and 5 VUs | PR9 | k6 | p95 <= 500 ms; failures < 1 % |
| EC6 | **Accessibility:** serious/critical axe violations on the key screens after the fix | PR8 | axe-core + Lighthouse | 0 serious/critical; Lighthouse accessibility >= 90 |

## 3.4 Weekly monitoring metrics (GQM)
| Goal | Question | Metric |
|---|---|---|
| Know how complete requirements coverage is | How many requirements have at least one passing test? | Requirements coverage = covered FR / 12 (see 04-traceability.md) |
| Know the product quality trend | How many defects per size? | Defect density = defects / KLOC of tested code (344 statements ~ 0.35 KLOC) |
| Know fix quality | How often are fixes wrong? | Reopen rate = reopened / closed defects |
