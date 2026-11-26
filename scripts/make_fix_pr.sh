#!/bin/bash
# Creates the documented fix branch (fails before, passes after):  scripts/make_fix_pr.sh DEF-001   (or DEF-009)
# commit 1 = regression test enabled (CI red), commit 2 = the fix (CI green). Then push the branch and open a PR to main.
set -e
cd "$(dirname "$0")/.."
ID="${1:?usage: make_fix_pr.sh DEF-001|DEF-009}"
case "$ID" in
  DEF-001) TEST=tests/team/defects/test_def001_integer_overflow.py; PATCH=docs/team/fix-pr/DEF-001.patch; BR=fix/def-001-integer-overflow ;;
  DEF-009) TEST=tests/team/defects/test_def009_balance_race.py;     PATCH=docs/team/fix-pr/DEF-009.patch; BR=fix/def-009-balance-race ;;
  *) echo "unknown defect"; exit 1 ;;
esac
git checkout -b "$BR"
sed -i '/^pytestmark = pytest.mark.xfail/d' "$TEST"
git add "$TEST"
git commit -m "test: enable $ID regression test (red: reproduces the defect)"
git apply "$PATCH"
git add -A
git commit -m "fix: $ID (see docs/team/09-defect-log.md)"
echo "Now: git push -u origin $BR   and open a pull request. First commit's CI run = RED, last = GREEN."
