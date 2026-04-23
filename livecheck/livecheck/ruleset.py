"""
livecheck.ruleset — Named, reusable rule presets.

Register named groups of rules once, reuse everywhere:

    RuleSet.register("email_field", [
        "must be a non-empty string",
        "must be a valid email",
        "must have length at most 254",
    ])

    validate(value, *RuleSet.get("email_field"))
    # or use in Schema:
    schema = Schema({"email": RuleSet.schema_rules("email_field")})
"""
from __future__ import annotations
from typing import Any
from .core import Rule, Schema, validate, ValidationError

# ── Built-in presets ──────────────────────────────────────────────────────────
_PRESETS: dict[str, list[str]] = {
    "email": [
        "must be a non-empty string",
        "must be a valid email",
        "must have length at most 254",
        "must be trimmed",
    ],
    "password": [
        "must be a non-empty string",
        "must be a valid password",
        "must have length at most 128",
    ],
    "strong_password": [
        "must be a non-empty string",
        "must be a valid strong password",
        "must have length at most 128",
    ],
    "username": [
        "must be a non-empty string",
        "must be a valid username",
        "must be trimmed",
    ],
    "url": [
        "must be a non-empty string",
        "must be a valid url",
        "must have length at most 2048",
    ],
    "phone": [
        "must be a non-empty string",
        "must be a valid phone number",
        "must be trimmed",
    ],
    "age": [
        "must be an integer",
        "must be between 0 and 150",
    ],
    "adult_age": [
        "must be an integer",
        "must be between 18 and 120",
    ],
    "price": [
        "must be a number",
        "must be a positive number",
        "must have at most 2 decimal places",
    ],
    "uuid": [
        "must be a non-empty string",
        "must be a valid uuid",
    ],
    "ip": [
        "must be a non-empty string",
        "must be a valid IP address",
    ],
    "date": [
        "must be a non-empty string",
        "must be a valid date",
    ],
    "slug": [
        "must be a non-empty string",
        "must be a valid slug",
        "must have length at least 1",
        "must have length at most 200",
    ],
    "hex_color": [
        "must be a non-empty string",
        "must be a valid hex color",
    ],
    "lat": [
        "must be a number",
        "must be a valid latitude",
    ],
    "lon": [
        "must be a number",
        "must be a valid longitude",
    ],
    "percentage": [
        "must be a number",
        "must be a percentage",
    ],
    "country": [
        "must be a non-empty string",
        "must be a valid country code",
    ],
    "currency": [
        "must be a non-empty string",
        "must be a valid currency code",
    ],
    "jwt": [
        "must be a non-empty string",
        "must be a valid jwt token",
    ],
    "semver": [
        "must be a non-empty string",
        "must be a valid semver",
    ],
    "credit_card": [
        "must be a non-empty string",
        "must be a valid credit card number",
    ],
    "api_key": [
        "must be a non-empty string",
        "must be a strong api key",
    ],
    "bmi": [
        "must be a number",
        "must be a valid bmi",
    ],
    "blood_pressure": [
        "must be a non-empty string",
        "must be a valid blood pressure",
    ],
    "http_status": [
        "must be an integer",
        "must be a valid http status code",
    ],
    "log_level": [
        "must be a non-empty string",
        "must be a valid log level",
    ],
    "sku": [
        "must be a non-empty string",
        "must be a valid sku",
    ],
    "identifier": [
        "must be a non-empty string",
        "must be a valid python identifier",
    ],
    "env_var": [
        "must be a non-empty string",
        "must be a valid env var name",
    ],
}


class RuleSet:
    """
    Named, reusable rule presets. Use built-in presets or register your own.

    Built-in presets: email, password, strong_password, username, url, phone,
    age, adult_age, price, uuid, ip, date, slug, hex_color, lat, lon,
    percentage, country, currency, jwt, semver, credit_card, api_key,
    bmi, blood_pressure, http_status, log_level, sku, identifier, env_var.

    Example::

        # Use a preset in validate()
        validate(value, *RuleSet.get("email"))

        # Use presets in Schema
        schema = Schema({
            "email":    RuleSet.schema_rules("email"),
            "password": RuleSet.schema_rules("strong_password"),
            "age":      RuleSet.schema_rules("adult_age"),
        })

        # Register a custom preset
        RuleSet.register("eu_vat", [
            "must be a non-empty string",
            "must match pattern '^[A-Z]{2}[0-9A-Z]{8,12}$'",
        ])
    """

    @classmethod
    def register(cls, name: str, rules: list[str], *, overwrite: bool = False) -> None:
        """Register a new named rule preset."""
        if name in _PRESETS and not overwrite:
            raise ValueError(f"RuleSet '{name}' already exists. Use overwrite=True to replace.")
        _PRESETS[name] = list(rules)

    @classmethod
    def get(cls, name: str) -> list[str]:
        """Return the list of rule strings for a preset."""
        if name not in _PRESETS:
            raise KeyError(f"Unknown RuleSet '{name}'. Available: {list(_PRESETS)}")
        return list(_PRESETS[name])

    @classmethod
    def schema_rules(cls, name: str) -> list[Rule]:
        """Return a list of Rule objects for use in Schema()."""
        return [Rule(r) for r in cls.get(name)]

    @classmethod
    def validate(cls, value: Any, name: str) -> Any:
        """Validate value against a named preset (raises ValidationError on failure)."""
        return validate(value, *cls.get(name))

    @classmethod
    def is_valid(cls, value: Any, name: str) -> bool:
        """Return True if value passes all rules in the preset."""
        try:
            cls.validate(value, name)
            return True
        except (ValidationError, KeyError):
            return False

    @classmethod
    def list(cls) -> list[str]:
        """Return all registered preset names."""
        return sorted(_PRESETS.keys())

    @classmethod
    def describe(cls, name: str) -> str:
        """Return a human-readable description of a preset's rules."""
        rules = cls.get(name)
        lines = [f"RuleSet '{name}':"]
        for r in rules:
            lines.append(f"  - {r}")
        return "\n".join(lines)

    @classmethod
    def extend(cls, name: str, extra_rules: list[str], new_name: str | None = None) -> str:
        """
        Extend an existing preset with additional rules.
        If new_name is given, creates a new preset. Otherwise mutates in place.
        Returns the name of the (possibly new) preset.
        """
        base = cls.get(name)
        combined = base + extra_rules
        target = new_name or name
        _PRESETS[target] = combined
        return target
