# 14. Test Completion Report (DRAFT - update with your own final runs)

## 14.1 What was tested
| Area | Status | Evidence |
|---|---|---|
| Unit / white-box | Done: 344 statements, 122 branches, 100 % | `coverage report`, 12-white-box-mcc-mcdc.md |
| API / integration | Done: EP + 3-point BVA (hand-written + 71 generated cases), rejections, invalid transitions, repeated requests, read-back | `tests/team/api` |
| Test-data generation | Done: spec -> EP/BVA; regeneration demo (2 constraints changed) | `evidence/regeneration_demo.txt` |
| Mutation | Done: mutmut 98.9 % (4 equivalent), custom operators 95.7 % (2 equivalent) | `evidence/mutation_analysis.md` |
| Performance + recovery | Done: p95 and failure % at 1 and 5 VUs, 2 runs each; 3 recovery tests | 05-performance-plan.md |
| Security | Partly: source review, dependency audit done; Playwright access matrix + ZAP passive **to run** | 07-security-assessment.md |
| Browser E2E (4 UCs, 22 flows) | **Written, not executed by the AI** - run `cd e2e && npm test` | 03-use-cases.md |
| Accessibility (axe, Lighthouse, keyboard) | **Written, to run**; before/after fix pending | 08-usability-accessibility.md |
| SonarQube / GitHub Actions | **Configured, to run**; thresholds justified | 06-ci-quality-gate.md |
## 14.2 Not tested / deviations
* Concurrent approvals of two different pending requests (TOCTOU on `used_days`) - only the balance-row creation race was reproduced (DEF-009).
* Cross-browser, mobile, large data volumes, MySQL backend.
* Deviation: unit/API tests freeze the date and use cheap password hashing for speed/determinism (documented).
## 14.3 Open defects (9)
DEF-001, 002, 003, 004, 005, 006, 007, 008, 009 - see 09-defect-log.md. Open Major: **001, 003, 004, 009**.
## 14.4 Residual risk per risk
| Risk | Residual | Reason |
|---|---|---|
| PR1 balance integrity | High until DEF-009 fixed | Race found; approvals concurrency untested |
| PR6 auth configuration | High | DEF-003/004 open |
| PR2 authorization | Low | all decision tables and access checks pass |
| PR3/PR4 rules, state machine | Low | 100 % coverage, mutation killed |
| PR5 validation | Medium | DEF-001 open (fix prepared), DEF-002 minor |
| PR7 persistence | Low | recovery tests pass |
| PR8 accessibility | Unknown | measure and fix (not yet run) |
| PR9 performance | Low | p95 <= 107 ms at 5 VUs, failures 0.25-0.38 % (DEF-009) |
## 14.5 Release criteria: actual vs target (update after your runs)
| Criterion | Target | Actual |
|---|---|---|
| EC1 balance integrity tests + mutation | 100 % coverage, mutation >= 95 % | 100 %, 98.9 % - met |
| EC2 auth configuration | DEF-003/004 fixed | open - **not met** |
| EC4 no open Major functional defect | 0 | 2 (DEF-001, DEF-009) - **not met** |
## 14.6 Recommendation
**HOLD** until DEF-001, DEF-003, DEF-004 and DEF-009 are fixed through the pipeline (patches are prepared in `docs/team/fix-pr/`) and E2E, accessibility and ZAP results are added. Reassess then.
