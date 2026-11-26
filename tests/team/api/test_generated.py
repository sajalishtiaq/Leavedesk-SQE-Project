"""API tests driven ONLY by the generator output (tests/team/api/generated/cases.json).

Regenerate with:  python tools/gen_test_data.py
Each case changes exactly ONE field of an otherwise valid request (one invalid value per test).
"""
import json
import os
from pathlib import Path

import pytest

from .. import helpers as h

pytestmark = pytest.mark.api
CASES_FILE = os.environ.get("CASES_FILE", str(Path(__file__).parent / "generated" / "cases.json"))
DATA = json.loads(Path(CASES_FILE).read_text())
CASES = DATA["cases"]
INVALID_STATUS = {"applyLeave": 422, "reviewLeave": 422, "listLeave": 400, "getBalances": 400}
SUCCESS_STATUS = {"applyLeave": 201, "reviewLeave": 200, "listLeave": 200, "getBalances": 200}
MISSING = "__MISSING__"


def base_body(endpoint):
    if endpoint == "applyLeave":
        return {"leave_type_id": 1, "start_date": "2027-03-15", "end_date": "2027-03-15",
                "reason": "Family function out of town"}
    if endpoint == "reviewLeave":
        return {"decision": "approve", "note": "ok then"}
    return {}


def expected_status(case):
    if case["valid"]:
        return SUCCESS_STATUS[case["endpoint"]]
    if isinstance(case["expected_status"], int):
        return case["expected_status"]
    return INVALID_STATUS[case["endpoint"]]


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_generated_case(case, client, employee, admin, auth, make_request, read_balance):
    ep, loc, field, value = case["endpoint"], case["location"], case["field"], case["value"]
    body, query = base_body(ep), {}
    target = body if loc == "body" else query
    if value == MISSING:
        target.pop(field, None)
    else:
        target[field] = value

    if ep == "applyLeave":
        res = client.post("/api/leave-requests", json=body, headers=auth(employee))
    elif ep == "reviewLeave":
        item = make_request(employee, h.MON, h.WED, days=3)
        res = client.post(f"/api/leave-requests/{item.id}/review", json=body, headers=auth(admin))
    elif ep == "listLeave":
        res = client.get("/api/leave-requests", query_string=query, headers=auth(employee))
    else:  # getBalances: valid user_id is the caller's own id
        if field == "user_id" and case["valid"]:
            query["user_id"] = employee.id
        res = client.get("/api/leave-balances", query_string=query, headers=auth(employee))

    assert res.status_code == expected_status(case), (case["id"], res.get_json())

    # read-back of the shared record after success / rejection
    if ep in ("applyLeave", "reviewLeave"):
        used = read_balance(employee)
        if ep == "applyLeave":
            assert used in (None, 0)                     # apply never consumes balance
        else:
            assert used == 3 if res.status_code == 200 else used in (None, 0)

    # clamped paging values: assert the effective value
    if case["clamp"] and case["valid"] and field == "per_page":
        assert res.get_json()["per_page"] == min(max(int(value), 1), 50)
    if case["clamp"] and case["valid"] and field == "page":
        assert res.get_json()["page"] == max(int(value), 1)
