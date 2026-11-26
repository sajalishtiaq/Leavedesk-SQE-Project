# 03. Use Case Specifications (automated in `e2e/tests/uc*.spec.ts`)
Group of three: assign two use cases per member (UC-1..UC-4 are ready; add UC-5/UC-6, e.g. "View leave balance" and "Filter requests", copying the pattern, if you are three).

## UC-1 Apply for leave (FR-A1..A6) - spec file `uc1-apply.spec.ts`
Actor: employee. **Pre:** signed in, Casual balance 12 days, no overlapping request. **Post (main):** request saved with status `pending`, `days` = working days, balance `used_days` unchanged, confirmation shown.
| Flow | Steps / condition | Automated id |
|---|---|---|
| Main | Open "Request time off", fill type, dates, reason, Send | UC1-MAIN |
| Alt A1 | Choose Sick leave instead of Casual | UC1-A1 |
| Alt A2 | Range spans a weekend; only Mon-Fri counted (2 days) | UC1-A2 |
| Exc E1 | Reason < 10 chars: message "Add a little more detail..."; correct it -> success | UC1-E1 |
| Exc E2 | 13 days > 12 balance: server message "Only 12 day(s)..."; correct to 12 -> success | UC1-E2 |
| Exc E3 | Overlaps own request: message "...overlaps these dates", no duplicate | UC1-E3 |

## UC-2 Review leave request (FR-B1..B3, B5) - `uc2-review.spec.ts`
Actor: admin. **Pre:** a pending request of another employee. **Post (main):** status `approved`, employee `used_days` += days.
| Flow | Steps / condition | Id |
|---|---|---|
| Main | Approvals -> Review -> Approve | UC2-MAIN |
| Alt A1 | Reject with note; balance unchanged | UC2-A1 |
| Alt A2 | Approved request appears under the Approved tab | UC2-A2 |
| Exc E1 | Reject without note -> "Add a short note..."; add note -> rejected | UC2-E1 |
| Exc E2 | Second approval exceeds balance -> error, stays pending, balance counted once | UC2-E2 |

## UC-3 Cancel leave (FR-B4) - `uc3-cancel.spec.ts`
Actor: employee (owner). **Pre:** pending/approved request starting after today. **Post (main):** status `cancelled`; approved leave returns days.
| Flow | Steps / condition | Id |
|---|---|---|
| Main | View -> Cancel request -> confirm (pending) | UC3-MAIN |
| Alt A1 | Cancel an approved request: balance restored | UC3-A1 |
| Alt A2 | "Keep it": nothing changes | UC3-A2 |
| Exc E1 | Rejected request: no cancel action | UC3-E1 |
| Exc E2 | Leave starting today: no cancel action | UC3-E2 |

## UC-4 Sign in and role-based access (FR-B3, B6) - `uc4-auth.spec.ts`
Actor: employee / admin / visitor. **Post (main):** employee lands on the dashboard.
| Flow | Steps / condition | Id |
|---|---|---|
| Main | Sign in with valid credentials | UC4-MAIN |
| Alt A1 | Submit with Enter key | UC4-A1 |
| Alt A2 | Reveal password with the toggle | UC4-A2 |
| Exc E1 | Wrong password: "Incorrect email or password." | UC4-E1 |
| Exc E2 | Employee opens /approvals: redirected, no admin screen | UC4-E2 |
| Exc E3 | Signed-out visitor opens /leave: redirected to sign in | UC4-E3 |
Run: `cd e2e && npm install && npm run install-browsers && npm test` (backend/frontend start automatically).
