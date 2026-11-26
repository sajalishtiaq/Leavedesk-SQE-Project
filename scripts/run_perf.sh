#!/bin/bash
# Runs the k6 workload: 1 VU x2 and 5 VUs x2, each 10 s warm-up + 60 s measured. Same build/machine/seed data.
# Needs: k6 (set K6=/path/to/k6 if not on PATH). Output: docs/team/evidence/perf/
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
K6="${K6:-k6}"; OUT="$ROOT/docs/team/evidence/perf"; mkdir -p "$OUT"
. backend/.venv/bin/activate
{ echo "date: $(date -u +%FT%TZ)"; echo "k6: $($K6 version)"; python --version; uname -srm; nproc | sed 's/^/cpus: /';
  echo "git: $(git rev-parse --short HEAD)"; } > "$OUT/environment.txt"
for VUS in 1 5; do
  for RUN in 1 2; do
    if curl -fs localhost:5001/api/health >/dev/null; then echo "port 5001 already in use - stop the running server first"; exit 1; fi
    ./scripts/reset_db.sh >/dev/null 2>&1                         # identical starting data every run
    ( cd backend && exec flask --app run:app run -p 5001 --no-debugger --no-reload >/tmp/perf_server.log 2>&1 </dev/null ) &
    SERVER_PID=$!
    for i in $(seq 1 30); do curl -fs localhost:5001/api/health >/dev/null && break; sleep 1; done
    set +e
    VUS=$VUS OUT="$OUT/vus${VUS}_run${RUN}.json" $K6 run --quiet scripts/perf/apply_leave.js > "$OUT/vus${VUS}_run${RUN}.txt" 2>&1
    echo "vus=$VUS run=$RUN k6 exit code: $?" | tee -a "$OUT/exit_codes.txt"   # 99 = a limit was crossed (reported, not hidden)
    kill "$SERVER_PID"; wait "$SERVER_PID" 2>/dev/null      # server stopped by signal: non-zero status is expected
    set -e
    sleep 2
  done
done
python scripts/perf/summarize.py
