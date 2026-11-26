"""API tests - Workflow 1: Apply for leave (POST /api/leave-requests). EP + 3-point BVA."""
import pytest

from .. import helpers as h

pytestmark = pytest.mark.api
URL = "/api/leave-requests"


def post(client, headers, body):
    return client.post(URL, json=body, headers=headers)


def test_apply_success_creates_pending_request(client, employee, auth, read_balance):
    res = post(client, auth(employee), h.payload(start=h.MON, end=h.FRI))
    assert res.status_code == 201
    body = res.get_json()
    assert (body["status"], body["days"]) == ("pending", 5)
    # shared record NOT changed by apply (only approval consumes balance)
    assert read_balance(employee) in (None, 0)


def test_apply_requires_authentication(client):
    res = client.post(URL, json=h.payload())
    assert res.status_code == 401


@pytest.mark.parametrize("body", [[1, 2], "text", 5])
def test_apply_body_must_be_json_object(client, employee, auth, body):
    assert client.post(URL, json=body, headers=auth(employee)).status_code == 400


def test_apply_non_json_body(client, employee, auth):
    res = client.post(URL, data="x", content_type="text/plain", headers=auth(employee))
    assert res.status_code == 400


# ---- leave_type_id: one invalid value per test -------------------------------
@pytest.mark.parametrize("value,status", [
    (None, 422), ("", 422), ("abc", 422), (True, 422), (0, 422), (-1, 422),
    (1, 201), (2, 201), (3, 201),
    (4, 404), (9999, 404),
])
def test_apply_leave_type_id_partitions(client, employee, auth, value, status):
    body = h.payload()
    if value is None:
        del body["leave_type_id"]
    else:
        body["leave_type_id"] = value
    assert post(client, auth(employee), body).status_code == status


# ---- dates --------------------------------------------------------------------
@pytest.mark.parametrize("field", ["start_date", "end_date"])
@pytest.mark.parametrize("value", [None, "", "2027/03/15", "15-03-2027", "2027-13-01", "2027-02-30"])
def test_apply_invalid_date_values(client, employee, auth, field, value):
    body = h.payload()
    if value is None:
        del body[field]
    else:
        body[field] = value
    res = post(client, auth(employee), body)
    assert res.status_code == 422 and field in res.get_json()["errors"]


def test_apply_end_before_start(client, employee, auth):
    res = post(client, auth(employee), h.payload(start=h.TUE, end=h.MON))
    assert res.status_code == 422 and "end_date" in res.get_json()["errors"]


@pytest.mark.parametrize("start,status", [(h.YESTERDAY, 422), (h.TODAY, 201), (h.TOMORROW, 201)])
def test_apply_start_date_boundary(client, employee, auth, start, status):
    assert post(client, auth(employee), h.payload(start=start, end=start)).status_code == status


@pytest.mark.parametrize("start,end,status", [
    (h.REAL_DATE(2027, 12, 30), h.REAL_DATE(2027, 12, 31), 201),   # below limit
    (h.REAL_DATE(2027, 12, 31), h.REAL_DATE(2027, 12, 31), 201),   # at limit
    (h.REAL_DATE(2027, 12, 31), h.REAL_DATE(2028, 1, 3), 422),     # above limit
])
def test_apply_calendar_year_boundary(client, employee, auth, start, end, status):
    assert post(client, auth(employee), h.payload(start=start, end=end)).status_code == status


def test_apply_weekend_only_rejected(client, employee, auth):
    res = post(client, auth(employee), h.payload(start=h.SAT, end=h.SUN))
    assert res.status_code == 422 and "end_date" in res.get_json()["errors"]


# ---- reason: BVA on min 10 / max 500 -----------------------------------------
@pytest.mark.parametrize("length,status", [
    (9, 422), (10, 201), (11, 201), (499, 201), (500, 201), (501, 422),
])
def test_apply_reason_length_boundaries(client, employee, auth, length, status):
    res = post(client, auth(employee), h.payload(reason="a" * length))
    assert res.status_code == status


@pytest.mark.parametrize("reason", [None, "", "          ", 12345])
def test_apply_reason_invalid_values(client, employee, auth, reason):
    body = h.payload()
    if reason is None:
        del body["reason"]
    else:
        body["reason"] = reason
    res = post(client, auth(employee), body)
    assert res.status_code == 422 and "reason" in res.get_json()["errors"]


# ---- balance boundary (3-point) & shared record read-back --------------------
@pytest.mark.parametrize("remaining,status", [(4, 422), (5, 201), (6, 201)])
def test_apply_balance_boundary(client, employee, auth, set_balance, remaining, status):
    set_balance(employee, remaining=remaining)
    res = post(client, auth(employee), h.payload(start=h.MON, end=h.FRI))   # 5 days
    assert res.status_code == status
    if status == 422:
        assert "leave_type_id" in res.get_json()["errors"]


def test_apply_rejection_leaves_shared_record_unchanged(client, employee, auth, set_balance, read_balance):
    set_balance(employee, remaining=2)
    before = read_balance(employee)
    post(client, auth(employee), h.payload(start=h.MON, end=h.FRI))
    assert read_balance(employee) == before


# ---- overlap + repeated request (no duplicates) ------------------------------
def test_apply_repeated_request_is_rejected_no_duplicate(client, employee, auth):
    headers = auth(employee)
    assert post(client, headers, h.payload(start=h.MON, end=h.WED)).status_code == 201
    second = post(client, headers, h.payload(start=h.MON, end=h.WED))
    assert second.status_code == 422 and "start_date" in second.get_json()["errors"]
    listing = client.get(URL, headers=headers).get_json()
    assert listing["total"] == 1


@pytest.mark.parametrize("start,end,status", [
    (h.THU, h.FRI, 201),     # day after existing end
    (h.WED, h.THU, 422),     # starts exactly on existing end
    (h.MON, h.MON, 422),     # one day inside
])
def test_apply_overlap_boundaries(client, employee, auth, make_request, start, end, status):
    make_request(employee, h.MON, h.WED, days=3)
    assert post(client, auth(employee), h.payload(start=start, end=end)).status_code == status


@pytest.mark.parametrize("old_status,status", [("rejected", 201), ("cancelled", 201), ("approved", 422), ("pending", 422)])
def test_apply_overlap_depends_on_existing_status(client, employee, auth, make_request, old_status, status):
    make_request(employee, h.MON, h.WED, status=old_status, days=3)
    assert post(client, auth(employee), h.payload(start=h.MON, end=h.WED)).status_code == status


def test_apply_overlap_is_per_employee(client, employee, other_employee, auth, make_request):
    make_request(other_employee, h.MON, h.WED, days=3)
    assert post(client, auth(employee), h.payload(start=h.MON, end=h.WED)).status_code == 201


def test_admin_can_apply_too(client, admin, auth):
    assert post(client, auth(admin), h.payload()).status_code == 201
