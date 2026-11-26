"""API tests - cancel (state change) + state-transition coverage."""
import pytest

from .. import helpers as h

pytestmark = pytest.mark.api


def cancel(client, headers, rid):
    return client.post(f"/api/leave-requests/{rid}/cancel", headers=headers)


# ---- decision table: owner (O) x cancellable status (S) x future start (F) ----
# O=F -> 403 ; O=T,S=F -> 409 ; O=T,S=T,F=F -> 409 ; all true -> 200
TABLE = [
    (False, False, False, 403), (False, False, True, 403),
    (False, True, False, 403), (False, True, True, 403),
    (True, False, False, 409), (True, False, True, 409),
    (True, True, False, 409), (True, True, True, 200),
]


@pytest.mark.parametrize("is_owner,cancellable,future,expected", TABLE)
def test_cancel_decision_table(client, make_user, auth, make_request, is_owner, cancellable, future, expected):
    owner = make_user("employee")
    caller = owner if is_owner else make_user("employee")
    day = h.TOMORROW if future else h.YESTERDAY
    item = make_request(owner, day, day, status="pending" if cancellable else "rejected")
    assert cancel(client, auth(caller), item.id).status_code == expected


@pytest.mark.parametrize("start,status", [(h.YESTERDAY, 409), (h.TODAY, 409), (h.TOMORROW, 200)])
def test_cancel_start_date_boundary(client, employee, auth, make_request, start, status):
    item = make_request(employee, start, start)
    assert cancel(client, auth(employee), item.id).status_code == status


def test_cancel_pending_does_not_change_balance(client, employee, auth, make_request, read_balance, read_status, set_balance):
    set_balance(employee, remaining=8)
    item = make_request(employee, h.MON, h.WED, days=3)
    assert cancel(client, auth(employee), item.id).status_code == 200
    assert read_status(item.id) == "cancelled"
    assert read_balance(employee) == 4               # unchanged (12-8)


def test_cancel_approved_restores_balance(client, employee, admin, auth, make_request, read_balance, read_status):
    item = make_request(employee, h.MON, h.WED, days=3)
    assert client.post(f"/api/leave-requests/{item.id}/review", json={"decision": "approve"}, headers=auth(admin)).status_code == 200
    assert read_balance(employee) == 3
    assert cancel(client, auth(employee), item.id).status_code == 200
    assert read_status(item.id) == "cancelled"
    assert read_balance(employee) == 0               # round trip: shared record restored


def test_cancel_approved_never_makes_balance_negative(client, employee, auth, make_request, set_balance, read_balance):
    set_balance(employee, remaining=12, used=1)      # inconsistent data: used < days
    item = make_request(employee, h.MON, h.FRI, status="approved", days=5)
    assert cancel(client, auth(employee), item.id).status_code == 200
    assert read_balance(employee) == 0


def test_cancel_twice_is_rejected_no_double_refund(client, employee, auth, make_request, set_balance, read_balance):
    set_balance(employee, remaining=9)               # used = 3
    item = make_request(employee, h.MON, h.WED, status="approved", days=3)
    headers = auth(employee)
    assert cancel(client, headers, item.id).status_code == 200
    assert cancel(client, headers, item.id).status_code == 409
    assert read_balance(employee) == 0


def test_cancel_unknown_request_404(client, employee, auth):
    assert cancel(client, auth(employee), 424242).status_code == 404


def test_cancel_requires_authentication(client, employee, make_request):
    item = make_request(employee)
    assert cancel(client, {}, item.id).status_code == 401


def test_admin_cannot_cancel_someone_elses_request(client, employee, admin, auth, make_request):
    item = make_request(employee, h.TOMORROW, h.TOMORROW)
    assert cancel(client, auth(admin), item.id).status_code == 403


# ---- state transition coverage (all allowed + >=1 disallowed from every state) ----
ALLOWED = [
    ("pending", "approve", 200), ("pending", "reject", 200), ("pending", "cancel", 200),
    ("approved", "cancel", 200),
]
DISALLOWED = [
    ("approved", "approve", 409), ("approved", "reject", 409),
    ("rejected", "approve", 409), ("rejected", "reject", 409), ("rejected", "cancel", 409),
    ("cancelled", "approve", 409), ("cancelled", "reject", 409), ("cancelled", "cancel", 409),
]


@pytest.mark.parametrize("state,action,expected", ALLOWED + DISALLOWED)
def test_state_transition_matrix(client, employee, admin, auth, make_request, read_status, state, action, expected):
    item = make_request(employee, h.TOMORROW, h.TOMORROW, status=state)
    if action == "cancel":
        res = cancel(client, auth(employee), item.id)
    else:
        res = client.post(
            f"/api/leave-requests/{item.id}/review",
            json={"decision": action, "note": "because"},
            headers=auth(admin),
        )
    assert res.status_code == expected
    target = {"approve": "approved", "reject": "rejected", "cancel": "cancelled"}[action]
    assert read_status(item.id) == (target if expected == 200 else state)
