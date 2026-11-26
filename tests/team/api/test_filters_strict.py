"""Added after custom-mutation analysis (OWNER / STATUS survivors): stricter list-filter tests."""
import pytest

from .. import helpers as h

pytestmark = pytest.mark.api


@pytest.mark.parametrize("status", ["pending", "approved", "rejected", "cancelled"])
def test_every_allowed_status_filter_returns_only_that_status(client, employee, auth, make_request, status):
    days = {"pending": h.MON, "approved": h.TUE, "rejected": h.WED, "cancelled": h.THU}
    for st, day in days.items():
        make_request(employee, day, day, status=st)
    res = client.get(f"/api/leave-requests?status={status}", headers=auth(employee))
    body = res.get_json()
    assert res.status_code == 200 and body["total"] == 1
    assert body["items"][0]["status"] == status


def test_admin_user_id_filter_excludes_other_users(client, employee, other_employee, admin, auth, make_request):
    make_request(employee, h.MON, h.MON)
    make_request(employee, h.TUE, h.TUE)
    make_request(other_employee, h.WED, h.WED)
    make_request(other_employee, h.THU, h.THU)
    make_request(other_employee, h.FRI, h.FRI)
    body = client.get(f"/api/leave-requests?user_id={employee.id}", headers=auth(admin)).get_json()
    assert body["total"] == 2 and {i["employee"]["id"] for i in body["items"]} == {employee.id}


def test_department_filter_excludes_other_departments(client, employee, other_employee, admin, auth, make_request):
    make_request(employee, h.MON, h.MON)                  # Engineering
    make_request(employee, h.TUE, h.TUE)
    make_request(other_employee, h.WED, h.WED)            # Finance
    body = client.get("/api/leave-requests?department=Finance", headers=auth(admin)).get_json()
    assert body["total"] == 1 and body["items"][0]["employee"]["id"] == other_employee.id
    body = client.get("/api/leave-requests?department=Engineering", headers=auth(admin)).get_json()
    assert body["total"] == 2


def test_admin_search_by_name_excludes_other_users(client, make_user, admin, auth, make_request):
    a, b = make_user("employee", name="Zainab Alpha"), make_user("employee", name="Bilal Beta")
    make_request(a, h.MON, h.MON)
    make_request(a, h.TUE, h.TUE)
    make_request(b, h.WED, h.WED)
    body = client.get("/api/leave-requests?q=Zainab", headers=auth(admin)).get_json()
    assert body["total"] == 2 and {i["employee"]["id"] for i in body["items"]} == {a.id}
