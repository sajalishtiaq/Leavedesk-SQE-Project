# SQE Final Project - LeaveDesk (team work)
Upstream: https://github.com/Vardhan32/leave-management-system (MIT), baseline `b002faa4b46ba2090489c200c61787551591c70d` (tag `baseline-upstream`).
All team work lives in: `tests/team/`, `e2e/`, `tools/`, `scripts/`, `api-spec/`, `docs/team/`, `.github/workflows/quality-gate.yml`.

## Setup (once)
```bash
cd backend && python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt -r ../requirements-dev.txt && cd ..
```
## Everything that runs without a browser (one command)
```bash
./scripts/run_all.sh        # tests + coverage gate, traceability, regeneration demo
```
## Individual activities
| Activity | Command | Output |
|---|---|---|
| Reset DB | `scripts/reset_db.sh` | seeded `leave.db` |
| All tests | `python -m pytest` | 326 pass, 6 documented xfail (open defects) |
| Coverage gate | `python -m coverage run -m pytest && python scripts/check_gates.py coverage` | 100 % |
| Generate test data | `python tools/gen_test_data.py` | `tests/team/api/generated/cases.json` |
| Regeneration demo (viva) | `scripts/demo_regen.sh` | shows effect of 2 changed constraints |
| Mutation (mutmut) | `scripts/run_mutation.sh` then `python scripts/check_gates.py mutation` | `docs/team/evidence/mutmut_*` |
| Custom mutation | `python tools/custom_mutation.py` | `custom_mutation_*` |
| Traceability | `python tools/make_traceability.py` | `docs/team/04-traceability.md` |
| Performance (needs k6) | `K6=$(which k6) scripts/run_perf.sh` | `docs/team/evidence/perf/` |
| Browser E2E | `cd e2e && npm install && npm run install-browsers && npm test` | Playwright report |
| Accessibility | `npm run a11y:before`, fix, `npm run a11y:after`; `npm run lighthouse` | `evidence/a11y`, `evidence/lighthouse` |
| ZAP passive (Docker) | `scripts/zap_passive.sh` | `evidence/security/zap_alerts.json` |
| SonarQube (Docker) | see `docs/team/11-static-analysis.md` | dashboard screenshots |
| Dependency audit | `pip-audit -r backend/requirements.txt`; `cd frontend && npm audit` | `evidence/security` |
| GitHub issues | `scripts/create_issues.sh` | 9 issues |
| Fix PR / blocked PR | `scripts/make_fix_pr.sh DEF-001`, `scripts/make_blocked_pr.sh` | branches to push |
Windows: use WSL or Git Bash for the `.sh` scripts.

## Rules for the team
Every member commits their own work (commit history is checked). Do not use `continue-on-error` / `|| true`. Do not edit upstream tests.
