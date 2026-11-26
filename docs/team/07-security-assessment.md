# 07. Defensive Security Assessment (local copy, synthetic data, test accounts only)

## 7.1 Attack surface (both workflows)
| Route | Method | Data | Auth |
|---|---|---|---|
| `/api/auth/login`, `/api/auth/register` | POST | email, password | public |
| `/api/leave-requests` | POST / GET | type, dates, reason / filters | JWT |
| `/api/leave-requests/<id>` | GET | one request | JWT, owner or admin (others get 404) |
| `/api/leave-requests/<id>/review` | POST | decision, note | JWT, **admin only**, not own, pending only |
| `/api/leave-requests/<id>/cancel` | POST | - | JWT, **owner only** |
| `/api/leave-balances` | GET | `user_id`, `year` | JWT, own only unless admin |
| `/api/team` | GET | all employees | JWT, admin only |
Data: users (password hash), leave requests, leave balances. Token: JWT (HS256) sent as `Authorization: Bearer`, stored by the UI in `localStorage`.

## 7.2 Access matrix (expected) and automated verification
Verified by `e2e/tests/access.spec.ts` (Playwright, writes `evidence/access_matrix_results.json`) and by API tests (`test_review_decision_table`, `test_cancel_decision_table`, `test_balances_user_id_permissions`, `test_admin_required_decorator_on_team_endpoint`).
| # | Role | Action | Expected | Evidence |
|---|---|---|---|---|
| 1 | employee (other) | review someone else's request | 403 | POST .../review |
| 2 | employee (owner) | approve own request | 403 | POST .../review |
| 3 | employee (other) | view someone else's request | 404 (hidden, no information leak) | GET /leave-requests/<id> |
| 4 | employee (other) | read someone else's balances | 403 | GET /leave-balances?user_id= |
| 5 | anonymous | list requests | 401 | GET /leave-requests |
| 6 | admin | cancel an employee's request | 403 | POST .../cancel |
| 7 | employee (owner) | view own request | 200 (allowed) | GET /leave-requests/<id> |
| 8 | admin | approve employee request | 200 (allowed) | POST .../review |
| 9 | employee (UI) | open /approvals | redirected | browser URL |
Observed results: fill from `access_matrix_results.json` after running `npm test` (API-level equivalents already pass in `tests/team/api`).

## 7.3 OWASP ZAP passive scan
Run `scripts/zap_passive.sh` (ZAP daemon in Docker, Playwright traffic proxied through it, **no active scan**). Alerts are saved to
`evidence/security/zap_alerts.json`. Security controls reviewed (with source corroboration):
| Control | Observation | Source evidence |
|---|---|---|
| Session handling | No session cookies: authentication is a bearer JWT in `localStorage` (so cookie flags HttpOnly/Secure/SameSite do not apply; XSS would expose the token) | `frontend/src/auth/AuthContext.jsx` lines using `localStorage` |
| Role checks | Enforced server-side per endpoint (not only in the UI) | `leaves.py` `review_leave_request`, `cancel_leave_request`; `utils.admin_required` |
| Security headers | Flask sets none (no CSP, X-Frame-Options, X-Content-Type-Options) - expect ZAP passive alerts | no `after_request` hook in `app/__init__.py` |
| CORS | Restricted to configured origins (default `http://localhost:5173`) | `config.py` `CORS_ORIGINS` |

## 7.4 Dependency audit (evidence in `evidence/security/`)
| Tool | Scope | Result |
|---|---|---|
| pip-audit 2.x | 19 packages resolved from `backend/requirements.txt` (Flask 3.1.3, Flask-SQLAlchemy 3.1.1, Flask-JWT-Extended 4.7.4, Flask-Cors 6.0.5, PyMySQL 1.2.4, python-dotenv 1.2.4, PyJWT 2.15.1, SQLAlchemy 2.1.9, Werkzeug 3.1.9, ...) | **No known vulnerabilities** |
| npm audit | 145 packages (37 prod) from `frontend/package-lock.json` | **2 moderate**: `react-router-dom` / `react-router` (open redirect via backslash in `<Link>`/`useNavigate`, GHSA-wrjc-x8rr-h8h6; constructor injection in SSR hydration, GHSA-337j-9hxr-rhxg) |

## 7.5 Findings
| ID | Component | Evidence | Likely impact | Recommended correction | Severity | Risk |
|---|---|---|---|---|---|---|
| SEC-1 (DEF-003) | `app/config.py` | `SECRET_KEY` and `JWT_SECRET_KEY` fall back to a public constant when env vars are unset | Anyone can forge a valid admin JWT -> full access | Fail startup if `JWT_SECRET_KEY` is missing in non-test mode; document env setup | High | PR6 |
| SEC-2 (DEF-004) | `backend/run.py` | `app.run(port=5001, debug=True)` | Werkzeug interactive debugger and reloader if exposed beyond localhost | Use `FLASK_DEBUG` env, never `debug=True` in the documented start command | High | PR6 |
| SEC-3 (DEF-006) | `/api/auth/login` | No throttling or lockout (loop of wrong passwords never blocked) | Online password guessing | Rate limit (Flask-Limiter) per IP/account | Medium | PR6 |
| SEC-4 | UI token storage | JWT in `localStorage`, 12 h lifetime, no revocation | Token theft by XSS persists 12 h | httpOnly SameSite cookie or shorter expiry + refresh | Medium | PR6 |
| SEC-5 | HTTP responses | No CSP / X-Frame-Options / nosniff | Clickjacking, MIME sniffing | Add headers (Flask-Talisman) | Low | PR6 |
| SEC-6 (DEF-008) | `react-router-dom` 7.x range | npm audit | Open redirect in links built from user input | Upgrade to >= 7.18.6 (semver-major per audit) | Medium (not reachable: no user-controlled `to`) | PR6 |

## 7.6 Verified controls (no finding)
* Every state-changing endpoint requires a valid JWT (401 otherwise) - `test_missing_and_garbage_token`.
* Role escalation via registration impossible: `register` always creates `role="employee"` - source review `auth.py`.
* IDOR protected: employee reading another employee's request gets 404, balances 403 - API + access tests.
* SQL injection: all queries use the SQLAlchemy ORM with bound parameters (no string-built SQL); search/filters use `ilike(pattern)`.
* Passwords are stored hashed (Werkzeug); inactive users are rejected on every request (`current_user`).
* Dependency audit (Python): clean.
