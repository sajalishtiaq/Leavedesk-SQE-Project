import pytest

from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models import LeaveBalance, LeaveRequest, LeaveType, User
from app.services import ensure_leave_types

from . import helpers as h


@pytest.fixture(autouse=True)
def frozen_today(monkeypatch):
    """Freeze 'today' so every test is deterministic (2027-03-10, a Wednesday)."""
    monkeypatch.setattr("app.services.date", h.FakeDate)
    monkeypatch.setattr("app.api.leaves.date", h.FakeDate)


@pytest.fixture(autouse=True)
def fast_password_hashing(monkeypatch):
    """Test-only: cheap hashing so thousands of logins (and mutation runs) stay fast."""
    from werkzeug.security import generate_password_hash

    monkeypatch.setattr(
        "app.models.generate_password_hash",
        lambda password: generate_password_hash(password, method="pbkdf2:sha256:1"),
    )


@pytest.fixture()
def app():
    application = create_app(TestConfig)
    with application.app_context():
        db.create_all()
        ensure_leave_types()
        db.session.commit()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def make_user(app):
    counter = {"n": 0}

    def _make(role="employee", department="Engineering", active=True, name=None):
        counter["n"] += 1
        user = User(
            name=name or f"User {counter['n']}",
            email=f"user{counter['n']}@example.com",
            role=role,
            department=department,
            is_active=active,
        )
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
        return user

    return _make


@pytest.fixture()
def employee(make_user):
    return make_user("employee")


@pytest.fixture()
def other_employee(make_user):
    return make_user("employee", department="Finance")


@pytest.fixture()
def admin(make_user):
    return make_user("admin", department="HR")


@pytest.fixture()
def auth(client):
    def _auth(user):
        res = client.post(
            "/api/auth/login",
            json={"email": user.email, "password": "password123"},
        )
        assert res.status_code == 200, res.get_json()
        return {"Authorization": f"Bearer {res.get_json()['access_token']}"}

    return _auth


@pytest.fixture()
def make_request(app):
    """Insert a LeaveRequest directly in the DB (bypasses API rules)."""

    def _make(user, start=h.MON, end=h.MON, status="pending", days=1, leave_type_id=1):
        item = LeaveRequest(
            user_id=user.id,
            leave_type_id=leave_type_id,
            start_date=start,
            end_date=end,
            days=days,
            reason=h.GOOD_REASON,
            status=status,
        )
        db.session.add(item)
        db.session.commit()
        return item

    return _make


@pytest.fixture()
def set_balance(app):
    """Force a balance so that `remaining` days are left (allocated is the default)."""

    def _set(user, remaining, leave_type_id=1, year=2027, used=None):
        leave_type = db.session.get(LeaveType, leave_type_id)
        row = LeaveBalance.query.filter_by(
            user_id=user.id, leave_type_id=leave_type_id, year=year
        ).first()
        if row is None:
            row = LeaveBalance(
                user_id=user.id,
                leave_type_id=leave_type_id,
                year=year,
                allocated_days=leave_type.default_days,
                used_days=0,
            )
            db.session.add(row)
        row.used_days = used if used is not None else leave_type.default_days - remaining
        db.session.commit()
        return row

    return _set


@pytest.fixture()
def read_balance(app):
    def _read(user, leave_type_id=1, year=2027):
        db.session.expire_all()
        row = LeaveBalance.query.filter_by(
            user_id=user.id, leave_type_id=leave_type_id, year=year
        ).first()
        return None if row is None else row.used_days

    return _read


@pytest.fixture()
def read_status(app):
    def _read(request_id):
        db.session.expire_all()
        return db.session.get(LeaveRequest, request_id).status

    return _read
