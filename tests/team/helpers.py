"""Shared helpers for the team test-suite. All dates are fixed (see conftest)."""
import datetime as dt

REAL_DATE = dt.date
TODAY = REAL_DATE(2027, 3, 10)          # Wednesday (frozen "today")
YESTERDAY = REAL_DATE(2027, 3, 9)
TOMORROW = REAL_DATE(2027, 3, 11)
MON, TUE, WED, THU, FRI = (REAL_DATE(2027, 3, d) for d in (15, 16, 17, 18, 19))
SAT, SUN = REAL_DATE(2027, 3, 20), REAL_DATE(2027, 3, 21)
NEXT_MON = REAL_DATE(2027, 3, 22)

GOOD_REASON = "Family function out of town"   # >= 10 chars


class FakeDate(REAL_DATE):
    @classmethod
    def today(cls):
        return TODAY


def payload(leave_type_id=1, start=MON, end=MON, reason=GOOD_REASON):
    return {
        "leave_type_id": leave_type_id,
        "start_date": start.isoformat() if hasattr(start, "isoformat") else start,
        "end_date": end.isoformat() if hasattr(end, "isoformat") else end,
        "reason": reason,
    }
