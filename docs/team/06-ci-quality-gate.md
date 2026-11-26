# 06. CI Quality Gate (GitHub Actions: `.github/workflows/quality-gate.yml`)

Runs on every pull request to `main` (and pushes to `main`). Three jobs; **no `continue-on-error`, no `|| true`** anywhere
(checked by `grep -rn "continue-on-error\|\|\| true" .github scripts tools` - must print nothing).
| Job | What it does | Fails the PR when |
|---|---|---|
| `tests-and-coverage` | installs deps, runs all team tests under coverage, uploads `coverage.xml` | any test fails, or statement/branch coverage of the business-logic modules < 100 % |
| `mutation` | `scripts/run_mutation.sh` (mutmut) + `tools/custom_mutation.py` | mutmut score < 95 %, or any killable custom mutant survives |
| `sonarqube` | SonarQube Community in a service container, `scripts/sonar_setup.py` creates the quality gate, scan, gate check | gate conditions below fail |

## Thresholds and why (from our own evidence)
| Gate | Threshold | Evidence / justification |
|---|---|---|
| Coverage (business logic) | 100 % statement + branch | Assignment target; measured 344 statements / 122 branches at 100 %. Any drop means a rule path lost its test. |
| Mutmut score | >= 95 % | Measured 98.9 % (346/350); the 4 survivors are proven equivalent, so 98.9 % is the ceiling. 95 % leaves ~4 points of headroom for harmless new code while still failing when a rule's tests weaken (run 1 without the killer tests scored 81.1 %). |
| Custom operators | 0 killable survivors | 44/46 killed, 2 equivalent (`decision` max_length). Business-rule mutations should never survive. |
| Sonar coverage | >= 85 % | Whole `backend/app` (excluding `seed.py`) measures 89 %: auth/dashboard/startup code is only partly exercised by our workflow tests; 85 % keeps 4 points of margin. |
| Sonar duplication | <= 3 % | Standard Sonar default for new code; codebase is small. |
| Sonar bugs / vulnerabilities | 0 | Any new bug or vulnerability should block. |
| Sonar ratings | Security A, Reliability A | Same reasoning. |
Deployment: the workflow has no deploy job; enable **branch protection** on `main` requiring the three jobs, so a failing PR can neither merge nor deploy.

## One-time repository setup (you do this on GitHub)
1. Settings -> Branches -> add rule for `main`: *Require a pull request*, *Require status checks* (`tests-and-coverage`, `mutation`, `sonarqube`), *Include administrators*.
2. Push the repo; open PRs as below.

## Documented fix through a pull request (fails before, passes after)
`scripts/make_fix_pr.sh` creates branch `fix/def-001-integer-overflow`:
1. commit 1 - the regression test **without** xfail (`test_def001_integer_overflow.py`): CI is **red**.
2. commit 2 - the one-line fix in `app/utils.py` (`except (TypeError, ValueError, OverflowError)`): CI is **green**.
Open the PR, link both runs in the report (this proves fails-before / passes-after).

## Pull request blocked by the pipeline
`scripts/make_blocked_pr.sh` creates branch `demo/blocked-balance-rule` that changes the balance rule (`remaining_days < days` -> `<=`)
in `services.py`. Boundary tests fail, so `tests-and-coverage` fails and the PR cannot be merged. Keep the PR **open** and screenshot the red checks.
