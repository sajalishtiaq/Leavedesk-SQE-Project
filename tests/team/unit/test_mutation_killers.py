"""Tests added after surviving-mutant analysis (see docs/team/evidence/mutation_analysis.md).

Weak-assertion survivors: error messages were never asserted exactly.
Missing-test survivors: balance_for filters, balances_for ordering, overlap exclude_id.
"""
import pytest

from app.extensions import db
from app.models import LeaveBalance, LeaveType
from app.services import balance_for, balances_for, overlapping_request, validate_leave_window
from app.utils import ApiError, Validator

from .. import helpers as h

pytestmark = pytest.mark.unit


def v(**data):
    return Validator(data)


# ---------------- messages: utils ----------------
def test_api_error_str_is_message():
    assert str(ApiError("boom")) == "boom"


def test_label_derivation():
    assert v()._label("leave_type_id", None) == "Leave type id"
    assert v()._label("x", "Custom") == "Custom"


def test_text_messages_exact():
    val = v(a="  ", b="short", c="x" * 6)
    val.text("a", required=True)
    val.text("b", min_length=10)
    val.text("c", max_length=5)
    val2 = v()
    val2.text("reason", required=True)
    assert val.errors["a"] == "A is required."
    assert val.errors["b"] == "B must be at least 10 characters."
    assert val.errors["c"] == "C must be under 5 characters."
    assert val2.errors["reason"] == "Reason is required."


def test_text_default_max_length_is_500():
    ok, bad = v(t="x" * 500), v(t="x" * 501)
    ok.text("t"), bad.text("t")
    assert ok.errors == {} and bad.errors["t"] == "T must be under 500 characters."


def test_integer_messages_exact_and_defaults():
    val = v(a="", b=-1, c=11)
    val.integer("a", required=True)
    val.integer("b", minimum=0)
    val.integer("c", maximum=10)
    val2 = v()
    val2.integer("n", required=True)
    assert val.errors["a"] == "A is required."
    assert val.errors["b"] == "B cannot be less than 0."
    assert val.errors["c"] == "C cannot be more than 10."
    assert val2.errors["n"] == "N is required."


def test_integer_default_minimum_is_zero():
    val = v(n=0)
    assert val.integer("n") == 0 and val.errors == {}


def test_integer_label_in_messages():
    val = v(n="x")
    val.integer("n", label="Count")
    assert val.errors["n"] == "Count must be a whole number."


def test_date_messages_exact():
    val = v(a="", b="nope")
    val.date("a", required=True)
    val.date("b", label="Start")
    assert val.errors["a"] == "A is required."
    assert val.errors["b"] == "Start must use the YYYY-MM-DD format."


def test_raise_if_errors_message():
    val = v()
    val.errors["x"] = "bad"
    with pytest.raises(ApiError) as exc:
        val.raise_if_errors()
    assert exc.value.message == "Please check the submitted fields."


# ---------------- messages: API level (exact JSON message) ----------------
def test_json_body_message(client, employee, auth):
    res = client.post("/api/leave-requests", data="x", content_type="text/plain", headers=auth(employee))
    assert (res.status_code, res.get_json()["message"]) == (400, "Request body must be a JSON object.")


def test_current_user_message(client, make_user, auth):
    user = make_user("employee")
    headers = auth(user)
    user.is_active = False
    db.session.commit()
    res = client.get("/api/leave-requests", headers=headers)
    assert res.get_json()["message"] == "Account no longer exists."


def test_pagination_message(client, employee, auth):
    res = client.get("/api/leave-requests?page=x", headers=auth(employee))
    assert (res.status_code, res.get_json()["message"]) == (400, "Page and per_page must be whole numbers.")


def test_not_found_messages(client, employee, other_employee, auth, make_request):
    item = make_request(employee)
    missing = client.get("/api/leave-requests/424242", headers=auth(employee))
    hidden = client.get(f"/api/leave-requests/{item.id}", headers=auth(other_employee))
    assert missing.get_json()["message"] == hidden.get_json()["message"] == "Leave request not found."


# ---------------- messages: services ----------------
def _errors(start, end, user):
    return validate_leave_window(user, db.session.get(LeaveType, 1), start, end, start.year)[2]


def test_validate_messages_exact(app, employee, make_request, set_balance):
    assert _errors(h.TUE, h.MON, employee) == {"end_date": "End date cannot be before the start date."}
    assert _errors(h.REAL_DATE(2027, 12, 31), h.REAL_DATE(2028, 1, 3), employee) == {
        "end_date": "A leave request cannot span two calendar years."}
    assert _errors(h.YESTERDAY, h.YESTERDAY, employee) == {"start_date": "Leave cannot start in the past."}
    assert _errors(h.SAT, h.SUN, employee) == {"end_date": "The selected range has no working days (Mon\u2013Fri)."}
    make_request(employee, h.MON, h.WED, days=3)
    assert _errors(h.TUE, h.TUE, employee) == {
        "start_date": "You already have a pending or approved request that overlaps these dates."}


def test_balance_message_exact(app, employee, set_balance):
    set_balance(employee, remaining=4)
    assert _errors(h.MON, h.FRI, employee) == {
        "leave_type_id": "Only 4 day(s) of Casual Leave remain for 2027."}


def test_approve_balance_error_message_exact(app, employee, make_request, set_balance):
    from app.services import approve_request
    set_balance(employee, remaining=2)
    item = make_request(employee, h.MON, h.WED, days=3)
    errors = approve_request(item, type("R", (), {"id": 1}), None)
    assert errors == {"leave_type_id": "Only 2 day(s) of Casual Leave remain for 2027. This request needs 3."}


# ---------------- missing tests: service filters ----------------
def test_balance_for_filters_by_user_type_and_year(app, employee, other_employee, set_balance):
    set_balance(employee, remaining=1, leave_type_id=1, year=2027)
    set_balance(other_employee, remaining=7, leave_type_id=1, year=2027)
    set_balance(employee, remaining=3, leave_type_id=2, year=2027)
    set_balance(employee, remaining=9, leave_type_id=1, year=2028)
    lt1, lt2 = db.session.get(LeaveType, 1), db.session.get(LeaveType, 2)
    assert balance_for(employee, lt1, 2027).remaining_days == 1
    assert balance_for(other_employee, lt1, 2027).remaining_days == 7
    assert balance_for(employee, lt2, 2027).remaining_days == 3
    assert balance_for(employee, lt1, 2028).remaining_days == 9
    assert LeaveBalance.query.count() == 4            # nothing was duplicated


def test_new_balance_row_starts_at_zero_used(app, employee):
    row = balance_for(employee, db.session.get(LeaveType, 2), 2027)
    db.session.commit()
    assert (row.used_days, row.allocated_days) == (0, 10)


def test_balances_for_follows_sort_order_not_insertion_order(app, employee):
    for row in LeaveType.query.all():                 # invert sort_order vs id
        row.sort_order = 100 - row.id
    db.session.commit()
    assert [b.leave_type.code for b in balances_for(employee, 2027)] == ["EARNED", "SICK", "CASUAL"]


def test_overlap_exclude_id_only_excludes_that_request(app, employee, make_request):
    first = make_request(employee, h.MON, h.TUE, days=2)
    second = make_request(employee, h.TUE, h.WED, days=2)
    found = overlapping_request(employee.id, h.TUE, h.TUE, exclude_id=first.id)
    assert found is not None and found.id == second.id
