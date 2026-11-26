# 00. Environment and baseline
- Upstream: https://github.com/Vardhan32/leave-management-system (MIT)
- Baseline commit: b002faa4b46ba2090489c200c61787551591c70d (tag baseline-upstream)
- Fork: <your fork URL>
- OS: Windows + WSL2, Ubuntu 24.04.1 LTS
- Python 3.12.3, Node <from node --version>, npm <from npm --version>, git 2.43.0

## Commands
- Install: python3 -m venv .venv && source .venv/bin/activate && pip install -r backend/requirements.txt -r requirements-dev.txt
- Frontend install: cd frontend && npm ci
- Seed/reset: ./scripts/reset_db.sh
- Start API: cd backend && python run.py (port 5001)
- Start UI: cd frontend && npm run dev (port 5173)
- Tests: python -m pytest (326 passed, 6 xfailed)
- Coverage gate: python -m coverage run -m pytest && python scripts/check_gates.py coverage (100 %)

## Verified
2026-11-26 by Sajal Ishtiaq: tests, coverage gate, and the apply-then-approve flow in the browser.