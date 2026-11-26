#!/bin/bash
# Viva demo: change two spec constraints, regenerate test data, show the effect on the tests.
#   1) reason.minLength 10 -> 20      2) leave_type_id.maximum 3 -> 5
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
TMP=/tmp/regen_demo; rm -rf "$TMP"; mkdir -p "$TMP"
sed -e 's/minLength: 10/minLength: 20/' -e 's/maximum: 3,/maximum: 5,/' api-spec/openapi.yaml > "$TMP/openapi.yaml"
python tools/gen_test_data.py --spec "$TMP/openapi.yaml" --out "$TMP/cases.json"
python - <<'PY'
import json
old = json.load(open("tests/team/api/generated/cases.json"))["cases"]
new = json.load(open("/tmp/regen_demo/cases.json"))["cases"]
key = lambda c: (c["endpoint"], c["field"], c["class"])
o = {key(c): c for c in old}
print("\nChanged generated values (old -> new):")
for c in new:
    k = key(c)
    if k in o and (o[k]["value"] != c["value"] or o[k]["valid"] != c["valid"]):
        f = lambda x: repr(x["value"])[:14] + ("..." if len(repr(x["value"])) > 14 else "")
        print(f"  {c['field']:14} {c['class']:20} {f(o[k]):18}valid={o[k]['valid']!s:5} -> {f(c):18}valid={c['valid']}")
PY
echo; echo "Running API tests against the UNCHANGED app with the regenerated data (expect failures = effect):"
CASES_FILE="$TMP/cases.json" python -m pytest tests/team/api/test_generated.py -q -p no:cacheprovider 2>&1 | tail -8
