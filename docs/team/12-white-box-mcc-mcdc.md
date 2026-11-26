# 12. White-box Testing: Coverage, Multiple Condition Coverage (MCC) and MC/DC

## 12.1 Statement and branch coverage (coverage.py, scope in `.coveragerc`)
| Module | Statements | Branches | Coverage |
|---|---|---|---|
| `app/services.py` | 65 | 30 | 100 % |
| `app/utils.py` | 111 | 34 | 100 % |
| `app/api/leaves.py` | 168 | 58 | 100 % |
| **Total** | **344** | **122** | **100 % statement, 100 % branch, 0 uncovered** |
Command: `python -m coverage run -m pytest && python -m coverage report`. Nothing is excluded or `# pragma: no cover`d; the dead function `utc_timestamp` is covered by a direct test (`test_utc_timestamp_is_iso_string`) and reported as DEF-007. The four business rules BR1-BR4 are each covered by dedicated tests (see 01-test-basis.md and 04-traceability.md).

## 12.2 Critical module and why
**Critical module = review/cancel authorization and state decisions in `app/api/leaves.py` + the balance rule in `app/services.py`.** They protect the shared record (risk PR1, score 15) and access control (PR2).

## 12.3 Complete MCC - review decision (`review_leave_request`)
Conditions: **A** = reviewer is admin, **B** = request status is `pending`, **C** = request does not belong to the reviewer.
Intended outcome: ALLOW only when A and B and C. (The code checks them in sequence A -> B -> C; each failed check gives its own error code.)
| # | A | B | C | Expected outcome | Test case (`test_review_decision_table[...]`) |
|---|---|---|---|---|---|
| 1 | F | F | F | 403 | `[False-False-False-403]` |
| 2 | F | F | T | 403 | `[False-False-True-403]` |
| 3 | F | T | F | 403 | `[False-True-False-403]` |
| 4 | F | T | T | 403 | `[False-True-True-403]` |
| 5 | T | F | F | 409 | `[True-False-False-409]` |
| 6 | T | F | T | 409 | `[True-False-True-409]` |
| 7 | T | T | F | 403 (own request) | `[True-True-False-403]` |
| 8 | T | T | T | 200 | `[True-True-True-200]` |
All 2^3 = 8 combinations are executed.

## 12.4 MC/DC pairs derived from the MCC table (n + 1 = 4 tests)
Each condition must independently change the decision (ALLOW vs not ALLOW) while the others are held fixed.
| Condition | Pair (MCC rows) | A B C -> outcome | Shows |
|---|---|---|---|
| A (admin) | 8 and 4 | TTT -> ALLOW, FTT -> deny | admin role alone flips the decision |
| B (pending) | 8 and 6 | TTT -> ALLOW, TFT -> deny | status alone flips it |
| C (not own) | 8 and 7 | TTT -> ALLOW, TTF -> deny | ownership alone flips it |
Minimal MC/DC set = rows {8, 4, 6, 7} (rows 8, 4, 6, 7). The full MCC set (8 rows) is run, so the MC/DC set is a subset.

## 12.5 Complete MCC and MC/DC - cancel decision (`cancel_leave_request`)
Conditions: **O** = caller is the owner, **S** = status in (pending, approved), **F** = `start_date > today`. ALLOW only when O and S and F.
| # | O | S | F | Outcome | Test (`test_cancel_decision_table`) |
|---|---|---|---|---|---|
| 1 | F | F | F | 403 | `[False-False-False-403]` |
| 2 | F | F | T | 403 | `[False-False-True-403]` |
| 3 | F | T | F | 403 | `[False-True-False-403]` |
| 4 | F | T | T | 403 | `[False-True-True-403]` |
| 5 | T | F | F | 409 | `[True-False-False-409]` |
| 6 | T | F | T | 409 | `[True-False-True-409]` |
| 7 | T | T | F | 409 | `[True-True-False-409]` |
| 8 | T | T | T | 200 | `[True-True-True-200]` |
MC/DC pairs: O -> (8,4); S -> (8,6); F -> (8,7). Minimal set {8,4,6,7} = rows 8, 4, 6, 7. Boundary of F additionally covered 3-point (`test_cancel_start_date_boundary`: yesterday 409, today 409, tomorrow 200).

## 12.6 MCC - overlap guard in `validate_leave_window`: `if not errors and overlapping_request(...)`
P = `not errors` (no earlier validation error), Q = `overlapping_request(...)` returns a request. Python short-circuits: Q is not evaluated when P is false.
| P | Q | Outcome | Test |
|---|---|---|---|
| T | T | overlap error added | `test_validate_overlap` |
| T | F | no error (continue to balance check) | `test_validate_ok_returns_days_and_balance` |
| F | - (not evaluated) | skipped | `test_validate_end_before_start` (and other early errors) |
| F | T/F | **infeasible**: Q is never evaluated when P is false - justified, not testable |
MC/DC: P independent via (T,T) vs (F,-); Q independent via (T,T) vs (T,F). Set {TT, TF, F-} = 3 tests = n + 1.

## 12.7 Basis paths of `validate_leave_window` (V(G) = 10, see 11-static-analysis.md)
10 independent paths are exercised by 14 `test_validate_*` cases (end<start, cross-year, past start, today OK, no working days, overlap, balance below/at/above, success).
