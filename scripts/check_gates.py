#!/usr/bin/env python3
"""Quality-gate thresholds. Exits non-zero (fails the CI job) when a measured value is below threshold.

Usage: python scripts/check_gates.py coverage|mutation
Thresholds (justified in docs/team/06-ci-quality-gate.md):
  branch+statement coverage of business logic  >= 100 %   (assignment target for server-side business logic)
  mutmut score                                  >= 95  %   (98.9 % measured; 4 equivalent mutants cap the max at 98.9 %)
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THRESHOLDS = {"coverage": 100.0, "mutation": 95.0}


def coverage_value():
    out = subprocess.run([sys.executable, "-m", "coverage", "report"], cwd=ROOT, capture_output=True, text=True).stdout
    print(out)
    m = re.search(r"TOTAL\s+\d+\s+\d+\s+\d+\s+\d+\s+(\d+(?:\.\d+)?)%", out)
    if not m:
        sys.exit("could not read coverage total")
    return float(m.group(1))


def mutation_value():
    text = (ROOT / "docs/team/evidence/mutmut_summary.txt").read_text()
    print(text)
    m = re.search(r"score=(\d+(?:\.\d+)?)%", text)
    if not m:
        sys.exit("could not read mutation score")
    return float(m.group(1))


def main():
    kind = sys.argv[1]
    value = {"coverage": coverage_value, "mutation": mutation_value}[kind]()
    limit = THRESHOLDS[kind]
    print(f"{kind}: {value:.1f}% (threshold {limit:.1f}%)")
    if value < limit:
        sys.exit(f"GATE FAILED: {kind} {value:.1f}% < {limit:.1f}%")


if __name__ == "__main__":
    main()
