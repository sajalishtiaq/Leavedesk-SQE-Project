"""White-box unit tests for app/utils.py (Validator, paging, current_user)."""
import pytest
from flask import Flask

from app.utils import (
    ApiError,
    Validator,
    json_body,
    pagination_args,
    pagination_meta,
    utc_timestamp,
)

pytestmark = pytest.mark.unit


def v(**data):
    return Validator(data)


# ---- Validator.text ----------------------------------------------------------
def test_text_missing_required():
    val = v()
    assert val.text("reason", required=True) is None
    assert val.errors["reason"] == "Reason is required."


def test_text_missing_optional_is_ok():
    val = v()
    assert val.text("note") is None and val.errors == {}


def test_text_must_be_string():
    val = v(note=123)
    assert val.text("note") is None and "must be text" in val.errors["note"]


def test_text_blank_required_and_blank_optional():
    val = v(a="   ", b="   ")
    assert val.text("a", required=True) is None and "a" in val.errors
    assert val.text("b") is None and "b" not in val.errors


@pytest.mark.parametrize("length,ok", [(9, False), (10, True), (11, True)])
def test_text_min_length_boundary(length, ok):
    val = v(r="x" * length)
    val.text("r", min_length=10)
    assert ("r" not in val.errors) is ok


@pytest.mark.parametrize("length,ok", [(19, True), (20, True), (21, False)])
def test_text_max_length_boundary(length, ok):
    val = v(r="x" * length)
    val.text("r", max_length=20)
    assert ("r" not in val.errors) is ok


def test_text_strips_whitespace():
    assert v(r="  hello  ").text("r") == "hello"


def test_label_override():
    val = v()
    val.text("x", label="Custom", required=True)
    assert val.errors["x"] == "Custom is required."


# ---- Validator.integer -------------------------------------------------------
def test_integer_missing_and_empty():
    val = v(b="")
    assert val.integer("a", required=True) is None and "a" in val.errors
    assert val.integer("b", required=True) is None and "b" in val.errors
    val2 = v()
    assert val2.integer("a") is None and val2.errors == {}


@pytest.mark.parametrize("bad", [True, False, "abc", [1]])
def test_integer_rejects_non_numbers(bad):
    val = v(n=bad)
    assert val.integer("n") is None
    assert "whole number" in val.errors["n"] or "n" in val.errors


@pytest.mark.parametrize("n,ok", [(0, False), (1, True), (2, True)])
def test_integer_minimum_boundary(n, ok):
    val = v(n=n)
    val.integer("n", minimum=1)
    assert ("n" not in val.errors) is ok


@pytest.mark.parametrize("n,ok", [(9, True), (10, True), (11, False)])
def test_integer_maximum_boundary(n, ok):
    val = v(n=n)
    val.integer("n", maximum=10)
    assert ("n" not in val.errors) is ok


def test_integer_parses_numeric_string():
    assert v(n="7").integer("n") == 7


# ---- Validator.date ----------------------------------------------------------
def test_date_ok_missing_and_bad():
    assert str(v(d="2027-03-15").date("d")) == "2027-03-15"
    val = v()
    assert val.date("d") is None and val.errors == {}
    assert val.date("d", required=True) is None and "d" in val.errors
    val = v(d="15/03/2027")
    assert val.date("d") is None and "YYYY-MM-DD" in val.errors["d"]
    val = v(d="2027-02-30")
    assert val.date("d") is None and "d" in val.errors


def test_raise_if_errors():
    val = v()
    val.raise_if_errors()        # no errors, no exception
    val.errors["x"] = "bad"
    with pytest.raises(ApiError) as exc:
        val.raise_if_errors()
    assert exc.value.status_code == 422 and exc.value.errors == {"x": "bad"}


# ---- ApiError / json_body / paging / misc ------------------------------------
def test_api_error_defaults():
    err = ApiError("boom")
    assert (err.message, err.status_code, err.errors) == ("boom", 400, None)


def test_json_body_variants():
    flask_app = Flask(__name__)
    with flask_app.test_request_context(json={"a": 1}):
        assert json_body() == {"a": 1}
    with flask_app.test_request_context(json=[1, 2]):
        with pytest.raises(ApiError) as exc:
            json_body()
        assert exc.value.status_code == 400
    with flask_app.test_request_context(data="not json", content_type="text/plain"):
        with pytest.raises(ApiError):
            json_body()


@pytest.mark.parametrize("qs,expected", [
    ("", (1, 10)),
    ("?page=0&per_page=0", (1, 1)),         # below minimum -> clamped
    ("?page=-5&per_page=1", (1, 1)),
    ("?page=3&per_page=50", (3, 50)),       # at upper limit
    ("?page=2&per_page=51", (2, 50)),       # above limit -> clamped
])
def test_pagination_args(qs, expected):
    flask_app = Flask(__name__)
    with flask_app.test_request_context("/x" + qs):
        assert pagination_args() == expected


def test_pagination_args_rejects_non_numbers():
    flask_app = Flask(__name__)
    with flask_app.test_request_context("/x?page=a"):
        with pytest.raises(ApiError) as exc:
            pagination_args()
        assert exc.value.status_code == 400


def test_pagination_meta():
    class P:
        page, per_page, total, pages, has_next, has_prev = 2, 10, 25, 3, True, True

    assert pagination_meta(P) == {
        "page": 2, "per_page": 10, "total": 25, "pages": 3,
        "has_next": True, "has_prev": True,
    }


def test_utc_timestamp_is_iso_string():
    assert "T" in utc_timestamp()
