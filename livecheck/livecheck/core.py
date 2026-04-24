"""
Core classes: Rule, Schema, ValidationError, validate().
"""

from __future__ import annotations
from typing import Any
from dataclasses import dataclass, field
from .compiler import compile_rule


class ValidationError(Exception):
    """Raised when one or more validation rules fail."""

    def __init__(self, errors: dict[str, list[str]]):
        self.errors = errors
        lines = []
        for field_name, msgs in errors.items():
            for msg in msgs:
                lines.append(f"  [{field_name}] {msg}")
        super().__init__("Validation failed:\n" + "\n".join(lines))


@dataclass
class Rule:
    """
    A single validation rule expressed in plain English.

    Parameters
    ----------
    text : str
        The natural language rule, e.g. "must be a positive number".
    optional : bool
        If True, skip validation when the value is None.

    Examples
    --------
    >>> r = Rule("must be a valid email")
    >>> r.check("hello@example.com")
    (True, '')
    >>> r.check("not-an-email")
    (False, "Expected a valid email address, got 'not-an-email'")
    """
    text: str
    optional: bool = False
    _fn: Any = field(init=False, repr=False, default=None)

    def __post_init__(self):
        self._fn = compile_rule(self.text)

    def check(self, value: Any) -> tuple[bool, str]:
        if self.optional and value is None:
            return True, ""
        ok, msg = self._fn(value)
        return ok, (msg if not ok else "")


class Schema:
    """
    A collection of named fields, each with one or more Rules.

    Parameters
    ----------
    fields : dict[str, Rule | list[Rule]]
        Mapping of field names to their rules.

    Examples
    --------
    >>> schema = Schema({
    ...     "age": Rule("must be between 0 and 150"),
    ...     "email": [Rule("must be a non-empty string"), Rule("must be a valid email")],
    ... })
    >>> schema.validate({"age": 25, "email": "alice@example.com"})
    {'age': 25, 'email': 'alice@example.com'}
    """

    def __init__(self, fields: dict[str, "Rule | list[Rule]"]):
        self._fields: dict[str, list[Rule]] = {}
        for name, rules in fields.items():
            if isinstance(rules, Rule):
                self._fields[name] = [rules]
            else:
                self._fields[name] = list(rules)

    def validate(self, data: dict[str, Any], *, strict: bool = False) -> dict[str, Any]:
        """
        Validate a data dictionary against the schema.

        Parameters
        ----------
        data : dict
            The data to validate.
        strict : bool
            If True, raise on unknown keys in data.

        Returns
        -------
        dict
            The original data (unchanged) if valid.

        Raises
        ------
        ValidationError
            If one or more fields fail validation.
        """
        errors: dict[str, list[str]] = {}

        if strict:
            unknown = set(data) - set(self._fields)
            if unknown:
                for k in unknown:
                    errors.setdefault(k, []).append("Unknown field (strict mode)")

        for name, rules in self._fields.items():
            value = data.get(name)
            for rule in rules:
                ok, msg = rule.check(value)
                if not ok:
                    errors.setdefault(name, []).append(msg)

        if errors:
            raise ValidationError(errors)

        return data

    def is_valid(self, data: dict[str, Any]) -> bool:
        """Return True if data passes all rules, False otherwise."""
        try:
            self.validate(data)
            return True
        except ValidationError:
            return False

    def errors(self, data: dict[str, Any]) -> dict[str, list[str]]:
        """Return all validation errors without raising."""
        try:
            self.validate(data)
            return {}
        except ValidationError as e:
            return e.errors


def validate(value: Any, *rules: "str | Rule") -> Any:
    """
    Validate a single value against one or more rules.

    Parameters
    ----------
    value : Any
        The value to validate.
    *rules : str | Rule
        One or more rule strings or Rule objects.

    Returns
    -------
    Any
        The value if all rules pass.

    Raises
    ------
    ValidationError
        If any rule fails.

    Examples
    --------
    >>> validate(42, "must be a positive number", "must be between 1 and 100")
    42
    >>> validate("hello", Rule("must be a valid email"))
    # raises ValidationError
    """
    parsed_rules = [Rule(r) if isinstance(r, str) else r for r in rules]
    errors: list[str] = []
    for rule in parsed_rules:
        ok, msg = rule.check(value)
        if not ok:
            errors.append(msg)
    if errors:
        raise ValidationError({"value": errors})
    return value
