# 05. Performance and Recovery

## 5.1 Operation and limits (decided before testing)
Operation: `POST /api/leave-requests` (Workflow A, state-changing; one DB write + overlap query + balance read).
| Workload | p95 response time limit | Unexpected failures |
|---|---|---|
| 1 virtual user (baseline) | <= 500 ms | < 1 % |
| 5 simultaneous virtual users | <= 500 ms | < 1 % |
Why: this is an interactive form submit; people perceive responses under ~0.5 s as immediate, and a leave request is entered a few times a year, so
500 ms is generous but strict enough to catch a missing index or a lock. p95 (not the average) is used so slow outliers count. One failure in 100 is the
most an HR tool should lose; "unexpected" means any response other than the documented 201 (validation rejections are excluded by design because the
script sends only valid, non-overlapping requests with unique dates).

## 5.2 Method
`scripts/run_perf.sh`: k6 0.55, Flask dev server (`flask run --no-debugger --no-reload`) and k6 on the same machine, SQLite file DB reset before every run
(`scripts/reset_db.sh`), same build/commit. Each run = 10 s warm-up at the target VUs + **60 s measured** (tag `phase:measure`). 1 VU x 2 runs, 5 VUs x 2 runs.
Raw output: `evidence/perf/*.json|txt`, environment: `evidence/perf/environment.txt`.

## 5.3 Results
| VUs | Run | p95 (ms) | Requests/s | Unexpected failures % | Verdict |
|---|---|---|---|---|---|
| 1 | 1 | 12.2 | 87.3 | 0.00 | PASS |
| 1 | 2 | 9.6 | 106.4 | 0.00 | PASS |
| 5 | 1 | 96.8 | 89.8 | 0.38 | PASS |
| 5 | 2 | 107.0 | 79.6 | 0.25 | PASS |

Environment: 1 CPU core, Linux x86_64, Python 3.12.3, k6 0.55.0, k6 and server on the same machine (see `evidence/perf/environment.txt`).

**Interpretation against the limits**
* 1 VU: p95 9.6-12.2 ms, ~87-106 req/s, 0 failures -> **meets** both limits with a very large margin.
* 5 VUs: p95 96.8-107.0 ms (~9x the 1-VU value, because the single-core Flask dev server and SQLite writer serialise work) while throughput does not grow (80-90 req/s) -> the server is **saturated at ~90 req/s**; latency rises with queueing, not with a slower request. Still **within** the 500 ms limit.
* 5 VUs: unexpected failures 0.38 % and 0.25 % (< 1 % limit, so the criterion is met) but **not zero**. Server log analysis found 18 HTTP 500 responses, all `UNIQUE constraint failed: leave_balances...` -> **DEF-009**: two concurrent first requests for the same (employee, type, year) both insert the balance row. This is a genuine race condition (check-then-act in `balance_for`) found only because we measured under concurrency; it is a direct instance of risk PR1.
* Run-to-run variation at 5 VUs: p95 96.8 vs 107.0 ms (10 %), req/s 89.8 vs 79.6: results are comparable (same build, machine, seed data) but noisy; two runs per setup are the minimum, quote both.
Verdict: **limits met**; residual risk = DEF-009 must be fixed before release because failures grow with concurrent first-time use.

## 5.4 Failure-and-recovery test (`tests/team/api/test_recovery.py`)
Test double: `sqlalchemy.orm.Session.commit` replaced by a stand-in that raises `OperationalError("database unavailable")` before the write completes.
For approve, apply and cancel: (1) fail -> HTTP 500; (2) after the request ends (session rollback) the persisted state is unchanged (status, balance, request count);
(3) restore the dependency, retry -> expected final state; (4) repeat the request -> 409/422 and no duplicate record or double counting.
Observation: the API returns a generic 500 when the database is unavailable (no 503 / Retry-After) - recorded as a weakness, not a defect.
