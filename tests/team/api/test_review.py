"""API tests - Workflow 2: Review leave (POST /api/leave-requests/<id>/review)."""
import itertools

import pytest

from .. import helpers as h

pytestmark = pytest.mark.api


def review(client, headers, rid, decision="approve", note=None):
    body = {"decision": decision}
    if note is not None:
        body["note"] = note
    return client.post(f"/api/leave-requests/{rid}/review", json=body, headers=headers)


# ---- decision table: admin (A) x pending (B) x not-own (C) -------------------
# A=F -> 403 ; A=T,B=F -> 409 ; A=T,B=T,C=F -> 403 ; A=T,B=T,C=T -> 200
TABLE = [
    (False, False, False, 403), (False, False, True, 403),
    (False, True, False, 403), (False, True, True, 403),
    (True, False, False, 409), (True, False, True, 409),
    (True, True, False, 403), (True, True, True, 200),
]


@pytest.mark.parametrize("is_admin,is_pending,not_own,expected", TABLE)
def test_review_decision_table(client, make_user, auth, make_request, is_admin, is_pending, not_own, expected):
    reviewer = make_user("admin" if is_admin else "employee")
    owner = make_user("employee") if not_own else reviewer
    item = make_request(owner, status="pending" if is_pending else "approved")
    assert review(client, auth(reviewer), item.id).status_code == expected


# ---- state transitions through review ----------------------------------------
def test_pending_to_approved_updates_status_and_shared_balance(client, employee, admin, auth, make_request, read_balance, read_status):
    item = make_request(employee, h.MON, h.WED, days=3)
    res = review(client, auth(admin), item.id, "approve", "enjoy")
    assert res.status_code == 200
    body = res.get_json()
    assert (body["status"], body["review_note"]) == ("approved", "enjoy")
    assert read_status(item.id) == "approved"
    assert read_balance(employee) == 3                 # shared record increased


def test_pending_to_rejected_does_not_touch_balance(client, employee, admin, auth, make_request, read_balance, read_status):
    item = make_request(employee, h.MON, h.WED, days=3)
    res = review(client, auth(admin), item.id, "reject", "team is short staffed")
    assert res.status_code == 200 and res.get_json()["status"] == "rejected"
    assert read_status(item.id) == "rejected"
    assert read_balance(employee) in (None, 0)


@pytest.mark.parametrize("state", ["approved", "rejected", "cancelled"])
@pytest.mark.parametrize("decision", ["approve", "reject"])
def test_disallowed_review_from_final_states(client, employee, admin, auth, make_request, read_status, state, decision):
    item = make_request(employee, status=state)
    res = review(client, auth(admin), item.id, decision, "note here")
    assert res.status_code == 409
    assert read_status(item.id) == state             # unchanged


def test_repeated_approve_does_not_double_count(client, employee, admin, auth, make_request, read_balance):
    item = make_request(employee, h.MON, h.WED, days=3)
    headers = auth(admin)
    assert review(client, headers, item.id).status_code == 200
    assert review(client, headers, item.id).status_code == 409
    assert read_balance(employee) == 3


# ---- balance rule at approval (two pending requests, not enough for both) ----
def test_approve_fails_when_balance_consumed_by_another_approval(client, employee, admin, auth, make_request, set_balance, read_balance, read_status):
    set_balance(employee, remaining=5)
    first = make_request(employee, h.MON, h.WED, days=3)
    second = make_request(employee, h.NEXT_MON, h.NEXT_MON.replace(day=24), days=3)
    headers = auth(admin)
    assert review(client, headers, first.id).status_code == 200
    res = review(client, headers, second.id)
    assert res.status_code == 422 and "leave_type_id" in res.get_json()["errors"]
    assert read_status(second.id) == "pending"
    assert read_balance(employee) == 10              # 12-5 + 3, unchanged by failure


@pytest.mark.parametrize("remaining,status", [(2, 422), (3, 200), (4, 200)])
def test_approve_balance_boundary(client, employee, admin, auth, make_request, set_balance, remaining, status):
    set_balance(employee, remaining=remaining)
    item = make_request(employee, h.MON, h.WED, days=3)
    assert review(client, auth(admin), item.id).status_code == status


# ---- input validation (one invalid value per test) ---------------------------
@pytest.mark.parametrize("decision", [None, "", "maybe", "APPROVE", "x" * 21])
def test_review_invalid_decision(client, employee, admin, auth, make_request, decision):
    item = make_request(employee)
    body = {} if decision is None else {"decision": decision}
    res = client.post(f"/api/leave-requests/{item.id}/review", json=body, headers=auth(admin))
    assert res.status_code == 422 and "decision" in res.get_json()["errors"]


@pytest.mark.parametrize("note", [None, "", "   "])
def test_reject_requires_note(client, employee, admin, auth, make_request, note):
    item = make_request(employee)
    res = review(client, auth(admin), item.id, "reject", note)
    assert res.status_code == 422 and "note" in res.get_json()["errors"]


@pytest.mark.parametrize("length,status", [(499, 200), (500, 200), (501, 422)])
def test_review_note_length_boundary(client, employee, admin, auth, make_request, length, status):
    item = make_request(employee)
    assert review(client, auth(admin), item.id, "reject", "n" * length).status_code == status


def test_approve_without_note_is_allowed(client, employee, admin, auth, make_request):
    item = make_request(employee)
    assert review(client, auth(admin), item.id, "approve").status_code == 200


def test_review_unknown_request_is_404(client, admin, auth):
    assert review(client, auth(admin), 99999).status_code == 404


def test_review_validation_runs_before_lookup(client, admin, auth):
    # invalid decision + missing id -> 422 (validation first), documents the check order
    res = client.post("/api/leave-requests/99999/review", json={"decision": "x"}, headers=auth(admin))
    assert res.status_code == 422


def test_review_non_json_body(client, admin, auth, make_request, employee):
    item = make_request(employee)
    res = client.post(f"/api/leave-requests/{item.id}/review", data="x", content_type="text/plain", headers=auth(admin))
    assert res.status_code == 400


def test_review_requires_authentication(client, employee, make_request):
    item = make_request(employee)
    assert client.post(f"/api/leave-requests/{item.id}/review", json={"decision": "approve"}).status_code == 401
