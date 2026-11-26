#!/usr/bin/env python3
"""Custom, business-rule-aware mutation operators for LeaveDesk (assignment: >= 2 custom operators).

Operators
  ROLE   : negate an `is_admin` role check            (breaks BR2 / access control)
  STATUS : replace a status literal with another one   (breaks the state machine, BR3)
  OWNER  : flip ownership comparison on `user_id`      (breaks BR2 "not own" / BR4 "owner")
  LIMIT  : +/-1 on rule limits (reason 10/500, note 500, per_page 50, weekday < 5)   (BR1)
  BALANCE: change the balance comparison (< -> <= / >) (breaks BR1 boundary)
  USED   : flip the sign of used_days updates          (breaks the shared record)

Usage:  python tools/custom_mutation.py   -> docs/team/evidence/custom_mutation_{results.json,summary.txt}
Each mutant is applied to a COPY of the code (/tmp/custom_ws), the full team suite is run, and
the mutant is 'killed' if any test fails, 'survived' otherwise.
"""
import ast
import copy
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WS = Path(os.environ.get("CUSTOM_WS", "/tmp/custom_ws"))
TARGETS = ["app/services.py", "app/utils.py", "app/api/leaves.py"]
STATUSES = ["pending", "approved", "rejected", "cancelled"]


def _src(node):
    return ast.unparse(node)


def sites(tree):
    """Yield (operator, description, node-index) for every mutation site."""
    out = []

    def dfs(n):  # same pre-order as Mutator.visit
        yield n
        for child in ast.iter_child_nodes(n):
            yield from dfs(child)

    for idx, node in enumerate(dfs(tree)):
        if isinstance(node, ast.Attribute) and node.attr == "is_admin":
            out.append(("ROLE", "negate is_admin", idx))
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in STATUSES:
            out.append(("STATUS", f"'{node.value}' -> '{STATUSES[(STATUSES.index(node.value)+1) % 4]}'", idx))
        elif isinstance(node, ast.Compare) and "user_id" in _src(node) and isinstance(node.ops[0], (ast.Eq, ast.NotEq)):
            out.append(("OWNER", f"flip == / != in `{_src(node)}`", idx))
        elif isinstance(node, ast.keyword) and node.arg in ("min_length", "max_length") and isinstance(node.value, ast.Constant):
            out.append(("LIMIT", f"{node.arg}={node.value.value} +1", idx))
            out.append(("LIMIT", f"{node.arg}={node.value.value} -1", idx + 0.5))
        elif isinstance(node, ast.Compare) and "weekday" in _src(node) and isinstance(node.comparators[0], ast.Constant):
            out.append(("LIMIT", "weekday() threshold +1", idx))
            out.append(("LIMIT", "weekday() threshold -1", idx + 0.5))
        elif isinstance(node, ast.Call) and getattr(node.func, "id", "") == "min" and any(
            isinstance(a, ast.Constant) and a.value == 50 for a in node.args
        ):
            out.append(("LIMIT", "per_page cap 50 +1", idx))
            out.append(("LIMIT", "per_page cap 50 -1", idx + 0.5))
        elif isinstance(node, ast.Compare) and "remaining_days" in _src(node.left) and isinstance(node.ops[0], ast.Lt):
            out.append(("BALANCE", f"`<` -> `<=` in `{_src(node)}`", idx))
            out.append(("BALANCE", f"`<` -> `>` in `{_src(node)}`", idx + 0.5))
        elif isinstance(node, ast.AugAssign) and "used_days" in _src(node.target):
            out.append(("USED", f"`{_src(node)}` sign flip", idx))
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Sub) and "used_days" in _src(node.left):
            out.append(("USED", f"`{_src(node)}` - -> +", idx))
    return out


class Mutator(ast.NodeTransformer):
    def __init__(self, target_idx, desc):
        self.target = target_idx
        self.desc = desc
        self.counter = -1
        self.done = False

    def visit(self, node):
        self.counter += 1
        here = self.counter
        node = self.generic_visit(node)
        key = int(self.target)
        half = self.target != key
        if here != key or self.done:
            return node
        self.done = True
        if isinstance(node, ast.Attribute) and node.attr == "is_admin":
            return ast.UnaryOp(op=ast.Not(), operand=node)
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            node.value = STATUSES[(STATUSES.index(node.value) + 1) % 4]
        elif isinstance(node, ast.Compare) and "user_id" in _src(node):
            node.ops[0] = ast.NotEq() if isinstance(node.ops[0], ast.Eq) else ast.Eq()
        elif isinstance(node, ast.keyword):
            node.value.value += -1 if half else 1
        elif isinstance(node, ast.Compare) and "weekday" in _src(node):
            node.comparators[0].value += -1 if half else 1
        elif isinstance(node, ast.Call):
            for a in node.args:
                if isinstance(a, ast.Constant) and a.value == 50:
                    a.value += -1 if half else 1
        elif isinstance(node, ast.Compare) and "remaining_days" in _src(node.left):
            node.ops[0] = ast.Gt() if half else ast.LtE()
        elif isinstance(node, ast.AugAssign):
            node.op = ast.Sub() if isinstance(node.op, ast.Add) else ast.Add()
        elif isinstance(node, ast.BinOp):
            node.op = ast.Add()
        return node


def run_tests():
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-x", "-q", "-p", "no:cacheprovider"],
        cwd=WS, capture_output=True, text=True, timeout=300,
    )
    return r.returncode


def main():
    if WS.exists():
        shutil.rmtree(WS)
    (WS / "tests").mkdir(parents=True)
    shutil.copytree(ROOT / "backend" / "app", WS / "app", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(ROOT / "tests" / "team", WS / "tests" / "team", ignore=shutil.ignore_patterns("__pycache__"))
    (WS / "tests" / "__init__.py").touch()
    (WS / "pytest.ini").write_text("[pytest]\ntestpaths = tests/team\npythonpath = .\n")
    assert run_tests() == 0, "baseline suite must be green before mutating"

    results = []
    for rel in TARGETS:
        path = WS / rel
        original = path.read_text()
        tree = ast.parse(original)
        for op, desc, idx in sites(tree):
            mutated = Mutator(idx, desc).visit(copy.deepcopy(tree))
            ast.fix_missing_locations(mutated)
            path.write_text(ast.unparse(mutated))
            killed = run_tests() != 0
            results.append({"file": rel, "operator": op, "mutation": desc, "status": "killed" if killed else "survived"})
            path.write_text(original)
            print(("KILLED  " if killed else "SURVIVED"), rel, op, desc, flush=True)

    evidence = ROOT / "docs" / "team" / "evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "custom_mutation_results.json").write_text(json.dumps(results, indent=2))
    by_op = {}
    for r in results:
        by_op.setdefault(r["operator"], [0, 0])[0 if r["status"] == "killed" else 1] += 1
    total = len(results)
    killed = sum(1 for r in results if r["status"] == "killed")
    lines = [f"custom operators: total={total} killed={killed} survived={total-killed} score={100*killed/max(total,1):.1f}%"]
    lines += [f"  {op}: killed={k} survived={s}" for op, (k, s) in sorted(by_op.items())]
    (evidence / "custom_mutation_summary.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
