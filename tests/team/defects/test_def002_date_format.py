"""DEF-002 (low): Validator.date() accepts non-YYYY-MM-DD input such as 20270315 or 2027-W11-1.

Cause: date.fromisoformat() on Python >= 3.11 accepts ISO basic/week formats and the
value is passed through str(), so integers are accepted too.
Expected: 422 "must use the YYYY-MM-DD format".  Actual: 201 Created.
Status: OPEN (xfail strict). Fix: validate with a regex ^\\d{4}-\\d{2}-\\d{2}$ and isinstance(str).
"""
import pytest

from .. import helpers as h

pytestmark = pytest.mark.xfail(strict=True, reason="DEF-002 open: non-extended ISO dates accepted")


@pytest.mark.parametrize("value", [20270315, "20270315", "2027-W11-1"])
def test_non_standard_date_formats_rejected(client, employee, auth, value):
    body = h.payload()
    body["start_date"] = value
    body["end_date"] = value
    res = client.post("/api/leave-requests", json=body, headers=auth(employee))
    assert res.status_code == 422
