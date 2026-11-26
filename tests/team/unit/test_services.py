"""White-box unit tests for app/services.py (business-rule functions)."""
import pytest

from app.extensions import db
from app.models import LeaveBalance, LeaveType
from app.services import (
    approve_request,
    balance_for,
    balances_for,
    ensure_leave_types,
    overlapping_request,
    validate_leave_window,
    working_days,
)

from .. import helpers as h

pytestmark = pytest.mark.unit


# ---- working_days: loop + weekday branch -------------------------------------
@pytest.mark.parametrize(
    "start,end,expected",
    [
        (h.MON, h.MON, 1),      # single weekday
        (h.MON, h.FRI, 5),      # full week
        (h.FRI, h.NEXT_MON, 2),  # spans weekend: Fri + Mon
        (h.SAT, h.SUN, 0),      # weekend only
        (h.SAT, h.SAT, 0),      # single weekend day
        (h.SUN, h.NEXT_MON, 1),
        (h.MON, h.NEXT_MON, 6),
    ],
)
def test_working_days(start, end, expected):
    assert working_days(start, end) == expected


def test_working_days_end_before_start_is_zero():
    assert working_days(h.FRI, h.MON) == 0


# ---- ensure_leave_types: create vs existing ----------------------------------
def test_ensure_leave_types_creates_missing_and_is_idempotent(app):
    db.session.query(LeaveType).delete()
    db.session.commit()
    created = ensure_leave_types()
    db.session.commit()
    assert [t.code for t in created] == ["CASUAL", "SICK", "EARNED"]
    again = ensure_leave_types()
    assert len(again) == 3 and LeaveType.query.count() == 3


def test_ensure_leave_types_adds_only_missing_one(app):
    LeaveType.query.filter_by(code="SICK").delete()
    db.session.commit()
    result = ensure_leave_types()
    assert {t.code for t in result} == {"CASUAL", "SICK", "EARNED"}


# ---- balance_for / balances_for ----------------------------------------------
def test_balance_for_creates_default_row(app, employee):
    leave_type = db.session.get(LeaveType, 1)
    balance = balance_for(employee, leave_type, 2027)
    assert balance.allocated_days == leave_type.default_days
    assert balance.used_days == 0
    assert balance.remaining_days == leave_type.default_days


def test_balance_for_returns_existing_row(app, employee, set_balance):
    set_balance(employee, remaining=4)
    leave_type = db.session.get(LeaveType, 1)
    balance = balance_for(employee, leave_type, 2027)
    assert balance.remaining_days == 4
    assert LeaveBalance.query.filter_by(user_id=employee.id).count() == 1


def test_remaining_days_never_negative(app, employee, set_balance):
    row = set_balance(employee, remaining=0, used=99)
    assert row.remaining_days == 0


def test_balances_for_returns_one_per_leave_type(app, employee):
    assert len(balances_for(employee, 2027)) == 3


# ---- overlapping_request: status filter, boundaries, exclude_id --------------
@pytest.mark.parametrize("status,blocks", [
    ("pending", True), ("approved", True), ("rejected", False), ("cancelled", False),
])
def test_overlap_only_counts_pending_and_approved(app, employee, make_request, status, blocks):
    make_request(employee, h.MON, h.WED, status=status, days=3)
    found = overlapping_request(employee.id, h.TUE, h.TUE)
    assert (found is not None) is blocks


@pytest.mark.parametrize("start,end,overlaps", [
    (h.MON.replace(day=8), h.MON.replace(day=12), False),  # ends day before existing start (BVA below)
    (h.MON.replace(day=8), h.MON, True),                   # ends exactly on existing start (at)
    (h.MON.replace(day=8), h.TUE, True),                   # inside (above)
    (h.WED, h.WED, True),                                  # starts exactly on existing end (at)
    (h.THU, h.FRI, False),                                 # starts day after existing end (above)
])
def test_overlap_boundaries(app, employee, make_request, start, end, overlaps):
    make_request(employee, h.MON, h.WED, status="pending", days=3)
    assert (overlapping_request(employee.id, start, end) is not None) is overlaps


