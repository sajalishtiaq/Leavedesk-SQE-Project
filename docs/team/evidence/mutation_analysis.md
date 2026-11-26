# Mutation analysis (mutmut)

Tool: mutmut 3.8.1 on `app/services.py`, `app/utils.py`, `app/api/leaves.py` (script: `scripts/run_mutation.sh`).

| Run | Mutants | Killed | Survived | Score |
|---|---|---|---|---|
| 1 (before analysis) | 350 | 284 | 66 | 81.1 % |
| 2 (after adding the tests below) | 350 | 346 | 4 | 98.9 % |

## Run 1: 66 surviving mutants analysed
Weak assertion: **55**, missing test: **7**, equivalent: **4**.

| # | Mutant | Original | Mutated | Class | Reason / action |
|---|---|---|---|---|---|
| 1 | `services.x_balance_for__mutmut_5` | `user_id=user.id, leave_type_id=leave_type.id, year=year` | `leave_type_id=leave_type.id, year=year` | missing test | no test proved the balance lookup filters by user |
| 2 | `services.x_balance_for__mutmut_6` | `user_id=user.id, leave_type_id=leave_type.id, year=year` | `user_id=user.id, year=year` | missing test | no test proved it filters by leave type |
| 3 | `services.x_balance_for__mutmut_7` | `user_id=user.id, leave_type_id=leave_type.id, year=year` | `user_id=user.id, leave_type_id=leave_type.id, ).first()` | missing test | no test proved it filters by year |
| 4 | `services.x_balance_for__mutmut_14` | `used_days=0,` | `used_days=None,` | equivalent | `used_days` column already defaults to 0, so passing None/omitting it stores the same value |
| 5 | `services.x_balance_for__mutmut_19` | `used_days=0,` | `)` | equivalent | argument removed; column default (0) gives identical behaviour |
| 6 | `services.x_balances_for__mutmut_7` | `for leave_type in LeaveType.query.order_by(LeaveType.sort_or` | `for leave_type in LeaveType.query.order_by(None).all()` | missing test | ordering by sort_order never asserted |
| 7 | `services.x_overlapping_request__mutmut_20` | `query = query.filter(LeaveRequest.id != exclude_id)` | `query = query.filter(None)` | missing test | exclude_id tested only with a single request |
| 8 | `services.x_validate_leave_window__mutmut_3` | `errors["end_date"] = "End date cannot be before the start da` | `errors["end_date"] = None` | weak assertion | error message / label text never asserted exactly |
| 9 | `services.x_validate_leave_window__mutmut_6` | `errors["end_date"] = "End date cannot be before the start da` | `errors["end_date"] = "XXEnd date cannot be before the start ` | weak assertion | error message / label text never asserted exactly |
| 10 | `services.x_validate_leave_window__mutmut_7` | `errors["end_date"] = "End date cannot be before the start da` | `errors["end_date"] = "end date cannot be before the start da` | weak assertion | error message / label text never asserted exactly |
| 11 | `services.x_validate_leave_window__mutmut_8` | `errors["end_date"] = "End date cannot be before the start da` | `errors["end_date"] = "END DATE CANNOT BE BEFORE THE START DA` | weak assertion | error message / label text never asserted exactly |
| 12 | `services.x_validate_leave_window__mutmut_13` | `errors["end_date"] = "A leave request cannot span two calend` | `errors["end_date"] = "XXA leave request cannot span two cale` | weak assertion | error message / label text never asserted exactly |
| 13 | `services.x_validate_leave_window__mutmut_14` | `errors["end_date"] = "A leave request cannot span two calend` | `errors["end_date"] = "a leave request cannot span two calend` | weak assertion | error message / label text never asserted exactly |
| 14 | `services.x_validate_leave_window__mutmut_17` | `errors["start_date"] = "Leave cannot start in the past."` | `errors["start_date"] = None` | weak assertion | error message / label text never asserted exactly |
| 15 | `services.x_validate_leave_window__mutmut_20` | `errors["start_date"] = "Leave cannot start in the past."` | `errors["start_date"] = "XXLeave cannot start in the past.XX"` | weak assertion | error message / label text never asserted exactly |
| 16 | `services.x_validate_leave_window__mutmut_21` | `errors["start_date"] = "Leave cannot start in the past."` | `errors["start_date"] = "leave cannot start in the past."` | weak assertion | error message / label text never asserted exactly |
| 17 | `services.x_validate_leave_window__mutmut_22` | `errors["start_date"] = "Leave cannot start in the past."` | `errors["start_date"] = "LEAVE CANNOT START IN THE PAST."` | weak assertion | error message / label text never asserted exactly |
| 18 | `services.x_validate_leave_window__mutmut_36` | `errors["end_date"] = "The selected range has no working days` | `errors["end_date"] = "XXThe selected range has no working da` | weak assertion | error message / label text never asserted exactly |
| 19 | `services.x_validate_leave_window__mutmut_37` | `errors["end_date"] = "The selected range has no working days` | `errors["end_date"] = "the selected range has no working days` | weak assertion | error message / label text never asserted exactly |
| 20 | `services.x_validate_leave_window__mutmut_50` | `"You already have a pending or approved request that overlap` | `"XXYou already have a pending or approved request that overl` | weak assertion | error message / label text never asserted exactly |
| 21 | `services.x_validate_leave_window__mutmut_51` | `"You already have a pending or approved request that overlap` | `"you already have a pending or approved request that overlap` | weak assertion | error message / label text never asserted exactly |
| 22 | `services.x_validate_leave_window__mutmut_63` | `errors["leave_type_id"] = (` | `errors["leave_type_id"] = None` | weak assertion | error message / label text never asserted exactly |
| 23 | `utils.ApiError.__init____mutmut_2` | `super().__init__(message)` | `super().__init__(None)` | weak assertion | error message / label text never asserted exactly |
| 24 | `utils.Validator._label__mutmut_6` | `return label or key.replace("_", " ").capitalize()` | `return label or key.replace("XX_XX", " ").capitalize()` | weak assertion | error message / label text never asserted exactly |
| 25 | `utils.Validator._label__mutmut_7` | `return label or key.replace("_", " ").capitalize()` | `return label or key.replace("_", "XX XX").capitalize()` | weak assertion | error message / label text never asserted exactly |
| 26 | `utils.Validator.text__mutmut_2` | `def text(self, key, label=None, required=False, max_length=5` | `def text(self, key, label=None, required=False, max_length=5` | missing test | default max_length (500) never exercised |
| 27 | `utils.Validator.text__mutmut_18` | `self.errors[key] = f"{label} is required."` | `self.errors[key] = None` | weak assertion | error message / label text never asserted exactly |
| 28 | `utils.Validator.text__mutmut_20` | `self.errors[key] = f"{label} must be at least {min_length} c` | `self.errors[key] = None` | weak assertion | error message / label text never asserted exactly |
| 29 | `utils.Validator.text__mutmut_22` | `self.errors[key] = f"{label} must be under {max_length} char` | `self.errors[key] = None` | weak assertion | error message / label text never asserted exactly |
| 30 | `utils.Validator.integer__mutmut_2` | `def integer(self, key, label=None, required=False, minimum=0` | `def integer(self, key, label=None, required=False, minimum=1` | missing test | default minimum (0) never exercised |
| 31 | `utils.Validator.integer__mutmut_3` | `label = self._label(key, label)` | `label = None` | weak assertion | error message / label text never asserted exactly |
| 32 | `utils.Validator.integer__mutmut_5` | `label = self._label(key, label)` | `label = self._label(key, None)` | weak assertion | error message / label text never asserted exactly |
| 33 | `utils.Validator.integer__mutmut_11` | `if value in (None, ""):` | `if value in (None, "XXXX"):` | weak assertion | error message / label text never asserted exactly |
| 34 | `utils.Validator.integer__mutmut_12` | `self.errors[key] = f"{label} is required."` | `self.errors[key] = None` | weak assertion | error message / label text never asserted exactly |
| 35 | `utils.Validator.integer__mutmut_18` | `self.errors[key] = f"{label} cannot be less than {minimum}."` | `self.errors[key] = None` | weak assertion | error message / label text never asserted exactly |
| 36 | `utils.Validator.integer__mutmut_22` | `self.errors[key] = f"{label} cannot be more than {maximum}."` | `self.errors[key] = None` | weak assertion | error message / label text never asserted exactly |
| 37 | `utils.Validator.date__mutmut_2` | `label = self._label(key, label)` | `label = None` | weak assertion | error message / label text never asserted exactly |
| 38 | `utils.Validator.date__mutmut_4` | `label = self._label(key, label)` | `label = self._label(key, None)` | weak assertion | error message / label text never asserted exactly |
| 39 | `utils.Validator.date__mutmut_10` | `if value in (None, ""):` | `if value in (None, "XXXX"):` | weak assertion | error message / label text never asserted exactly |
| 40 | `utils.Validator.date__mutmut_11` | `self.errors[key] = f"{label} is required."` | `self.errors[key] = None` | weak assertion | error message / label text never asserted exactly |
| 41 | `utils.Validator.raise_if_errors__mutmut_1` | `raise ApiError("Please check the submitted fields.", 422, se` | `raise ApiError(None, 422, self.errors)` | weak assertion | error message / label text never asserted exactly |
| 42 | `utils.Validator.raise_if_errors__mutmut_7` | `raise ApiError("Please check the submitted fields.", 422, se` | `raise ApiError("XXPlease check the submitted fields.XX", 422` | weak assertion | error message / label text never asserted exactly |
| 43 | `utils.Validator.raise_if_errors__mutmut_8` | `raise ApiError("Please check the submitted fields.", 422, se` | `raise ApiError("please check the submitted fields.", 422, se` | weak assertion | error message / label text never asserted exactly |
| 44 | `utils.Validator.raise_if_errors__mutmut_9` | `raise ApiError("Please check the submitted fields.", 422, se` | `raise ApiError("PLEASE CHECK THE SUBMITTED FIELDS.", 422, se` | weak assertion | error message / label text never asserted exactly |
| 45 | `utils.x_json_body__mutmut_5` | `raise ApiError("Request body must be a JSON object.", 400)` | `raise ApiError(None, 400)` | weak assertion | error message / label text never asserted exactly |
| 46 | `utils.x_json_body__mutmut_7` | `raise ApiError("Request body must be a JSON object.", 400)` | `raise ApiError(400)` | weak assertion | error message / label text never asserted exactly |
| 47 | `utils.x_json_body__mutmut_8` | `raise ApiError("Request body must be a JSON object.", 400)` | `raise ApiError("Request body must be a JSON object.", )` | equivalent | `ApiError(msg)` defaults to status 400, identical to passing 400 |
| 48 | `utils.x_json_body__mutmut_9` | `raise ApiError("Request body must be a JSON object.", 400)` | `raise ApiError("XXRequest body must be a JSON object.XX", 40` | weak assertion | error message / label text never asserted exactly |
| 49 | `utils.x_json_body__mutmut_10` | `raise ApiError("Request body must be a JSON object.", 400)` | `raise ApiError("request body must be a json object.", 400)` | weak assertion | error message / label text never asserted exactly |
| 50 | `utils.x_json_body__mutmut_11` | `raise ApiError("Request body must be a JSON object.", 400)` | `raise ApiError("REQUEST BODY MUST BE A JSON OBJECT.", 400)` | weak assertion | error message / label text never asserted exactly |
| 51 | `utils.x_current_user__mutmut_15` | `raise ApiError("Account no longer exists.", 401)` | `raise ApiError("XXAccount no longer exists.XX", 401)` | weak assertion | error message / label text never asserted exactly |
| 52 | `utils.x_current_user__mutmut_16` | `raise ApiError("Account no longer exists.", 401)` | `raise ApiError("account no longer exists.", 401)` | weak assertion | error message / label text never asserted exactly |
| 53 | `utils.x_pagination_args__mutmut_19` | `raise ApiError("Page and per_page must be whole numbers.", 4` | `raise ApiError(None, 400)` | weak assertion | error message / label text never asserted exactly |
| 54 | `utils.x_pagination_args__mutmut_21` | `raise ApiError("Page and per_page must be whole numbers.", 4` | `raise ApiError(400)` | weak assertion | error message / label text never asserted exactly |
| 55 | `utils.x_pagination_args__mutmut_22` | `raise ApiError("Page and per_page must be whole numbers.", 4` | `raise ApiError("Page and per_page must be whole numbers.", )` | equivalent | `ApiError(msg)` defaults to status 400, identical to passing 400 |
| 56 | `utils.x_pagination_args__mutmut_23` | `raise ApiError("Page and per_page must be whole numbers.", 4` | `raise ApiError("XXPage and per_page must be whole numbers.XX` | weak assertion | error message / label text never asserted exactly |
| 57 | `utils.x_pagination_args__mutmut_24` | `raise ApiError("Page and per_page must be whole numbers.", 4` | `raise ApiError("page and per_page must be whole numbers.", 4` | weak assertion | error message / label text never asserted exactly |
| 58 | `utils.x_pagination_args__mutmut_25` | `raise ApiError("Page and per_page must be whole numbers.", 4` | `raise ApiError("PAGE AND PER_PAGE MUST BE WHOLE NUMBERS.", 4` | weak assertion | error message / label text never asserted exactly |
| 59 | `api.leaves.x_get_request_or_404__mutmut_7` | `raise ApiError("Leave request not found.", 404)` | `raise ApiError(None, 404)` | weak assertion | error message / label text never asserted exactly |
| 60 | `api.leaves.x_get_request_or_404__mutmut_11` | `raise ApiError("Leave request not found.", 404)` | `raise ApiError("XXLeave request not found.XX", 404)` | weak assertion | error message / label text never asserted exactly |
| 61 | `api.leaves.x_get_request_or_404__mutmut_12` | `raise ApiError("Leave request not found.", 404)` | `raise ApiError("leave request not found.", 404)` | weak assertion | error message / label text never asserted exactly |
| 62 | `api.leaves.x_get_request_or_404__mutmut_13` | `raise ApiError("Leave request not found.", 404)` | `raise ApiError("LEAVE REQUEST NOT FOUND.", 404)` | weak assertion | error message / label text never asserted exactly |
| 63 | `api.leaves.x_get_request_or_404__mutmut_18` | `raise ApiError("Leave request not found.", 404)` | `raise ApiError(None, 404)` | weak assertion | error message / label text never asserted exactly |
| 64 | `api.leaves.x_get_request_or_404__mutmut_22` | `raise ApiError("Leave request not found.", 404)` | `raise ApiError("XXLeave request not found.XX", 404)` | weak assertion | error message / label text never asserted exactly |
| 65 | `api.leaves.x_get_request_or_404__mutmut_23` | `raise ApiError("Leave request not found.", 404)` | `raise ApiError("leave request not found.", 404)` | weak assertion | error message / label text never asserted exactly |
| 66 | `api.leaves.x_get_request_or_404__mutmut_24` | `raise ApiError("Leave request not found.", 404)` | `raise ApiError("LEAVE REQUEST NOT FOUND.", 404)` | weak assertion | error message / label text never asserted exactly |

