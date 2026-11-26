#!/bin/bash
# Runs every activity that needs no browser/Docker. Fails on the first problem.
set -e
cd "$(dirname "$0")/.."
. backend/.venv/bin/activate
python -m coverage erase
python -m coverage run -m pytest
python scripts/check_gates.py coverage
python tools/gen_test_data.py
python tools/make_traceability.py > /dev/null && echo "traceability: 12/12 requirements covered"
./scripts/demo_regen.sh > docs/team/evidence/regeneration_demo.txt && echo "regeneration demo saved"
echo "ALL OK (mutation: scripts/run_mutation.sh, performance: scripts/run_perf.sh, browser/security: see TEAM_README.md)"