def test_overlap_ignores_other_users(app, employee, other_employee, make_request):
    make_request(other_employee, h.MON, h.WED)
    assert overlapping_request(employee.id, h.MON, h.WED) is None


def test_overlap_exclude_id_skips_the_request_itself(app, employee, make_request):
    existing = make_request(employee, h.MON, h.WED, days=3)
    assert overlapping_request(employee.id, h.MON, h.WED) is not None
    assert overlapping_request(employee.id, h.MON, h.WED, exclude_id=existing.id) is None


# ---- validate_leave_window: every branch -------------------------------------
def _validate(app, user, start, end, year=None):
    leave_type = db.session.get(LeaveType, 1)
    return validate_leave_window(user, leave_type, start, end, year or start.year)


def test_validate_ok_returns_days_and_balance(app, employee):
    days, balance, errors = _validate(app, employee, h.MON, h.FRI)
    assert (days, errors) == (5, {})
    assert balance is not None


def test_validate_end_before_start(app, employee):
    days, balance, errors = _validate(app, employee, h.TUE, h.MON)
    assert "end_date" in errors and days == 0 and balance is None


def test_validate_crosses_year(app, employee):
    start, end = h.REAL_DATE(2027, 12, 31), h.REAL_DATE(2028, 1, 3)
    _, _, errors = _validate(app, employee, start, end)
    assert "calendar year" in errors["end_date"]


def test_validate_start_in_past(app, employee):
    _, _, errors = _validate(app, employee, h.YESTERDAY, h.YESTERDAY)
    assert "start_date" in errors


def test_validate_start_today_is_allowed(app, employee):
    days, _, errors = _validate(app, employee, h.TODAY, h.TODAY)
    assert (days, errors) == (1, {})


def test_validate_no_working_days(app, employee):
    _, _, errors = _validate(app, employee, h.SAT, h.SUN)
    assert "no working days" in errors["end_date"]


def test_validate_overlap(app, employee, make_request):
    make_request(employee, h.MON, h.WED, days=3)
    _, _, errors = _validate(app, employee, h.TUE, h.THU)
    assert "overlaps" in errors["start_date"]


@pytest.mark.parametrize("remaining,ok", [(4, False), (5, True), (6, True)])
def test_validate_balance_boundary_3_point(app, employee, set_balance, remaining, ok):
    set_balance(employee, remaining=remaining)
    _, _, errors = _validate(app, employee, h.MON, h.FRI)   # needs 5 days
    assert ("leave_type_id" not in errors) is ok


# ---- approve_request: both branches + side effects ---------------------------
class _Reviewer:
    id = 999


def test_approve_updates_balance_and_status(app, employee, make_request, set_balance):
    set_balance(employee, remaining=5)
    item = make_request(employee, h.MON, h.WED, days=3)
    assert approve_request(item, _Reviewer, "ok") is None
    assert (item.status, item.reviewed_by_id, item.review_note) == ("approved", 999, "ok")
    assert item.reviewed_at is not None
    assert balance_for(employee, item.leave_type, 2027).used_days == 10  # 12-5 + 3


def test_approve_exact_remaining_is_allowed(app, employee, make_request, set_balance):
    set_balance(employee, remaining=3)
    item = make_request(employee, h.MON, h.WED, days=3)
    assert approve_request(item, _Reviewer, None) is None


def test_approve_rejected_when_not_enough_balance(app, employee, make_request, set_balance):
    set_balance(employee, remaining=2)
    item = make_request(employee, h.MON, h.WED, days=3)
    errors = approve_request(item, _Reviewer, None)
    assert "leave_type_id" in errors
    assert item.status == "pending"              # unchanged
    assert balance_for(employee, item.leave_type, 2027).used_days == 10  # unchanged
