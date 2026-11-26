#!/usr/bin/env python3
"""Reads k6 summary JSONs and writes the comparison table against the limits."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "docs/team/evidence/perf"
P95_LIMIT, FAIL_LIMIT = 500.0, 1.0
rows = ["| VUs | Run | p95 (ms) | Requests/s | Unexpected failures % | Verdict |", "|---|---|---|---|---|---|"]
for vus in (1, 5):
    for run in (1, 2):
        f = OUT / f"vus{vus}_run{run}.json"
        if not f.exists():
            continue
        m = json.loads(f.read_text())["metrics"]
        p95 = m["http_req_duration{phase:measure}"]["values"]["p(95)"]
        rate = m["http_reqs{phase:measure}"]["values"]["rate"]
        fail = m["unexpected_failures{phase:measure}"]["values"]["rate"] * 100
        ok = p95 <= P95_LIMIT and fail < FAIL_LIMIT
        rows.append(f"| {vus} | {run} | {p95:.1f} | {rate:.1f} | {fail:.2f} | {'PASS' if ok else 'FAIL'} |")
text = "\n".join(rows)
(OUT / "results_table.md").write_text(text + "\n")
print(text)
