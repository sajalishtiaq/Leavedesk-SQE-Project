# 01. System, Scope and Test Basis

## 1.1 System under test
| Item | Value |
|---|---|
| MIS | LeaveDesk, Employee Leave Management (Flask API + React UI + SQLite) |
| Upstream | https://github.com/Vardhan32/leave-management-system |
| Licence | MIT (see `LICENSE`) |
| Baseline commit | `b002faa4b46ba2090489c200c61787551591c70d` (git tag `baseline-upstream`) |
| Module | Leave Requests (`backend/app/api/leaves.py`, `services.py`, `utils.py`) |
| Our tests | `tests/team/` (upstream `backend/tests/` earns no marks and is not used) |

## 1.2 Reproducible environment
```bash
cd backend && python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt -r ../requirements-dev.txt
../scripts/reset_db.sh          # create tables + seed demo data (reset between runs)
python run.py                   # API on http://localhost:5001
cd ../frontend && npm ci && npm run dev   # UI on http://localhost:5173
# run all team tests
cd .. && python -m pytest
```
Test accounts: `demo@leavedesk.in / demo1234` (employee), `admin@leavedesk.in / admin1234` (admin).
Reset between runs: `scripts/reset_db.sh` (deletes `leave.db`, re-creates, re-seeds).

## 1.3 Selected workflows
| Workflow | Start condition | User action | Expected outcome |
|---|---|---|---|
| **A. Apply for leave** | Employee logged in, balance exists (default Casual = 12 days/year) | `POST /api/leave-requests` with type, dates, reason | `201`, request saved as `pending`, `days` = Mon-Fri count. Invalid data / over-balance / overlap -> `422`, nothing saved |
| **B. Review and cancel leave** | A `pending` request exists; admin (or owner for cancel) logged in | Admin `POST .../review` (approve/reject) or owner `POST .../cancel` | pending -> approved / rejected / cancelled; approved -> cancelled. Approve increases `used_days`, cancel of approved leave decreases it |

**Shared record:** `LeaveBalance.used_days` (per employee, leave type, year).
Workflow B (approve) **changes** it, Workflow B (cancel approved) **restores** it, Workflow A **reads** it (remaining = allocated - used) to accept/reject.

## 1.4 Functional requirements
| ID | Workflow | Requirement |
|---|---|---|
| FR-A1 | A | An authenticated user can submit a request (leave_type_id, start_date, end_date, reason); it is stored with status `pending` |
| FR-A2 | A | Requested days = number of Mon-Fri days in the inclusive range; a range with 0 working days is rejected |
| FR-A3 | A | A request is rejected if working days > remaining balance of that type/year |
| FR-A4 | A | Dates must satisfy: end >= start, start >= today, start and end in the same calendar year |
| FR-A5 | A | A request overlapping the same employee's own pending/approved request is rejected |
| FR-A6 | A | Input validation: leave type must exist (404), reason 10-500 chars, body must be a JSON object |
| FR-B1 | B | Admin approves a pending request: status `approved`, reviewer/time/note stored, `used_days` += days |
| FR-B2 | B | Admin rejects a pending request only with a note: status `rejected`, balance unchanged |
| FR-B3 | B | Only an admin may review; an admin cannot review their own request; only `pending` requests can be reviewed |
| FR-B4 | B | The owner can cancel their own pending request or approved request that starts after today; cancelling approved leave restores the days |
| FR-B5 | B | Approval re-checks the balance and fails (422) if the days are no longer available |
| FR-B6 | B | Employees see only their own requests (others return 404); admins see all |

## 1.5 Business rules
| ID | Type | Rule |
|---|---|---|
| BR1 | **Boundary / limit** | `working_days <= remaining_days` (remaining = allocated - used, never negative); also reason length 10..500, note <= 500, per_page 1..50 |
| BR2 | **Decision (3 Boolean conditions)** | Review is allowed only if `is_admin` AND `status == pending` AND `request.user != reviewer` |
| BR3 | **State change** | pending -> approved / rejected / cancelled; approved -> cancelled (only before start); rejected and cancelled are final |
| BR4 | Decision (3 conditions) | Cancel is allowed only if caller is owner AND status in (pending, approved) AND `start_date > today` |
| BR5 | Date rule | start >= today, end >= start, same calendar year, at least one working day |
| BR6 | Uniqueness | No overlap with own pending/approved requests (rejected/cancelled do not block) |

## 1.6 Roles and access matrix
| Action | Employee (own) | Employee (other's request) | Admin |
|---|---|---|---|
| Apply for leave | Allowed | n/a | Allowed (for self) |
| View request detail | Allowed | **404** | Allowed |
| List requests | Own only | n/a | All |
| Review (approve/reject) | **403** | **403** | Allowed (not own: 403) |
| Cancel | Allowed (rules BR4) | **403** | **403** (not owner) |
| View other's balances | **403** | n/a | Allowed |
| `GET /api/team` | **403** | n/a | Allowed |

## 1.7 Test basis and recorded assumptions
Basis = upstream `README.md` + source code (no formal spec).
| # | Assumption / observation |
|---|---|
| AS-1 | Balance year = year of the **start date** (code: `validate_leave_window(..., start.year)`) |
| AS-2 | Applying with start = today is **allowed** (`start < today` is rejected) but cancelling a request that starts today is **not** (`start <= today`); recorded as an inconsistency, tested as implemented |
| AS-3 | Pending requests do **not** reserve balance; balance is consumed on approval (FR-B5 covers the race) |
| AS-4 | Validation order in review: role -> input -> existence -> state -> ownership. Test `test_review_validation_runs_before_lookup` documents it |
| AS-5 | `utils.utc_timestamp` is dead code (unused). Covered by a direct unit test and reported in static analysis |

## 1.8 Records read / changed
| Record | Workflow A | Workflow B |
|---|---|---|
| `LeaveRequest` | creates (pending) | updates status, reviewer, note, timestamps |
| `LeaveBalance.used_days` | **reads** (remaining) | **changes** (approve +days, cancel approved -days) |
| `LeaveBalance` row | creates default row if missing | creates default row if missing |
| `LeaveType` | reads (exists, default days) | reads |
| `User` | reads (role, active) | reads (role, ownership) |

## 1.9 My Understanding
Workflow A, Apply for leave: an employee picks a leave type, dates and a reason. The system counts only working days (Mon–Fri), and if the request is valid it saves it as pending (mine was 2 days). A pending request does not change the balance.

Workflow B, Review and cancel: an admin approves or rejects a pending request. Approving changes its status to approved and reduces the employee's remaining balance by the request's days. If the employee cancels an approved request before it starts, the days are returned and my balance went back to 10.

Shared record: LeaveBalance.used_days. Workflow A reads it to decide whether a request fits, and Workflow B changes it on approval (and on cancelling an approved request).