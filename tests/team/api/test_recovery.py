"""Controlled failure-and-recovery tests (state-changing operations).

Test double: sqlalchemy Session.commit is replaced by a flaky stand-in that raises
OperationalError ("database unavailable") BEFORE the write completes. We then
  1) verify the persisted state after the failure (nothing changed),
  2) restore the dependency,
  3) retry and assert the expected final state with NO duplicate records / double counting.
"""
import pytest
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.extensions import db
from app.models import LeaveRequest

from .. import helpers as h

pytestmark = pytest.mark.api


@pytest.fixture()
def database_outage(app, monkeypatch):
    """Returns a switch: outage.down() / outage.up()."""
    app.config["PROPAGATE_EXCEPTIONS"] = False      # let the API turn the crash into HTTP 500
    real_commit = Session.commit
    state = {"down": False}

    def flaky_commit(self):
        if state["down"]:
            raise OperationalError("COMMIT", {}, Exception("database unavailable"))
        return real_commit(self)

    monkeypatch.setattr(Session, "commit", flaky_commit)

    class Switch:
        def down(self):
            state["down"] = True

        def up(self):
            state["down"] = False

    return Switch()


def end_failed_request():
    """In production Flask-SQLAlchemy rolls the session back when the request's app context ends.
    The test client re-uses the fixture's app context, so we do that teardown step explicitly."""
    db.session.rollback()


def count_requests(user):
    db.session.expire_all()
    return LeaveRequest.query.filter_by(user_id=user.id).count()


def test_approve_survives_database_outage_without_double_counting(
    client, employee, admin, auth, make_request, read_balance, read_status, database_outage
):
    item = make_request(employee, h.MON, h.WED, days=3)
    headers = auth(admin)
    url = f"/api/leave-requests/{item.id}/review"

    database_outage.down()
    failed = client.post(url, json={"decision": "approve"}, headers=headers)
    assert failed.status_code == 500
    end_failed_request()
    # persisted state after the failure: untouched
    assert read_status(item.id) == "pending"
    assert read_balance(employee) in (None, 0)

    database_outage.up()
    retry = client.post(url, json={"decision": "approve"}, headers=headers)
    assert retry.status_code == 200
    assert read_status(item.id) == "approved"
    assert read_balance(employee) == 3

    again = client.post(url, json={"decision": "approve"}, headers=headers)   # repeated request
    assert again.status_code == 409
    assert read_balance(employee) == 3                                        # still counted once


def test_apply_survives_database_outage_without_duplicate_records(
    client, employee, auth, database_outage
):
    headers = auth(employee)
    body = h.payload(start=h.MON, end=h.WED)

    database_outage.down()
    failed = client.post("/api/leave-requests", json=body, headers=headers)
    assert failed.status_code == 500
    end_failed_request()
    assert count_requests(employee) == 0                                      # nothing persisted

    database_outage.up()
    retry = client.post("/api/leave-requests", json=body, headers=headers)
    assert retry.status_code == 201 and count_requests(employee) == 1

    duplicate = client.post("/api/leave-requests", json=body, headers=headers)
    assert duplicate.status_code == 422                                       # overlap rule blocks it
    assert count_requests(employee) == 1                                      # no duplicates


def test_cancel_survives_database_outage_and_refunds_once(
    client, employee, auth, make_request, set_balance, read_balance, read_status, database_outage
):
    set_balance(employee, remaining=9)                    # used = 3
    item = make_request(employee, h.MON, h.WED, status="approved", days=3)
    headers = auth(employee)
    url = f"/api/leave-requests/{item.id}/cancel"

    database_outage.down()
    assert client.post(url, headers=headers).status_code == 500
    end_failed_request()
    assert read_status(item.id) == "approved" and read_balance(employee) == 3

    database_outage.up()
    assert client.post(url, headers=headers).status_code == 200
    assert read_status(item.id) == "cancelled" and read_balance(employee) == 0
    assert client.post(url, headers=headers).status_code == 409
    assert read_balance(employee) == 0
