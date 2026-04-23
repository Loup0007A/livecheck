"""
livecheck.extras — Extra utilities: batch_validate, SchemaBuilder,
explain, suggest, validate_args, i18n rule support.
"""
from __future__ import annotations
import re
import csv
import io
from typing import Any
from .core import Schema, Rule, ValidationError
from .compiler import compile_rule, _fuzzy_normalize, PATTERNS, _CANONICAL_RULES, _CORRECTIONS


# ══════════════════════════════════════════════════════════════════════════════
# explain() — explain a rule in plain language
# ══════════════════════════════════════════════════════════════════════════════

_EXPLANATIONS: dict[str, str] = {
    "must be a positive number": "The value must be a number strictly greater than 0.",
    "must be a negative number": "The value must be a number strictly less than 0.",
    "must be between X and Y": "The value must be a number between the two given bounds (inclusive).",
    "must be greater than N": "The value must be strictly greater than N.",
    "must be less than N": "The value must be strictly less than N.",
    "must be an integer": "The value must be a whole number (int), not a float or boolean.",
    "must be even": "The value must be an integer divisible by 2.",
    "must be odd": "The value must be an integer NOT divisible by 2.",
    "must be a prime number": "The value must be a prime number (divisible only by 1 and itself).",
    "must be a perfect square": "The value must be an integer that is the square of another integer (e.g. 4, 9, 16).",
    "must be a multiple of N": "The value must be divisible by N with no remainder.",
    "must be a valid email": "The value must be a syntactically correct email address (user@domain.tld).",
    "must be a valid url": "The value must start with http:// or https:// and be a valid URL.",
    "must be a valid uuid": "The value must follow the UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.",
    "must be a valid ip address": "The value must be a valid IPv4 or IPv6 address.",
    "must be a valid ipv4 address": "The value must be a valid IPv4 address (e.g. 192.168.1.1).",
    "must be a valid ipv6 address": "The value must be a valid IPv6 address.",
    "must be a valid slug": "The value must be lowercase, contain only letters/digits and hyphens, like 'my-blog-post'.",
    "must be a valid hex color": "The value must be a CSS hex color: #RGB or #RRGGBB.",
    "must be a palindrome": "The value must read the same forwards and backwards.",
    "must be trimmed": "The value must have no leading or trailing whitespace.",
    "must be a valid password": "The value must have 8+ chars, 1 uppercase, 1 lowercase, 1 digit, 1 special char.",
    "must be a valid date": "The value must be a parseable date string (e.g. 2024-01-15, 15/01/2024).",
    "must be a valid time": "The value must be a time string HH:MM or HH:MM:SS.",
    "must be a valid phone number": "The value must be a phone number with 7-20 digits (spaces, dashes, parentheses allowed).",
    "must be a valid credit card number": "The value must pass the Luhn algorithm (validates most card numbers).",
    "must be a valid json": "The value must be a string that parses as valid JSON.",
    "must be a boolean": "The value must be exactly True or False (not 0/1).",
    "must be a list": "The value must be a Python list.",
    "must be a dict": "The value must be a Python dict.",
    "must have length at least N": "The value (string or list) must have at least N characters/items.",
    "must have length at most N": "The value (string or list) must have at most N characters/items.",
    "must be a valid latitude": "The value must be a float between -90 and 90.",
    "must be a valid longitude": "The value must be a float between -180 and 180.",
    "must be a valid probability": "The value must be a float between 0.0 and 1.0.",
    "must be a valid currency code": "The value must be an ISO 4217 currency code (USD, EUR, GBP, etc.).",
    "must be a valid country code": "The value must be an ISO 3166-1 alpha-2 country code (US, FR, DE, etc.).",
    "must be a valid port number": "The value must be an integer between 0 and 65535.",
    "must be a valid md5 hash": "The value must be a 32-character hexadecimal MD5 hash.",
    "must be a valid sha256 hash": "The value must be a 64-character hexadecimal SHA-256 hash.",
    "must be a valid jwt token": "The value must be a JWT: three base64url-encoded parts separated by dots.",
    "must be a valid cron expression": "The value must be a cron expression with 5 space-separated fields.",
    "must be a valid env var name": "The value must be UPPER_CASE and start with a letter or underscore.",
    "must be a valid python identifier": "The value must be a valid Python variable name (not a keyword).",
    "must be a valid username": "The value must be 3-30 chars using letters, digits, underscores, hyphens or dots.",
    "must have unique items": "The list must not contain any duplicate values.",
    "must be a sorted list": "The list must be sorted in ascending order.",
    "must be a fibonacci number": "The value must appear in the Fibonacci sequence (1,1,2,3,5,8,13,…).",
    "must be a roman numeral": "The value must be a valid Roman numeral (e.g. XIV, XLII, MCMXCIX).",
    "must be a valid mime type": "The value must follow the pattern type/subtype (e.g. image/jpeg, text/html).",
    "must be a valid locale": "The value must be a locale code like en_US or fr_FR.",
}


