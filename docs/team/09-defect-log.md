# 09. Defect Management

Every defect below must also exist as a **GitHub Issue** (labels: `severity:*`, `priority:*`, `status:*`, `category:*`). Use `scripts/create_issues.sh` (needs `gh auth login`).

## 9.1 Defect log
| ID | Title | Category | Severity | Priority | Status | Triage decision | Evidence / test | Linked risk |
|---|---|---|---|---|---|---|---|---|
| DEF-001 | `leave_type_id: 1e400` (or any overflowing JSON number) crashes the API with HTTP 500 (`OverflowError` not caught in `Validator.integer`) | Input validation | **Major** | High | Open (fix prepared) | Fix now: one-line change, regression test exists | `tests/team/defects/test_def001_integer_overflow.py` | PR5 |
| DEF-002 | Dates such as `20270315`, `2027-W11-1` or the integer `20270315` are accepted though the API documents `YYYY-MM-DD` | Input validation | Minor | Low | Open | Fix next sprint | `test_def002_date_format.py` | PR5 |
| DEF-003 | Hard-coded fallback `SECRET_KEY`/`JWT_SECRET_KEY` allows forging admin tokens when env vars are unset | Security config | **Major** | High | Open | Fix before release (hold criterion EC2) | SEC-1 | PR6 |
| DEF-004 | Documented start command `python run.py` uses `debug=True` (interactive debugger) | Security config | **Major** | High | Open | Fix before release | SEC-2 | PR6 |
| DEF-005 | Inconsistent boundary: apply allows start = today but cancel of a request starting today is refused (`<` vs `<=`) | Business rule | Minor | Low | Open (design decision) | Clarify with owner; recorded as AS-2 | `test_cancel_start_date_boundary` | PR3 |
| DEF-006 | No throttling on `/api/auth/login` | Security config | Medium | Medium | Open | Accept for coursework, document | SEC-3 | PR6 |
| DEF-007 | `utils.utc_timestamp()` is unused dead code | Maintainability | Trivial | Low | Open | Remove or use | static analysis, `test_utc_timestamp_is_iso_string` | - |
| DEF-009 | Concurrent first requests for the same (employee, type, year) both INSERT the balance row -> UNIQUE violation -> HTTP 500 (`balance_for` get-or-create race). Found by k6 at 5 VUs (18 x 500) | Concurrency / data integrity | **Major** | High | Open (fix prepared) | Fix before release (EC4) | `tests/team/defects/test_def009_balance_race.py`, `evidence/perf/` | PR1, PR9 |
| DEF-008 | `react-router-dom` 7.x in vulnerable range (2 moderate advisories) | Dependency | Minor | Low | Open | Upgrade | npm audit | PR6 |

Severity: Critical = data loss/security breach in normal use, Major = rule bypass or crash on crafted input, Minor = wrong but harmless, Trivial = cosmetic.
Lifecycle: New -> Triaged -> In progress -> Fixed -> Verified -> Closed (or Reopened). Reopen count so far: 0 (reopen rate 0 / 0).

## 9.2 Pareto by category (9 defects)
| Category | Count | % | Cumulative % |
|---|---|---|---|
| Security config | 3 | 33.3 | 33.3 |
| Input validation | 2 | 22.2 | 55.6 |
| Business rule | 1 | 11.1 | 66.7 |
| Dependency | 1 | 11.1 | 77.8 |
| Maintainability | 1 | 11.1 | 88.9 |
| Concurrency / data integrity | 1 | 11.1 | 100.0 |
Security configuration and input validation account for 56 % of defects. Process actions: configuration checklist (secure defaults), generator-driven negative-input tests (`tools/gen_test_data.py`), and a concurrency check in the performance suite (this is how DEF-009 was found).
Note on severity: DEF-009 has the highest *business* impact of the functional defects (user-visible 500 on first use of a year, repeatable under 5 users).

## 9.3 Root cause analysis 1 - DEF-001 (500 on overflowing number)
**5 Whys**
1. Why did the API return 500? An `OverflowError` escaped `Validator.integer`.
2. Why? `int(value)` raises `OverflowError` for `float('inf')`, but the code only catches `TypeError` and `ValueError`.
3. Why was infinity possible? Python's JSON parser turns `1e400` into `inf`, and the validator accepts any JSON type for `leave_type_id`.
4. Why was that not noticed? Upstream tests only used well-formed numbers and strings; no test fed boundary/extreme numeric values.
5. Why? The team had no systematic negative-input technique (EP/BVA) or generator, so validation gaps were found only by chance.
**Fishbone** - Effect: HTTP 500 on crafted input.
* Method: no negative-input test technique; * Code: narrow `except`; * Tools: no fuzz/generator; * Requirements: input domain of `leave_type_id` not specified (OpenAPI missing); * People: validation written for happy-path users; * Environment: Python 3.11+ JSON/float behaviour not considered.
**Corrective action:** catch `OverflowError` in `Validator.integer` (patch: `docs/team/fix-pr/DEF-001.patch`), remove the xfail marker.
**Preventive actions:** OpenAPI spec as the source of the input domain; generator-driven EP/BVA tests in CI; add an "extreme values" class to the generator.

## 9.4 Root cause analysis 2 - DEF-003 (hard-coded fallback secret)
**5 Whys**
1. Why can an attacker forge a token? The JWT signing key is a constant visible in the source.
2. Why a constant? `os.getenv("SECRET_KEY", "<default>")` supplies a default for developer convenience.
3. Why is the default allowed in a deployable config? One `Config` class serves development and production; no environment-specific config.
4. Why? The project has no production hardening checklist or startup validation.
5. Why? Security configuration was not in the project's definition of done.
**Fishbone** - Effect: forgeable admin tokens.
* Method: no secure-defaults rule; * Code: default in `getenv`; * Tools: no secret scanner / config check in CI; * Documentation: README start command encourages dev mode; * People: convenience prioritised; * Environment: env vars not set in local runs.
**Corrective action:** raise on start when `JWT_SECRET_KEY` is unset unless `TESTING`/`FLASK_DEBUG`.
**Preventive actions:** add a CI check that greps for default secrets (or Bandit/Sonar security hotspots), config test `test_config_requires_secret`, secure-defaults checklist.
