#!/usr/bin/env python3
"""Automated test-data generator: reads the OpenAPI spec, emits EP classes and 3-point BVA values.

For every constrained input (request-body property or query/path parameter) it generates:
  EP  : one representative VALID class + one INVALID class per violated constraint
        (missing, wrong type, below min, above max, too short/long, bad enum, bad date format, ...)
        -> every invalid case changes exactly ONE field (one invalid value per test).
  BVA : 3-point values (just below, exactly at, just above) for every numeric limit, string-length
        limit and date lower bound.
Output: tests/team/api/generated/cases.json (consumed by tests/team/api/test_generated.py)

Usage: python tools/gen_test_data.py [--spec api-spec/openapi.yaml] [--out ...] [--today 2027-03-10]
"""
import argparse
import datetime as dt
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def resolve(spec, node):
    while isinstance(node, dict) and "$ref" in node:
        ref = node["$ref"].lstrip("#/").split("/")
        node = spec
        for part in ref:
            node = node[part]
    return node


def valid_value(name, schema, today):
    t = schema.get("type")
    if "enum" in schema:
        return schema["enum"][0]
    if t == "string" and schema.get("format") == "date":
        return (today + dt.timedelta(days=5)).isoformat()      # a Monday when today is a Wednesday
    if t == "string":
        lo, hi = schema.get("minLength", 1), schema.get("maxLength", 50)
        return "a" * min(max(lo + 5, lo), hi)
    if t == "integer":
        lo, hi = schema.get("minimum", 1), schema.get("maximum", 10**6)
        return min(max(lo, 1), hi)
    return None


def cases_for_field(endpoint, loc, name, schema, required, today):
    """Return list of case dicts for one field."""
    out = []
    t = schema.get("type")

    def add(tech, cls, value, valid, status=None, note=""):
        out.append({
            "endpoint": endpoint, "location": loc, "field": name, "technique": tech,
            "class": cls, "value": value, "valid": valid, "expected_status": status, "note": note,
            "clamp": bool(schema.get("x-clamp")),
        })

    # ---- EP ----
    add("EP", "valid", valid_value(name, schema, today), True)
    if required:
        add("EP", "missing", "__MISSING__", False, "422/400")
    if t == "integer":
        add("EP", "wrong_type_string", "abc", False)
        add("EP", "wrong_type_bool", True, False)
        if "minimum" in schema:
            add("EP", "below_minimum", schema["minimum"] - 1, bool(schema.get("x-clamp")))
    if t == "string" and "enum" in schema:
        add("EP", "not_in_enum", "zzz", False)
    if t == "string" and schema.get("format") == "date":
        add("EP", "bad_format", "15/03/2027", False)
        add("EP", "impossible_date", "2027-02-30", False)
        add("EP", "empty", "", False)
    if t == "string" and "enum" not in schema and schema.get("format") != "date":
        add("EP", "wrong_type_number", 12345, False)
        add("EP", "blank_whitespace", "   ", not required)

    # ---- 3-point BVA ----
    if t == "integer":
        for key, step in (("minimum", 1), ("maximum", 1)):
            if key in schema:
                lim = schema[key]
                for delta, lab in ((-step, "below"), (0, "at"), (step, "above")):
                    val = lim + delta
                    inside = (val >= schema.get("minimum", -10**9)) and (val <= schema.get("maximum", 10**9))
                    if schema.get("x-clamp"):
                        inside = True            # clamped, not rejected
                    add("BVA", f"{key}_{lab}", val, inside, None,
                        "x-above-max-status" if (not inside and key == "maximum") else "")
    if t == "string" and "enum" not in schema and schema.get("format") != "date":
        for key in ("minLength", "maxLength"):
            if key in schema:
                lim = schema[key]
                for delta, lab in ((-1, "below"), (0, "at"), (1, "above")):
                    n = lim + delta
                    inside = schema.get("minLength", 0) <= n <= schema.get("maxLength", 10**9)
                    if n >= 1:
                        add("BVA", f"{key}_{lab}", "a" * n, inside)
    if t == "string" and schema.get("format") == "date" and "x-min-days-from-today" in schema:
        base = today + dt.timedelta(days=schema["x-min-days-from-today"])
        for delta, lab in ((-1, "below"), (0, "at"), (1, "above")):
            d = base + dt.timedelta(days=delta)
            add("BVA", f"min_days_{lab}", d.isoformat(), delta >= 0, None, f"date={d.isoformat()}")
    if t == "string" and schema.get("format") == "date" and "x-min-field" in schema:
        base = today + dt.timedelta(days=5)      # equals the valid value of the referenced field
        for delta, lab in ((-1, "below"), (0, "at"), (1, "above")):
            d = base + dt.timedelta(days=delta)
            add("BVA", f"min_field_{lab}", d.isoformat(), delta >= 0, None, f">= {schema['x-min-field']}")
    return out


def generate(spec, today):
    cases = []
    for path, item in spec["paths"].items():
        for method, op in item.items():
            endpoint = op.get("operationId", f"{method} {path}")
            for p in op.get("parameters", []):
                if p["in"] == "path":
                    continue          # ids come from fixtures, not generated
                cases += cases_for_field(endpoint, p["in"], p["name"], p["schema"], p.get("required", False), today)
            body = op.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema")
            if body:
                body = resolve(spec, body)
                for name, schema in body.get("properties", {}).items():
                    cases += cases_for_field(endpoint, "body", name, schema, name in body.get("required", []), today)
    for i, c in enumerate(cases, 1):
        c["id"] = f"{c['endpoint']}-{c['field']}-{c['technique']}-{c['class']}-{i}"
        c["max_status_hint"] = None
    # attach x-above-max-status where spec defines it
    for path, item in spec["paths"].items():
        for method, op in item.items():
            body = op.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema")
            if body:
                for name, schema in resolve(spec, body).get("properties", {}).items():
                    if "x-above-max-status" in schema:
                        for c in cases:
                            if c["endpoint"] == op["operationId"] and c["field"] == name and c["class"] == "maximum_above":
                                c["expected_status"] = schema["x-above-max-status"]
    return cases


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default=str(ROOT / "api-spec" / "openapi.yaml"))
    ap.add_argument("--out", default=str(ROOT / "tests" / "team" / "api" / "generated" / "cases.json"))
    ap.add_argument("--today", default="2027-03-10")
    a = ap.parse_args()
    spec = yaml.safe_load(Path(a.spec).read_text())
    cases = generate(spec, dt.date.fromisoformat(a.today))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps({"spec": a.spec, "today": a.today, "cases": cases}, indent=1))
    ep = sum(c["technique"] == "EP" for c in cases)
    print(f"generated {len(cases)} cases (EP={ep}, BVA={len(cases)-ep}) -> {a.out}")


if __name__ == "__main__":
    main()
