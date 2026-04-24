"""Tests for livecheck core — Rule, Schema, validate(), ValidationError."""
import pytest
from livecheck import Rule, Schema, validate, ValidationError


# ── validate() ────────────────────────────────────────────────────────────────

class TestValidate:
    def test_single_rule_pass(self):
        assert validate(42, "must be a positive number") == 42

    def test_single_rule_fail(self):
        with pytest.raises(ValidationError) as exc:
            validate(-1, "must be a positive number")
        assert "value" in exc.value.errors

    def test_multiple_rules_all_pass(self):
        assert validate(50, "must be between 1 and 100", "must be even") == 50

    def test_multiple_rules_first_fails(self):
        with pytest.raises(ValidationError):
            validate(0, "must be a positive number", "must be even")

    def test_multiple_rules_collect_all_errors(self):
        with pytest.raises(ValidationError) as exc:
            validate(-3, "must be a positive number", "must be even")
        errors = exc.value.errors["value"]
        assert len(errors) == 2

    def test_returns_value_on_success(self):
        result = validate("alice@example.com", "must be a valid email")
        assert result == "alice@example.com"

    def test_rule_object_accepted(self):
        r = Rule("must be an integer")
        assert validate(7, r) == 7

    def test_string_and_rule_object_mixed(self):
        r = Rule("must be a positive number")
        assert validate(5, r, "must be odd") == 5


# ── Rule ──────────────────────────────────────────────────────────────────────

class TestRule:
    def test_check_pass(self):
        r = Rule("must be a valid email")
        ok, msg = r.check("alice@example.com")
        assert ok is True
        assert msg == ""

    def test_check_fail(self):
        r = Rule("must be a valid email")
        ok, msg = r.check("not-an-email")
        assert ok is False
        assert "email" in msg.lower()

    def test_optional_skips_none(self):
        r = Rule("must be a valid email", optional=True)
        ok, msg = r.check(None)
        assert ok is True

    def test_optional_validates_non_none(self):
        r = Rule("must be a valid email", optional=True)
        ok, msg = r.check("bad")
        assert ok is False

    def test_unknown_rule_raises(self):
        with pytest.raises(ValueError, match="Could not compile"):
            Rule("must be a completely fictional constraint xyz123")


# ── Schema ────────────────────────────────────────────────────────────────────

class TestSchema:
    def test_validate_pass(self, user_schema, valid_user):
        result = user_schema.validate(valid_user)
        assert result == valid_user

    def test_validate_fail_collects_all_errors(self, user_schema, invalid_user):
        with pytest.raises(ValidationError) as exc:
            user_schema.validate(invalid_user)
        errors = exc.value.errors
        assert "email" in errors
        assert "age" in errors
        assert "username" in errors
        assert "role" in errors

    def test_is_valid_true(self, user_schema, valid_user):
        assert user_schema.is_valid(valid_user) is True

    def test_is_valid_false(self, user_schema, invalid_user):
        assert user_schema.is_valid(invalid_user) is False

    def test_errors_returns_dict(self, user_schema, invalid_user):
        errs = user_schema.errors(invalid_user)
        assert isinstance(errs, dict)
        assert "email" in errs

    def test_errors_empty_on_valid(self, user_schema, valid_user):
        assert user_schema.errors(valid_user) == {}

    def test_strict_mode_rejects_unknown(self):
        s = Schema({"name": Rule("must be a non-empty string")})
        with pytest.raises(ValidationError) as exc:
            s.validate({"name": "Alice", "extra": "oops"}, strict=True)
        assert "extra" in exc.value.errors

    def test_list_of_rules_per_field(self):
        s = Schema({"bio": [Rule("must be a non-empty string"),
                             Rule("must have length at most 200")]})
        assert s.is_valid({"bio": "Hello world"})
        assert not s.is_valid({"bio": ""})
        assert not s.is_valid({"bio": "x" * 201})

    def test_missing_field_treated_as_none(self):
        s = Schema({"name": Rule("must be a non-empty string")})
        assert not s.is_valid({})

    def test_error_message_content(self, user_schema):
        errs = user_schema.errors({"email": "bad", "age": 5,
                                   "username": "ab", "role": "root"})
        assert any("email" in m.lower() for m in errs.get("email", []))


# ── ValidationError ───────────────────────────────────────────────────────────

class TestValidationError:
    def test_errors_dict_accessible(self):
        try:
            validate("x", "must be a valid email")
        except ValidationError as e:
            assert isinstance(e.errors, dict)

    def test_str_representation(self):
        try:
            validate("x", "must be a valid email")
        except ValidationError as e:
            text = str(e)
            assert "Validation failed" in text
