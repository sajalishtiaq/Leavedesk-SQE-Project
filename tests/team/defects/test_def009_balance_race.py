"""DEF-009 (Major): get-or-create race in services.balance_for.

Found by k6 at 5 virtual users: 0.25-0.38 % of POST /api/leave-requests returned HTTP 500 with
`UNIQUE constraint failed: leave_balances.user_id, leave_type_id, year`.
Cause: two concurrent requests both see "no balance row yet" and both INSERT it (check-then-act race).
Deterministic reproduction: the lookup returns nothing although the row exists (what the losing request sees).
Expected: the existing row is returned. Actual: IntegrityError -> HTTP 500.
Status: OPEN (xfail strict). Fix: wrap the INSERT in a SAVEPOINT, on IntegrityError re-query the row.
"""
import pytest

from app.extensions import db
from app.models import LeaveBalance, LeaveType
from app.services import balance_for

pytestmark = pytest.mark.xfail(strict=True, reason="DEF-009 open: balance_for get-or-create race")


class _BlindQuery:
    """Simulates the moment another request has already inserted the row but ours has not seen it:
    the first lookup (`first()`) finds nothing; a later re-query (`one()`) sees the real row."""

    def __init__(self, real):
        self.real, self.kw = real, {}

    def filter_by(self, **kw):
        self.kw = kw
        return self

    def first(self):
        return None

    def one(self):
        return self.real.filter_by(**self.kw).one()


def test_balance_for_survives_concurrent_creation(app, employee, set_balance, monkeypatch):
    set_balance(employee, remaining=7)                         # the 'other request' already created the row
    leave_type = db.session.get(LeaveType, 1)
    monkeypatch.setattr("app.services.LeaveBalance.query", _BlindQuery(LeaveBalance.query))
    balance = balance_for(employee, leave_type, 2027)          # currently raises IntegrityError
    db.session.flush()
    assert balance.remaining_days == 7
