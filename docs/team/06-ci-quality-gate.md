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
| Sonar coverage | >= 85 % | Measured on our declared scope (services.py, utils.py, api/leaves.py): 100.0 % in our run https://github.com/sajalishtiaq/Leavedesk-SQE-Project/actions/runs/45997685665. Files outside that scope (models, auth, dashboard, config, extensions, __init__, seed) are excluded from the coverage figure with `sonar.coverage.exclusions`, but are still analysed for bugs, vulnerabilities and smells. The brief sets the coverage target for server-side business logic of the selected workflows, so Sonar's coverage scope matches it. |
| Sonar duplication | <= 3 % | Standard Sonar default for new code; codebase is small. |
| Sonar bugs / vulnerabilities | 0 | Any new bug or vulnerability should block the merge. One rule is deliberately ignored for one file (S4502 CSRF in `__init__.py`, see "What failed and how we fixed it"). |
| Sonar ratings | Security A, Reliability A | Same reasoning. |
Deployment: the workflow has no deploy job; enable **branch protection** on `main` requiring the three jobs, so a failing PR can neither merge nor deploy.

## What failed and how we fixed it (our runs on PR #1 and follow-ups)

**1. mutation job failed after 14 seconds, exit code 126.**
Exit code 126 means the shell found the file but could not execute it. `scripts/run_mutation.sh`
had no executable bit in git: our clone is on `/mnt/c` under WSL with `core.fileMode=false`, so `chmod +x` was never
recorded. Fix: `git update-index --chmod=+x scripts/*.sh` (`git ls-files -s` now shows mode 100755).
After this the job passed.

**2. sonarqube job failed at "Enforce Sonar quality gate".**
The log only said "Quality Gate has FAILED" and pointed to a dashboard on `localhost:9000`, which
is the temporary SonarQube server inside the job and disappears when the job ends, so the log gave no reason.
We added a step, "Show Sonar gate details" (`if: always()`, read-only), that prints the gate status, the measures
and the open issues from the Sonar API. We also upgraded `sonarqube-scan-action` from v5 to v6 after the
deprecation warning.

**3. What the gate details showed.**
Passed: coverage 100.0, bugs 0, duplicated lines 0.0, reliability rating A. Failed: vulnerabilities 1 (limit 0) and
security rating D (limit A). The issues were:
- `python:S4502` CRITICAL, `backend/app/__init__.py:11` (`Flask(__name__)`): "Make sure disabling CSRF protection is safe here."
- `python:S8786` MAJOR, `backend/app/utils.py:11` (`EMAIL_RE`): regular expression with super-linear backtracking.
  This is a code smell, not part of the gate.

**4. Decision on S4502 (CSRF).**
CSRF abuses cookies that the browser sends automatically. We checked the source:
no cookies are set in `backend/app`, the frontend sends the token in an `Authorization: Bearer` header
(`frontend/src/api/client.js`), and CORS uses `supports_credentials=False`. A browser does not attach such a header
on its own, so CSRF is not applicable here. Adding CSRF tokens would also break the JSON API. We ignored this one
rule for this one file with `sonar.issue.ignore.multicriteria` in `sonar-project.properties`. Any other vulnerability
still fails the gate. Related observation for the security section: the token is kept in `localStorage`, so an XSS
bug would expose it.

**5. Open finding S8786 (email regex).**
`[^@\s]+\.[^@\s]+` has two adjacent parts that both match dots, so input such as `a@` followed by many dots forces
repeated backtracking. Impact is limited because the email field is capped at 255 characters before the regex runs.
Not fixed. Residual risk: low.

**6. Result.**
All three jobs green (https://github.com/sajalishtiaq/Leavedesk-SQE-Project/actions/runs/45997685665). Evidence screenshots (taken by us): `docs/team/evidence/ci/-.

## Repository setup we did
Branch protection on `main` pull request required, status checks `tests-and-coverage`, `mutation`,
`sonarqube` required .

## Documented fix through a pull request (fails before, passes after)
`scripts/make_fix_pr.sh` creates branch `fix/def-001-integer-overflow`:
1. commit 1 - the regression test **without** xfail (`test_def001_integer_overflow.py`): CI is **red**.
2. commit 2 - the one-line fix in `app/utils.py` (`except (TypeError, ValueError, OverflowError)`): CI is **green**.
Open the PR, link both runs in the report (this proves fails-before / passes-after).

## Pull request blocked by the pipeline
`scripts/make_blocked_pr.sh` creates branch `demo/blocked-balance-rule` that changes the balance rule (`remaining_days < days` -> `<=`)
in `services.py`. Boundary tests fail, so `tests-and-coverage` fails and the PR cannot be merged. Keep the PR **open** and screenshot the red checks.
