#!/usr/bin/env python3
"""Fails if a custom-operator mutant survived that is not on the documented equivalent list."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Documented equivalent mutants (see docs/team/evidence/mutation_analysis.md)
EQUIVALENT = {"max_length=20 +1", "max_length=20 -1"}
results = json.loads((ROOT / "docs/team/evidence/custom_mutation_results.json").read_text())
bad = [r for r in results if r["status"] == "survived" and r["mutation"] not in EQUIVALENT]
for r in bad:
    print("SURVIVED:", r["file"], r["operator"], r["mutation"])
if bad:
    sys.exit(f"GATE FAILED: {len(bad)} killable custom mutant(s) survived")
print(f"custom mutation gate OK ({len(results)} mutants)")
