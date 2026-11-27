# 13. Responsible AI-Use Record (required in the PDF; part of the 20 viva marks)

**Rule for this project:** AI may draft; the team must be able to explain, rerun and defend every artefact. Anything you cannot explain in the viva loses marks.
Fill the "Understood by" column honestly; each member should be able to explain at least the rows of their own area.

| # | Date | Tool | Task | What AI produced | What the team verified / changed | Understood by |
|---|---|---|---|---|---|---|
| 1 | 24-11-26 | Claude (Anthropic) | Repository selection | Shortlist of 5 repos; checked licence, size, business logic by cloning; chose LeaveDesk (MIT, Flask+React+SQLite) | Team confirmed licence file, ran upstream tests (53 pass), registered in the sheet | Saliha Noor |
| 2 | 24-11-26 | Claude | Test basis + business rules | Requirements, rules BR1-BR6, access matrix, assumptions | Cross-checked every rule against `services.py` / `leaves.py` | Sajal Ishtiaq |
| 3 | 24-11-26 | Claude | Unit + API test suite (`tests/team`) | 326 tests incl. decision tables, state matrix, BVA | Ran with coverage (100 % statement + branch); reviewed each file | Sajal Ishtiaq |
| 4 | 24-11-26 | Claude | OpenAPI spec + generator + generated tests | `api-spec/openapi.yaml`, `tools/gen_test_data.py`, `test_generated.py` | Regenerated with changed constraints (`scripts/demo_regen.sh`) | Sajal Ishtiaq |
| 5 | 24-11-26 | Claude | Mutation analysis + custom operators | mutmut config, `tools/custom_mutation.py`, killer tests, analysis of 66 survivors | Re-ran; read every survivor diff; confirmed 4 equivalent mutants | Saliha Noor |
| 6 | 27-11-26 | Claude | CI workflow, Sonar setup, perf and recovery scripts | YAML, scripts, k6 workload, recovery tests | CI/Sonar/ZAP/Playwright **must be run by the team** (not executed by the AI); results pasted from your runs | Sajal Ishtiaq |
| 7 | 27-11-26 | Claude | Documentation drafts | Test plan, risk register, defect log + RCA, security assessment | Edit numbers/names, verify against your own evidence | Saliha Noor |
| 8 |  27-11-26 | Claude (Anthropic) | CI debugging | Diagnosis of the mutation failure (exit 126); a step that prints the Sonar gate details; suggested scoping Sonar coverage and ignoring S4502 for one file | Ran the pipeline ourselves and read the real gate output; checked the source (no cookies, bearer-token header) before accepting S4502 as not applicable; all three jobs green on our PR | Sajal Ishtiaq |
| 9 | 27-11-26 | Claude (Anthropic) | Environment setup troubleshooting | Fixes for WSL line endings, Windows npm vs Linux Node, git file modes, fork and branch setup | Applied each fix and confirmed the app runs and tests pass | Sajal Ishtiaq |
| 10 | 27-11-26 | Claude (Anthropic) | Planning and brief analysis | Phase plan and ownership split from the project brief and the teacher's announcement | Compared the plan with the brief | Sajal Ishtiaq |

## Things the AI found that you must be able to explain
* DEF-001 (OverflowError -> 500) was found while writing boundary tests; DEF-009 (race in `balance_for`) was found from k6 server logs at 5 users.
* Equivalent mutants: why `ApiError(msg)` vs `ApiError(msg, 400)` cannot be killed.
* Why the tests freeze "today" (2027-03-10) and why unit tests use fast password hashing.

## Limits of AI use (state in the report)
AI output can be wrong or untested; the items marked "not executed by the AI" were not run in its environment (Playwright browsers, Lighthouse, ZAP, SonarQube, GitHub Actions, Docker). Every number in the final PDF must come from a run you did or re-ran.
