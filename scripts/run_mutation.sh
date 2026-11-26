#!/bin/bash
# Runs mutmut on the business-rule modules in an isolated workspace.
# Usage: scripts/run_mutation.sh   (writes docs/team/evidence/mutmut_*.txt)
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WS="${MUT_WS:-/tmp/mutation_ws}"
rm -rf "$WS" && mkdir -p "$WS/tests" "$ROOT/docs/team/evidence"
cp -r "$ROOT/backend/app" "$WS/app"
cp -r "$ROOT/tests/team" "$WS/tests/team" && touch "$WS/tests/__init__.py"
find "$WS" -name __pycache__ -prune -exec rm -rf {} +
cat > "$WS/pytest.ini" <<'INI'
[pytest]
testpaths = tests/team
pythonpath = .
addopts = -q -p no:cacheprovider
INI
cat > "$WS/pyproject.toml" <<'TOML'
[tool.mutmut]
paths_to_mutate = ["app/services.py", "app/utils.py", "app/api/leaves.py"]
tests_dir = ["tests/team/"]
also_copy = ["app/", "pytest.ini", "tests/"]
TOML
cd "$WS"
# mutmut may exit non-zero when mutants survive; we judge the score ourselves below.
set +e
mutmut run --max-children "${JOBS:-4}" > "$WS/run.log" 2>&1
RUN_RC=$?
mutmut results --all true > "$ROOT/docs/team/evidence/mutmut_results.txt" 2>&1
set -e
if [ ! -s "$WS/run.log" ]; then echo "mutmut produced no output (rc=$RUN_RC)"; exit 1; fi
python3 - "$ROOT" "$WS/run.log" <<'PY'
import re, sys
root, log = sys.argv[1], sys.argv[2]
text = open(log, errors="replace").read()
m = re.findall(r"(\d+)/(\d+)\D+?(\d+)\D+?(\d+)\D+?(\d+)\D+?(\d+)\D+?(\d+)\D+?(\d+)\D+?(\d+)", text)
done, total, killed, nocov, timeout, suspicious, survived, skipped, _ = map(int, m[-1])
score = 100 * (killed + timeout) / max(killed + timeout + survived + suspicious, 1)
out = f"mutmut: total={total} killed={killed} survived={survived} timeout={timeout} suspicious={suspicious} score={score:.1f}%"
print(out)
open(f"{root}/docs/team/evidence/mutmut_summary.txt", "w").write(out + "\n")
PY