## Actions (all killable mutants killed)
* **Weak assertions:** `tests/team/unit/test_mutation_killers.py` asserts every error message exactly (utils, services, API JSON).
* **Missing tests:** same file adds filter tests for `balance_for`, ordering test for `balances_for`, `exclude_id` test with two requests, default-parameter tests for `Validator.text/integer`.
* **Equivalent (4, still alive in run 2):** behaviour identical (column default 0; `ApiError` default status 400). Not killable; they cap the maximum score at 346/350 = 98.9 %.

Business-rule mutants (comparison operators, boundaries, boolean operators, status literals) were all killed in run 1 already.

## Custom mutation operators (`tools/custom_mutation.py`, 6 operators based on the business rules)
| Operator | Rule attacked | Example |
|---|---|---|
| ROLE | BR2 admin-only review | negate `user.is_admin` |
| STATUS | BR3 state machine | `'pending'` -> `'approved'` |
| OWNER | BR2/BR4 ownership | flip `user_id == / !=` |
| LIMIT | BR1 limits | reason 10/500, note 500, per_page 50, weekday < 5 (+/-1) |
| BALANCE | BR1 balance boundary | `<` -> `<=` / `>` |
| USED | shared record | `+=` -> `-=`, `-` -> `+` on `used_days` |

| Run | Mutants | Killed | Survived | Score |
|---|---|---|---|---|
| 1 | 46 | 39 | 7 | 84.8 % |
| 2 (after `test_filters_strict.py`) | 46 | 44 | 2 | 95.7 % |

Run 1 survivors were **real test gaps**: filters tested with data too small to distinguish `==` from `!=` (OWNER), and the status filter tested for one status only (STATUS). Fixed in `tests/team/api/test_filters_strict.py`.
Run 2 survivors (2): `decision` `max_length=20 +/-1` is **equivalent** - any decision other than `approve`/`reject` is rejected anyway, so the length limit is redundant (documented in `scripts/check_custom_mutation.py`).
