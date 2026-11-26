#!/bin/bash
# OWASP ZAP in PASSIVE mode while the Playwright tests drive BOTH workflows. No active scanning/attacks.
# Needs Docker, the app running (backend :5001, frontend :5173) and e2e deps installed (cd e2e && npm install && npm run install-browsers).
set -e
cd "$(dirname "$0")/.."
OUT=docs/team/evidence/security; mkdir -p "$OUT"
docker rm -f zap >/dev/null 2>&1
docker run -d --name zap --network host zaproxy/zap-stable zap.sh -daemon -host 127.0.0.1 -port 8090 \
  -config api.disablekey=true -config scanner.attackOnStart=false >/dev/null
for i in $(seq 1 60); do curl -fs http://127.0.0.1:8090/JSON/core/view/version >/dev/null && break; sleep 2; done
(cd e2e && PW_PROXY=http://127.0.0.1:8090 npx playwright test tests/uc1-apply.spec.ts tests/uc2-review.spec.ts tests/access.spec.ts)
for i in $(seq 1 60); do                                     # wait until the passive scanner queue is empty
  [ "$(curl -s http://127.0.0.1:8090/JSON/pscan/view/recordsToScan | python3 -c 'import sys,json;print(json.load(sys.stdin)["recordsToScan"])')" = "0" ] && break; sleep 2; done
curl -s "http://127.0.0.1:8090/JSON/core/view/alerts?baseurl=http://localhost" > "$OUT/zap_alerts.json"
curl -s "http://127.0.0.1:8090/OTHER/core/other/htmlreport/" > "$OUT/zap_report.html"
docker rm -f zap >/dev/null
python3 - <<'PY'
import json, collections
alerts = json.load(open("docs/team/evidence/security/zap_alerts.json")).get("alerts", [])
by = collections.Counter((a["risk"], a["alert"]) for a in alerts)
for (risk, name), n in sorted(by.items()):
    print(f"{risk:14} {name}  x{n}")
PY