def explain(rule: str) -> str:
    """
    Return a plain English explanation of what a validation rule does.

    Example::

        >>> explain("must be a valid email")
        'The value must be a syntactically correct email address (user@domain.tld).'

        >>> explain("must be between X and Y")
        'The value must be a number between the two given bounds (inclusive).'
    """
    text = rule.strip().rstrip(".")
    norm = _fuzzy_normalize(text)

    # Try exact / normalised match against known explanations
    for attempt in [text, norm, text.lower(), norm.lower()]:
        if attempt in _EXPLANATIONS:
            return _EXPLANATIONS[attempt]

    # Parameterised rules: strip numeric args and try template key
    generalised = re.sub(r"\d+(?:\.\d+)?", "N", text)
    if generalised in _EXPLANATIONS:
        return _EXPLANATIONS[generalised]
    generalised_lower = generalised.lower()
    if generalised_lower in _EXPLANATIONS:
        return _EXPLANATIONS[generalised_lower]

    # Try to compile and auto-generate a description
    try:
        fn = compile_rule(text)
        doc = getattr(fn, '__doc__', None) or text
        return f"Compiled rule: '{doc}'. No detailed explanation available yet."
    except ValueError:
        return f"Rule '{text}' is not recognised. Check livecheck.list_patterns() for supported rules."


# ══════════════════════════════════════════════════════════════════════════════
# suggest() — given a value, suggest relevant rules
# ══════════════════════════════════════════════════════════════════════════════

