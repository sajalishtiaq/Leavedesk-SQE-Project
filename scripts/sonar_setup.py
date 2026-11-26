#!/usr/bin/env python3
"""Prepare a fresh SonarQube (Community) for CI or local use.

 - waits until the server is UP
 - creates the project, a custom quality gate and assigns it
 - generates an analysis token and exports it (GITHUB_ENV in CI, otherwise printed)

Gate conditions (justified in docs/team/06-ci-quality-gate.md):
  coverage < 85 %  | duplicated_lines_density > 3 % | bugs > 0 | vulnerabilities > 0
  | security_rating worse than A | reliability_rating worse than A
Usage: python scripts/sonar_setup.py http://localhost:9000   (admin password from SONAR_ADMIN_PASSWORD, default admin)
"""
import os
import sys
import time

import requests

URL = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:9000"
AUTH = ("admin", os.environ.get("SONAR_ADMIN_PASSWORD", "admin"))
KEY, GATE = "leavedesk-sqe", "leavedesk-gate"
CONDITIONS = [("coverage", "LT", "85"), ("duplicated_lines_density", "GT", "3"), ("bugs", "GT", "0"),
              ("vulnerabilities", "GT", "0"), ("security_rating", "GT", "1"), ("reliability_rating", "GT", "1")]


def call(method, path, **data):
    r = requests.request(method, URL + path, auth=AUTH, data=data, timeout=60)
    if r.status_code >= 400 and "already exists" not in r.text:
        sys.exit(f"{method} {path} failed: {r.status_code} {r.text}")
    return r


for _ in range(60):
    try:
        if requests.get(URL + "/api/system/status", timeout=5).json().get("status") == "UP":
            break
    except Exception:
        pass
    time.sleep(5)
else:
    sys.exit("SonarQube did not become UP")

call("POST", "/api/projects/create", project=KEY, name="LeaveDesk SQE")
call("POST", "/api/qualitygates/create", name=GATE)
for metric, op, error in CONDITIONS:
    call("POST", "/api/qualitygates/create_condition", gateName=GATE, metric=metric, op=op, error=error)
call("POST", "/api/qualitygates/select", gateName=GATE, projectKey=KEY)
token = call("POST", "/api/user_tokens/generate", name=f"ci-{int(time.time())}").json()["token"]

if os.environ.get("GITHUB_ENV"):
    with open(os.environ["GITHUB_ENV"], "a") as fh:
        fh.write(f"SONAR_TOKEN={token}\n")
    print("SONAR_TOKEN exported to GITHUB_ENV")
else:
    print("SONAR_TOKEN=" + token)
