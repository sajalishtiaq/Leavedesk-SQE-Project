"""API tests for read endpoints that share the records: detail, balances, listing, auth, roles."""
import pytest

from app.extensions import db
from app.models import User

from .. import helpers as h

pytestmark = pytest.mark.api


# ---- GET /leave-requests/<id> : visibility ------------------------------------
def test_owner_admin_can_view_but_other_employee_gets_404(client, employee, other_employee, admin, auth, make_request):
    item = make_request(employee)
    url = f"/api/leave-requests/{item.id}"
    assert client.get(url, headers=auth(employee)).status_code == 200
    assert client.get(url, headers=auth(admin)).status_code == 200
    assert client.get(url, headers=auth(other_employee)).status_code == 404   # hidden, not 403
    assert client.get("/api/leave-requests/424242", headers=auth(admin)).status_code == 404


# ---- GET /leave-balances (shared record) -------------------------------------
def test_balances_default_year_and_three_types(client, employee, auth):
    res = client.get("/api/leave-balances", headers=auth(employee))
    body = res.get_json()
    assert res.status_code == 200 and body["year"] == 2027 and len(body["balances"]) == 3


def test_balances_explicit_year_creates_defaults(client, employee, auth):
    body = client.get("/api/leave-balances?year=2030", headers=auth(employee)).get_json()
    assert body["year"] == 2030 and body["balances"][0]["used_days"] == 0


def test_balances_reflect_approval(client, employee, admin, auth, make_request):
    item = make_request(employee, h.MON, h.WED, days=3)
    client.post(f"/api/leave-requests/{item.id}/review", json={"decision": "approve"}, headers=auth(admin))
    body = client.get("/api/leave-balances", headers=auth(employee)).get_json()
    casual = body["balances"][0]
    assert (casual["used_days"], casual["remaining_days"]) == (3, 9)


@pytest.mark.parametrize("qs", ["?year=abc", "?user_id=abc"])
def test_balances_invalid_params(client, admin, auth, qs):
    assert client.get("/api/leave-balances" + qs, headers=auth(admin)).status_code == 400


def test_balances_user_id_permissions(client, employee, other_employee, admin, auth):
    own = f"/api/leave-balances?user_id={employee.id}"
    other = f"/api/leave-balances?user_id={other_employee.id}"
    assert client.get(own, headers=auth(employee)).status_code == 200       # own id allowed
    assert client.get(other, headers=auth(employee)).status_code == 403     # denied
    assert client.get(other, headers=auth(admin)).status_code == 200        # admin allowed
    assert client.get("/api/leave-balances?user_id=99999", headers=auth(admin)).status_code == 404


def test_leave_types_endpoint(client, employee, auth):
    body = client.get("/api/leave-types", headers=auth(employee)).get_json()
    assert [t["code"] for t in body["leave_types"]] == ["CASUAL", "SICK", "EARNED"]


# ---- GET /leave-requests (list/filter/page) ----------------------------------
def test_employee_sees_only_own_requests(client, employee, other_employee, auth, make_request):
    make_request(employee)
    make_request(other_employee)
    assert client.get("/api/leave-requests", headers=auth(employee)).get_json()["total"] == 1


def test_admin_sees_all_requests(client, employee, other_employee, admin, auth, make_request):
    make_request(employee)
    make_request(other_employee)
    assert client.get("/api/leave-requests", headers=auth(admin)).get_json()["total"] == 2


def test_status_filter_valid_and_invalid(client, employee, auth, make_request):
    make_request(employee, status="pending")
    make_request(employee, h.TUE, h.TUE, status="approved")
    headers = auth(employee)
    assert client.get("/api/leave-requests?status=approved", headers=headers).get_json()["total"] == 1
    assert client.get("/api/leave-requests?status=bogus", headers=headers).status_code == 400


def test_admin_filters_user_department_type_year(client, employee, other_employee, admin, auth, make_request):
    make_request(employee, leave_type_id=1)
    make_request(other_employee, h.TUE, h.TUE, leave_type_id=2)
    headers = auth(admin)
    get = lambda qs: client.get("/api/leave-requests" + qs, headers=headers)
    assert get(f"?user_id={employee.id}").get_json()["total"] == 1
    assert get("?department=Finance").get_json()["total"] == 1
    assert get("?leave_type_id=2").get_json()["total"] == 1
    assert get("?year=2027").get_json()["total"] == 2
    assert get("?year=2031").get_json()["total"] == 0


@pytest.mark.parametrize("qs", ["?user_id=x", "?leave_type_id=x", "?year=x", "?page=x"])
def test_list_invalid_numeric_filters(client, admin, auth, qs):
    assert client.get("/api/leave-requests" + qs, headers=auth(admin)).status_code == 400


def test_employee_user_id_filter_is_ignored(client, employee, other_employee, auth, make_request):
    make_request(employee)
    make_request(other_employee)
    res = client.get(f"/api/leave-requests?user_id={other_employee.id}", headers=auth(employee))
    assert res.get_json()["total"] == 1             # still only their own


def test_search_employee_matches_reason_only(client, employee, auth, make_request):
    item = make_request(employee)
    item.reason = "dentist appointment"
    db.session.commit()
    headers = auth(employee)
    assert client.get("/api/leave-requests?q=dentist", headers=headers).get_json()["total"] == 1
    assert client.get("/api/leave-requests?q=zzz", headers=headers).get_json()["total"] == 0
    assert client.get(f"/api/leave-requests?q={employee.email}", headers=headers).get_json()["total"] == 0


def test_search_admin_matches_name_and_email(client, employee, admin, auth, make_request):
    make_request(employee)
    headers = auth(admin)
    assert client.get(f"/api/leave-requests?q={employee.name}", headers=headers).get_json()["total"] == 1
    assert client.get(f"/api/leave-requests?q={employee.email}", headers=headers).get_json()["total"] == 1


def test_pagination_metadata_and_clamp(client, employee, auth, make_request):
    for day in range(15, 20):
        make_request(employee, h.REAL_DATE(2027, 3, day), h.REAL_DATE(2027, 3, day))
    headers = auth(employee)
    body = client.get("/api/leave-requests?per_page=2&page=2", headers=headers).get_json()
    assert (body["page"], body["per_page"], body["total"], body["pages"]) == (2, 2, 5, 3)
    assert body["has_next"] and body["has_prev"] and len(body["items"]) == 2
    assert client.get("/api/leave-requests?per_page=500", headers=headers).get_json()["per_page"] == 50


# ---- authentication / authorization (access matrix at API level) -------------
def test_inactive_or_deleted_user_token_is_rejected(client, make_user, auth):
    user = make_user("employee")
    headers = auth(user)
    user.is_active = False
    db.session.commit()
    res = client.get("/api/leave-requests", headers=headers)
    assert res.status_code == 401 and "no longer exists" in res.get_json()["message"]


def test_missing_and_garbage_token(client):
    assert client.get("/api/leave-requests").status_code == 401
    res = client.get("/api/leave-requests", headers={"Authorization": "Bearer not.a.token"})
    assert res.status_code == 401


def test_admin_required_decorator_on_team_endpoint(client, employee, admin, auth):
    assert client.get("/api/team", headers=auth(employee)).status_code == 403
    assert client.get("/api/team", headers=auth(admin)).status_code == 200
    assert client.get("/api/team").status_code == 401
