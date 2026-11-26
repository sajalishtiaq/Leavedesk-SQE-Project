#!/bin/bash
# Creates a branch that breaks the balance rule so the pipeline BLOCKS the pull request.
set -e
cd "$(dirname "$0")/.."
git checkout -b demo/blocked-balance-rule
sed -i '0,/balance.remaining_days < days/s//balance.remaining_days <= days/' backend/app/services.py
git diff --stat
git commit -am "demo: off-by-one in balance rule (must be blocked by CI)"
echo "Now: git push -u origin demo/blocked-balance-rule, open a PR, and KEEP IT OPEN with the red checks (screenshot for the report)."
