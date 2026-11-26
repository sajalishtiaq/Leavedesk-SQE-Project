"""DEF-001: Validator.integer() crashes (HTTP 500) on a JSON number that overflows to infinity.

Reproduction: POST /api/leave-requests with  "leave_type_id": 1e400
Expected: 422 validation error ("must be a whole number").
Actual (baseline): OverflowError -> HTTP 500.

Status: OPEN. Marked xfail(strict) so the suite stays green and the test flips to
a failure (XPASS) the moment the bug is fixed -> remove the marker in the fix PR.
Fix: app/utils.py -> `except (TypeError, ValueError, OverflowError):`
"""
import pytest

from app.utils import Validator

from .. import helpers as h

pytestmark = pytest.mark.xfail(strict=True, reason="DEF-001 open: OverflowError not handled")


def test_unit_integer_infinity_rejected_cleanly():
    val = Validator({"n": float("inf")})
    assert val.integer("n") is None
    assert "whole number" in val.errors["n"]


def test_api_overflowing_leave_type_id_returns_422(client, employee, auth):
    body = (
        '{"leave_type_id": 1e400, "start_date": "2027-03-15", '
        '"end_date": "2027-03-15", "reason": "' + h.GOOD_REASON + '"}'
    )
    res = client.post(
        "/api/leave-requests",
        data=body,
        content_type="application/json",
        headers=auth(employee),
    )
    assert res.status_code == 422
