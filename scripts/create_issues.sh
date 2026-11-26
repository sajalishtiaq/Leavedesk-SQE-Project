#!/bin/bash
# Creates the defect issues on GitHub (needs: gh auth login). Edit REPO if needed.
set -e
for l in "severity:major" "severity:minor" "severity:medium" "severity:trivial" "priority:high" "priority:medium" "priority:low" "status:open" "triage:fix-now" "triage:fix-before-release" "triage:later"; do
  gh label create "$l" --force >/dev/null 2>&1
done
new() { gh issue create --title "$1" --label "$2" --body "$3"; }
new "DEF-001 HTTP 500 on overflowing JSON number (leave_type_id: 1e400)" "severity:major,priority:high,status:open,triage:fix-now" "Validator.integer does not catch OverflowError. Test: tests/team/defects/test_def001_integer_overflow.py. Fix: docs/team/fix-pr/DEF-001.patch. Risk PR5."
new "DEF-002 Non-YYYY-MM-DD dates accepted (20270315, 2027-W11-1)" "severity:minor,priority:low,status:open,triage:later" "date.fromisoformat accepts ISO basic/week formats on Python 3.11+. Test: test_def002_date_format.py. Risk PR5."
new "DEF-003 Hard-coded fallback SECRET_KEY/JWT_SECRET_KEY" "severity:major,priority:high,status:open,triage:fix-before-release" "Anyone can forge an admin JWT if env vars are unset. app/config.py. Risk PR6 (SEC-1)."
new "DEF-004 run.py starts with debug=True" "severity:major,priority:high,status:open,triage:fix-before-release" "Interactive Werkzeug debugger exposed by documented start command. Risk PR6 (SEC-2)."
new "DEF-005 Apply allows start=today but cancel refuses start=today" "severity:minor,priority:low,status:open,triage:later" "'<' vs '<=' inconsistency (AS-2). Needs owner decision."
new "DEF-006 No throttling on /api/auth/login" "severity:medium,priority:medium,status:open,triage:later" "Online password guessing possible (SEC-3)."
new "DEF-007 Dead code utils.utc_timestamp" "severity:trivial,priority:low,status:open,triage:later" "Unused function (static analysis)."
new "DEF-008 react-router-dom vulnerable range" "severity:minor,priority:low,status:open,triage:later" "npm audit: 2 moderate advisories (SEC-6)."
new "DEF-009 HTTP 500 under concurrency: balance row get-or-create race" "severity:major,priority:high,status:open,triage:fix-before-release" "UNIQUE constraint failed on leave_balances when two requests create the same (user,type,year) row. Found by k6 (5 VUs, 18 x 500). Test: test_def009_balance_race.py. Fix: docs/team/fix-pr/DEF-009.patch. Risks PR1/PR9."
