# 11. Static Analysis (SonarQube) and Cyclomatic Complexity

## 11.1 Running SonarQube locally
```bash
docker run -d --name sonarqube -p 9000:9000 sonarqube:community      # wait until http://localhost:9000 is UP
python scripts/sonar_setup.py http://localhost:9000                    # creates project, gate, prints SONAR_TOKEN
python -m coverage run -m pytest && python -m coverage xml -o coverage.xml
docker run --rm --network host -e SONAR_HOST_URL=http://localhost:9000 -e SONAR_TOKEN=<token> \
   -v "$PWD:/usr/src" sonarsource/sonar-scanner-cli                    # uses sonar-project.properties
```
Record in the report (screenshots of the dashboard): **Complexity, Duplications, Code smells, Bugs, Vulnerabilities, Security hotspots,
Coverage, Technical debt (SQALE), Reliability / Security / Maintainability ratings**, and explain each:
| Metric | What it tells us | Why it matters for LeaveDesk |
|---|---|---|
| Cyclomatic / cognitive complexity | Number of independent paths / how hard code is to read | Drives the number of tests needed; `list_leave_requests` (CC 14) and `validate_leave_window` (CC 10) are the hot spots |
| Duplication | Copy-pasted blocks | Repeated validation code multiplies fixes |
| Code smells / technical debt | Maintainability issues and the estimated fix time | Cost of future change |
| Bugs / vulnerabilities / hotspots | Likely defects and security-sensitive code | Expect hotspots on hard-coded secret, `debug=True` (DEF-003/004) |
| Coverage | Lines/branches executed by tests | We measure 100 % on business logic, 89 % whole app |
| Ratings (A-E) | Summary per dimension | Basis of the quality gate |
Radon (independent tool, measured here): average complexity A (3.9) over 30 blocks; highest `list_leave_requests` C (14), `validate_leave_window` B (10), `review_leave_request` B (10).

## 11.2 Hand-calculated cyclomatic complexity - `validate_leave_window` (services.py lines 66-97)
Decision nodes (each `if`/`elif` and each short-circuit operand of `and`):
| # | Predicate |
|---|---|
| 1 | `end < start` |
| 2 | `start.year != end.year` (elif) |
| 3 | `start < date.today()` (elif) |
| 4 | `not errors` (before working_days) |
| 5 | `days == 0` |
| 6 | `not errors` (first operand of `and`) |
| 7 | `overlapping_request(...)` (second operand of `and`) |
| 8 | `not errors` (before balance) |
| 9 | `balance.remaining_days < days` |

**V(G) = P + 1 = 9 + 1 = 10.**
Control-flow graph check: nodes N = 21 (entry, 9 decision nodes, 9 action nodes for the error/compute statements, a join node, return), edges E = 29, one connected component:
**V(G) = E - N + 2 = 29 - 21 + 2 = 10.**
| Tool | Value |
|---|---|
| Hand calculation | 10 |
| radon (measured) | 10 (rank B) |
| SonarQube | run it and fill in (expected 10: Sonar's Python rule counts `if`, `elif`, `and`) |
Interpretation: 10 independent paths -> at least 10 test cases for basis-path coverage; our unit tests contain 14 targeted cases (`test_validate_*`) so every path is covered.