def suggest(value: Any, max_results: int = 8) -> list[str]:
    """
    Suggest validation rules that make sense for the given value.

    Example::

        >>> suggest("alice@example.com")
        ['must be a non-empty string', 'must be a valid email', 'must contain only ascii', ...]

        >>> suggest(42)
        ['must be a number', 'must be an integer', 'must be a positive number', 'must be even', ...]
    """
    candidates: list[str] = []

    if isinstance(value, bool):
        candidates = ["must be a boolean", "must be truthy" if value else "must be falsy"]

    elif isinstance(value, int):
        candidates = [
            "must be an integer",
            "must be a number",
            "must be a positive number" if value > 0 else "must be a negative number" if value < 0 else "must be non-zero",
            "must be even" if value % 2 == 0 else "must be odd",
            f"must be between {max(0, value-100)} and {value+100}",
            f"must be greater than {value-1}",
            f"must be less than {value+1}",
        ]
        import math
        if value >= 0 and int(math.isqrt(value))**2 == value:
            candidates.append("must be a perfect square")
        if value >= 2:
            def is_prime(n):
                if n < 2: return False
                for i in range(2, int(n**0.5)+1):
                    if n % i == 0: return False
                return True
            if is_prime(value):
                candidates.append("must be a prime number")
        if value >= 0 and value <= 100:
            candidates.append("must be a percentage")
        if 0 <= value <= 65535:
            candidates.append("must be a valid port number")
        if 1000 <= value <= 9999:
            candidates.append("must be a valid year")
        if 1 <= value <= 12:
            candidates.append("must be a valid month")

    elif isinstance(value, float):
        candidates = [
            "must be a number",
            "must be a float",
            "must be a positive number" if value > 0 else "must be a negative number",
            f"must be between {value-10:.2f} and {value+10:.2f}",
        ]
        if 0.0 <= value <= 1.0:
            candidates.append("must be a valid probability")
        if 0 <= value <= 100:
            candidates.append("must be a percentage")
        if -90 <= value <= 90:
            candidates.append("must be a valid latitude")
        if -180 <= value <= 180:
            candidates.append("must be a valid longitude")

    elif isinstance(value, str):
        candidates = ["must be a non-empty string"] if value else ["must not be none"]
        candidates += ["must be a string"]
        if re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value):
            candidates.append("must be a valid email")
        if re.match(r"^https?://", value):
            candidates.append("must be a valid url")
        if re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", value, re.I):
            candidates.append("must be a valid uuid")
        if re.match(r"^[a-f0-9]{32}$", value, re.I):
            candidates.append("must be a valid md5 hash")
        if re.match(r"^[a-f0-9]{64}$", value, re.I):
            candidates.append("must be a valid sha256 hash")
        if re.match(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$", value):
            candidates.append("must be a valid hex color")
        if re.match(r"^\+?[\d\s\-().]{7,20}$", value):
            candidates.append("must be a valid phone number")
        if re.match(r"^\d{4}-\d{2}-\d{2}$", value):
            candidates.append("must be a valid date")
        if re.match(r"^[0-9A-Za-z+/]+=*$", value) and len(value) % 4 == 0:
            candidates.append("must be valid base64")
        if value == value.lower():
            candidates.append("must be lowercase")
        if value == value.upper() and value.isalpha():
            candidates.append("must be uppercase")
        if value.isalpha():
            candidates.append("must contain only letters")
        if value.isdigit():
            candidates.append("must contain only digits")
        if value.isalnum():
            candidates.append("must contain only alphanumeric characters")
        if value.isascii():
            candidates.append("must contain only ascii characters")
        if value == value.strip():
            candidates.append("must be trimmed")
        if re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", value):
            candidates.append("must be a valid slug")
        if re.match(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$", value):
            candidates.append("must be a valid email address")
        if len(value) >= 3:
            candidates.append(f"must have length at least 3")
        candidates.append(f"must have length at most {max(len(value), 255)}")
        candidates.append(f"must be one of {value}, other_value")

    elif isinstance(value, list):
        candidates = ["must be a list", "must be a non-empty list" if value else "must not be none"]
        candidates.append(f"must have at least {len(value)} items")
        candidates.append(f"must have at most {len(value)} items")
        if len(value) == len(set(str(i) for i in value)):
            candidates.append("must have unique items")
        try:
            if value == sorted(value):
                candidates.append("must be a sorted list")
        except TypeError:
            pass
        if all(isinstance(i, (int, float)) and not isinstance(i, bool) for i in value):
            candidates.append("must contain only numeric items")
        if all(isinstance(i, str) for i in value):
            candidates.append("must contain only string items")

    elif isinstance(value, dict):
        candidates = ["must be a dict", "must be a non-empty dict" if value else "must not be none"]
        for key in list(value.keys())[:3]:
            candidates.append(f"must contain the key '{key}'")

    elif value is None:
        candidates = ["must be none", "must not be none"]

    return candidates[:max_results]


# ══════════════════════════════════════════════════════════════════════════════
# batch_validate() — validate a list of dicts and produce a report
# ══════════════════════════════════════════════════════════════════════════════

from dataclasses import dataclass, field as dc_field


@dataclass
class BatchReport:
    """Report from batch_validate()."""
    total: int
    valid: int
    invalid: int
    errors_by_row: dict[int, dict[str, list[str]]] = dc_field(default_factory=dict)

    @property
    def pass_rate(self) -> float:
        return (self.valid / self.total * 100) if self.total else 0.0

    def summary(self) -> str:
        lines = [
            f"\nBatch validation: {self.valid}/{self.total} valid ({self.pass_rate:.1f}%)",
            f"Errors in {len(self.errors_by_row)} row(s):",
        ]
        for row_idx, field_errors in list(self.errors_by_row.items())[:20]:
            lines.append(f"  Row {row_idx}:")
            for field, msgs in field_errors.items():
                for msg in msgs:
                    lines.append(f"    [{field}] {msg}")
        if len(self.errors_by_row) > 20:
            lines.append(f"  ... and {len(self.errors_by_row) - 20} more rows.")
        return "\n".join(lines)

    def to_csv(self) -> str:
        """Export the error report as CSV string."""
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["row", "field", "error"])
        for row_idx, field_errors in self.errors_by_row.items():
            for field, msgs in field_errors.items():
                for msg in msgs:
                    writer.writerow([row_idx, field, msg])
        return buf.getvalue()

    def invalid_rows(self) -> list[int]:
        return list(self.errors_by_row.keys())


def batch_validate(
    data: list[dict],
    schema: Schema,
    *,
    stop_at: int | None = None,
) -> BatchReport:
    """
    Validate an entire list of dicts against a schema.

    Parameters
    ----------
    data : list[dict]
        Each element is a record to validate.
    schema : Schema
        The schema to apply to each record.
    stop_at : int | None
        If given, stop after this many invalid rows.

    Returns
    -------
    BatchReport
        Contains total/valid/invalid counts and per-row error details.

    Example::

        schema = Schema({"email": Rule("must be a valid email"), "age": Rule("must be between 18 and 120")})
        report = batch_validate(users, schema)
        print(report.summary())
        print(report.to_csv())
    """
    valid = 0
    errors_by_row: dict[int, dict[str, list[str]]] = {}

    for i, row in enumerate(data):
        row_errors = schema.errors(row)
        if row_errors:
            errors_by_row[i] = row_errors
            if stop_at is not None and len(errors_by_row) >= stop_at:
                break
        else:
            valid += 1

    return BatchReport(
        total=len(data),
        valid=valid,
        invalid=len(errors_by_row),
        errors_by_row=errors_by_row,
    )


# ══════════════════════════════════════════════════════════════════════════════
# SchemaBuilder — infer schema from example data
# ══════════════════════════════════════════════════════════════════════════════

class SchemaBuilder:
    """
    Infer a Schema automatically from a sample dict (or list of dicts).

    Example::

        builder = SchemaBuilder()
        builder.learn({"name": "Alice", "age": 30, "email": "alice@example.com"})
        builder.learn({"name": "Bob", "age": 25, "email": "bob@example.com"})
        schema = builder.build()
        print(builder.describe())
    """

    def __init__(self):
        self._samples: list[dict] = []

    def learn(self, sample: dict | list) -> "SchemaBuilder":
        """Add a sample record (or list of records) to the builder."""
        if isinstance(sample, list):
            self._samples.extend(sample)
        else:
            self._samples.append(sample)
        return self

    def _infer_rules(self, key: str, values: list[Any]) -> list[str]:
        """Infer plausible rules for a field from its observed values."""
        non_none = [v for v in values if v is not None]
        if not non_none:
            return ["must be none"]

        rules: list[str] = []
        types = set(type(v).__name__ for v in non_none)

        # All same type
        if len(types) == 1:
            t = types.pop()
            if t == "int":
                rules.append("must be an integer")
                mn, mx = min(non_none), max(non_none)
                if mn >= 0: rules.append("must be a positive number")
                rules.append(f"must be between {mn} and {mx}")
            elif t == "float":
                rules.append("must be a number")
                mn, mx = min(non_none), max(non_none)
                rules.append(f"must be between {mn:.4f} and {mx:.4f}")
            elif t == "str":
                rules.append("must be a non-empty string" if all(v for v in non_none) else "must be a string")
                lengths = [len(v) for v in non_none]
                if min(lengths) > 1:
                    rules.append(f"must have length at least {min(lengths)}")
                if max(lengths) < 10000 and max(lengths) != min(lengths):
                    rules.append(f"must have length at most {max(lengths)}")
                # Detect patterns
                if all(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v) for v in non_none):
                    rules.append("must be a valid email")
                elif all(re.match(r"^https?://", v) for v in non_none):
                    rules.append("must be a valid url")
                elif all(re.match(r"^\d{4}-\d{2}-\d{2}$", v) for v in non_none):
                    rules.append("must be a valid date")
                elif all(re.match(r"^\+?[\d\s\-().]{7,20}$", v) for v in non_none):
                    rules.append("must be a valid phone number")
                elif all(re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", v, re.I) for v in non_none):
                    rules.append("must be a valid uuid")
                elif len(set(non_none)) <= 10 and len(non_none) >= 3:
                    choices = ", ".join(sorted(set(non_none)))
                    rules.append(f"must be one of {choices}")
                if all(v == v.lower() for v in non_none if v):
                    rules.append("must be lowercase")
                if all(v == v.strip() for v in non_none):
                    rules.append("must be trimmed")
            elif t == "bool":
                rules.append("must be a boolean")
            elif t == "list":
                rules.append("must be a list")
                if all(v for v in non_none):
                    rules.append("must be a non-empty list")

        if None in values:
            # field is sometimes null → mark optional (note in description only)
            pass

        return rules or ["must not be none"]

    def build(self) -> Schema:
        """Build and return the inferred Schema."""
        if not self._samples:
            raise ValueError("No samples provided. Call .learn(sample) first.")

        all_keys: set[str] = set()
        for s in self._samples:
            all_keys.update(s.keys())

        fields: dict[str, list[Rule]] = {}
        for key in all_keys:
            values = [s.get(key) for s in self._samples]
            rule_texts = self._infer_rules(key, values)
            rules = []
            for rt in rule_texts:
                try:
                    rules.append(Rule(rt))
                except ValueError:
                    pass
            if rules:
                fields[key] = rules

        return Schema(fields)

    def describe(self) -> str:
        """Print a human-readable description of the inferred schema."""
        if not self._samples:
            return "No samples yet."

        all_keys: set[str] = set()
        for s in self._samples:
            all_keys.update(s.keys())

        lines = [f"Inferred schema from {len(self._samples)} sample(s):"]
        for key in sorted(all_keys):
            values = [s.get(key) for s in self._samples]
            rules = self._infer_rules(key, values)
            nullable = any(v is None for v in values)
            opt = " (optional)" if nullable else ""
            lines.append(f"  {key}{opt}:")
            for r in rules:
                lines.append(f"    - {r}")
        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
# @validate_args — inline argument validation via annotations
# ══════════════════════════════════════════════════════════════════════════════

import functools
import inspect


def validate_args(**rules: str | list[str]):
    """
    Decorator that validates function arguments before the function runs.

    Rules are given as keyword arguments matching parameter names.
    Multiple rules per argument can be given as a list.

    Example::

        @validate_args(
            email="must be a valid email",
            age=["must be an integer", "must be between 18 and 120"],
            username=["must be a non-empty string", "must have length at least 3"],
        )
        def register(email, age, username):
            ...
    """
    compiled: dict[str, list] = {}
    for param, rule_or_rules in rules.items():
        rule_list = [rule_or_rules] if isinstance(rule_or_rules, str) else list(rule_or_rules)
        compiled[param] = []
        for rt in rule_list:
            try:
                compiled[param].append((rt, compile_rule(rt)))
            except ValueError:
                norm = _fuzzy_normalize(rt)
                try:
                    compiled[param].append((rt, compile_rule(norm)))
                except ValueError:
                    raise ValueError(f"@validate_args: could not compile rule {rt!r} for param '{param}'")

    def decorator(fn):
        sig = inspect.signature(fn)

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
            except TypeError as e:
                raise TypeError(str(e))

            errors: dict[str, list[str]] = {}
            for param, rule_pairs in compiled.items():
                if param in bound.arguments:
                    value = bound.arguments[param]
                    for rule_text, validator_fn in rule_pairs:
                        ok, msg = validator_fn(value)
                        if not ok:
                            errors.setdefault(param, []).append(msg)

            if errors:
                raise ValidationError(errors)

            return fn(*args, **kwargs)

        return wrapper
    return decorator


# ══════════════════════════════════════════════════════════════════════════════
# i18n — add French, German, Spanish, Portuguese rule aliases
# ══════════════════════════════════════════════════════════════════════════════

_I18N_ALIASES: dict[str, str] = {
    # French
    "doit être positif": "must be a positive number",
    "doit être négatif": "must be a negative number",
    "doit être un entier": "must be an integer",
    "doit être un nombre": "must be a number",
    "doit être un email valide": "must be a valid email",
    "doit être une url valide": "must be a valid url",
    "doit être une chaîne": "must be a non-empty string",
    "doit être vrai": "must be truthy",
    "doit être faux": "must be falsy",
    "ne doit pas être vide": "must not be none",
    "doit être un booléen": "must be a boolean",
    "doit être une liste": "must be a list",
    "doit être un dictionnaire": "must be a dict",
    "doit être unique": "must have unique items",
    "doit être trié": "must be a sorted list",
    "doit être un palindrome": "must be a palindrome",
    "doit être en minuscules": "must be lowercase",
    "doit être en majuscules": "must be uppercase",
    "doit être un mot de passe valide": "must be a valid password",
    "doit être une date valide": "must be a valid date",
    "doit être un numéro de téléphone valide": "must be a valid phone number",
    "doit être un nombre premier": "must be a prime number",
    "doit être pair": "must be even",
    "doit être impair": "must be odd",
    "doit être dans le passé": "must be in the past",
    "doit être dans le futur": "must be in the future",
    "doit être un code pays valide": "must be a valid country code",
    "doit être un code devise valide": "must be a valid currency code",
    "doit être une adresse ip valide": "must be a valid ip address",
    "doit être un uuid valide": "must be a valid uuid",
    "doit être une couleur hexadécimale valide": "must be a valid hex color",
    # German
    "muss positiv sein": "must be a positive number",
    "muss negativ sein": "must be a negative number",
    "muss eine ganze zahl sein": "must be an integer",
    "muss eine gültige e-mail sein": "must be a valid email",
    "muss eine gültige url sein": "must be a valid url",
    "muss ein string sein": "must be a non-empty string",
    "darf nicht leer sein": "must not be none",
    "muss ein boolean sein": "must be a boolean",
    "muss eine liste sein": "must be a list",
    "muss gerade sein": "must be even",
    "muss ungerade sein": "must be odd",
    "muss ein gültiges passwort sein": "must be a valid password",
    "muss ein gültiges datum sein": "must be a valid date",
    "muss eine primzahl sein": "must be a prime number",
    "muss eindeutig sein": "must have unique items",
    # Spanish
    "debe ser positivo": "must be a positive number",
    "debe ser negativo": "must be a negative number",
    "debe ser un entero": "must be an integer",
    "debe ser un email válido": "must be a valid email",
    "debe ser una url válida": "must be a valid url",
    "debe ser una cadena": "must be a non-empty string",
    "no debe estar vacío": "must not be none",
    "debe ser un booleano": "must be a boolean",
    "debe ser una lista": "must be a list",
    "debe ser par": "must be even",
    "debe ser impar": "must be odd",
    "debe ser una contraseña válida": "must be a valid password",
    "debe ser una fecha válida": "must be a valid date",
    "debe ser primo": "must be a prime number",
    "debe ser único": "must have unique items",
    "debe ser ordenado": "must be a sorted list",
    # Portuguese
    "deve ser positivo": "must be a positive number",
    "deve ser negativo": "must be a negative number",
    "deve ser um inteiro": "must be an integer",
    "deve ser um email válido": "must be a valid email",
    "deve ser uma url válida": "must be a valid url",
    "deve ser uma string": "must be a non-empty string",
    "não deve ser vazio": "must not be none",
    "deve ser um booleano": "must be a boolean",
    "deve ser uma lista": "must be a list",
    "deve ser par": "must be even",
    "deve ser ímpar": "must be odd",
    "deve ser uma senha válida": "must be a valid password",
    "deve ser uma data válida": "must be a valid date",
    "deve ser primo": "must be a prime number",
    "deve ser único": "must have unique items",
}

# Register i18n aliases as corrections in the fuzzy layer
for alias, canonical in _I18N_ALIASES.items():
    _CORRECTIONS[alias.lower()] = canonical


def add_i18n_rule(alias: str, canonical: str) -> None:
    """Register a custom language alias for an existing rule."""
    _CORRECTIONS[alias.lower()] = canonical
    _I18N_ALIASES[alias.lower()] = canonical


def list_i18n_aliases(lang: str | None = None) -> dict[str, str]:
    """
    Return i18n rule aliases, optionally filtered by language prefix.

    Supported lang values: 'fr', 'de', 'es', 'pt'
    """
    prefixes = {
        "fr": ["doit ", "ne doit"],
        "de": ["muss ", "darf "],
        "es": ["debe "],
        "pt": ["deve ", "não "],
    }
    if lang is None:
        return dict(_I18N_ALIASES)
    starts = prefixes.get(lang.lower(), [])
    return {k: v for k, v in _I18N_ALIASES.items() if any(k.startswith(p) for p in starts)}
