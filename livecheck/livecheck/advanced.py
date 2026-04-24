"""
livecheck.advanced — Power-user features:

- ConditionalRule   : rule active only when a condition is met
- DependentSchema   : fields validated differently depending on sibling values
- diff_validate()   : validate a patch/update is a valid transition
- watch()           : observe a dict and auto-validate on changes
- generate()        : generate random values that pass a rule
- from_json_schema(): convert JSON Schema dict → livecheck Schema
- to_json_schema()  : convert livecheck Schema → JSON Schema dict
"""
from __future__ import annotations

import re
import random
import string
import time
import copy
import threading
from typing import Any, Callable, Iterator
from dataclasses import dataclass, field

from .core import Rule, Schema, ValidationError, validate
from .compiler import compile_rule, _fuzzy_normalize, PATTERNS


# ══════════════════════════════════════════════════════════════════════════════
# ConditionalRule
# ══════════════════════════════════════════════════════════════════════════════

class ConditionalRule:
    """
    A rule that only applies when a condition is satisfied.

    condition : callable(value) -> bool  OR  a rule string
    rule      : the rule to apply when condition is True

    Example::

        # Only validate as email if the value contains '@'
        r = ConditionalRule(
            condition=lambda v: isinstance(v, str) and "@" in v,
            rule="must be a valid email",
            label="email_if_looks_like_one"
        )

        # Only check age if role is 'adult'
        r = ConditionalRule(
            condition="must be greater than 0",  # condition is itself a rule
            rule="must be between 18 and 120",
        )
    """
    def __init__(self, condition: Callable | str, rule: str,
                 label: str = "", else_rule: str | None = None):
        self.label = label or f"conditional({rule!r})"
        self.rule = rule
        self.else_rule = else_rule
        self._rule_fn = compile_rule(_fuzzy_normalize(rule))
        self._else_fn = compile_rule(_fuzzy_normalize(else_rule)) if else_rule else None

        if isinstance(condition, str):
            cond_fn = compile_rule(_fuzzy_normalize(condition))
            self._condition = lambda v: cond_fn(v)[0]
        else:
            self._condition = condition

    def check(self, value: Any) -> tuple[bool, str]:
        if self._condition(value):
            ok, msg = self._rule_fn(value)
            return ok, msg
        elif self._else_fn:
            ok, msg = self._else_fn(value)
            return ok, msg
        return True, ""

    @property
    def text(self):
        return f"if condition → {self.rule}"


# ══════════════════════════════════════════════════════════════════════════════
# DependentSchema
# ══════════════════════════════════════════════════════════════════════════════

class DependentSchema(Schema):
    """
    Schema where a field's rules depend on another field's value.

    Example::

        schema = DependentSchema(
            fields={
                "age": Rule("must be an integer"),
                "discount": Rule("must be a percentage"),
            },
            dependencies={
                "discount": {
                    # extra rules for 'discount' when role == 'vip'
                    "role": {
                        "vip":      ["must be between 10 and 50"],
                        "standard": ["must be between 0 and 20"],
                        "_default": ["must be between 0 and 10"],
                    }
                }
            }
        )
    """
    def __init__(self,
                 fields: dict[str, "Rule | list[Rule]"],
                 dependencies: dict[str, dict[str, dict[str, list[str]]]] | None = None):
        super().__init__(fields)
        self._deps = dependencies or {}
        # Pre-compile dependent rules
        self._compiled_deps: dict[str, dict[str, dict[str, list]]] = {}
        for field_name, dep_map in self._deps.items():
            self._compiled_deps[field_name] = {}
            for trigger_field, value_map in dep_map.items():
                self._compiled_deps[field_name][trigger_field] = {}
                for trigger_val, rule_texts in value_map.items():
                    rules = []
                    for rt in rule_texts:
                        try:
                            rules.append((rt, compile_rule(rt)))
                        except ValueError:
                            norm = _fuzzy_normalize(rt)
                            rules.append((norm, compile_rule(norm)))
                    self._compiled_deps[field_name][trigger_field][trigger_val] = rules

    def validate(self, data: dict[str, Any], *, strict: bool = False) -> dict[str, Any]:
        # Base validation
        errors: dict[str, list[str]] = {}
        if strict:
            for k in set(data) - set(self._fields):
                errors.setdefault(k, []).append("Unknown field (strict mode)")

        for name, rules in self._fields.items():
            value = data.get(name)
            for rule in rules:
                ok, msg = rule.check(value)
                if not ok:
                    errors.setdefault(name, []).append(msg)

        # Dependent rules
        for field_name, dep_map in self._compiled_deps.items():
            value = data.get(field_name)
            for trigger_field, value_map in dep_map.items():
                trigger_val = str(data.get(trigger_field, ""))
                rule_pairs = value_map.get(trigger_val) or value_map.get("_default", [])
                for rule_text, rule_fn in rule_pairs:
                    ok, msg = rule_fn(value)
                    if not ok:
                        errors.setdefault(field_name, []).append(
                            f"[when {trigger_field}={trigger_val!r}] {msg}"
                        )

        if errors:
            raise ValidationError(errors)
        return data


# ══════════════════════════════════════════════════════════════════════════════
# diff_validate() — validate state transitions
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class TransitionRule:
    """A rule that governs how a field can change from old → new value."""
    field: str
    description: str
    check: Callable[[Any, Any], tuple[bool, str]]

    @staticmethod
    def immutable(field: str) -> "TransitionRule":
        """Field cannot change once set."""
        return TransitionRule(
            field=field,
            description=f"'{field}' is immutable",
            check=lambda old, new: (old == new or old is None,
                                    f"Field '{field}' is immutable: cannot change {old!r} → {new!r}")
        )

    @staticmethod
    def append_only(field: str) -> "TransitionRule":
        """List field can only grow, never shrink."""
        return TransitionRule(
            field=field,
            description=f"'{field}' is append-only",
            check=lambda old, new: (
                not isinstance(old, list) or (isinstance(new, list) and len(new) >= len(old)),
                f"Field '{field}' is append-only: cannot shrink {old!r} → {new!r}"
            )
        )

    @staticmethod
    def monotone_increase(field: str) -> "TransitionRule":
        """Numeric field can only increase."""
        return TransitionRule(
            field=field,
            description=f"'{field}' can only increase",
            check=lambda old, new: (old is None or new >= old,
                                    f"Field '{field}' can only increase: {old!r} → {new!r}")
        )

    @staticmethod
    def allowed_transitions(field: str, transitions: dict[Any, list[Any]]) -> "TransitionRule":
        """Field can only move to allowed states."""
        def _check(old, new):
            if old not in transitions:
                return True, ""
            allowed = transitions[old]
            if new not in allowed:
                return False, f"'{field}': invalid transition {old!r} → {new!r} (allowed: {allowed})"
            return True, ""
        return TransitionRule(field=field, description=f"'{field}' state machine", check=_check)

    @staticmethod
    def no_delete(field: str) -> "TransitionRule":
        """Field cannot be deleted (set to None/empty)."""
        return TransitionRule(
            field=field,
            description=f"'{field}' cannot be deleted",
            check=lambda old, new: (old is None or new not in (None, "", [], {}),
                                    f"Field '{field}' cannot be deleted: was {old!r}, got {new!r}")
        )


def diff_validate(
    old: dict[str, Any],
    new: dict[str, Any],
    schema: Schema | None = None,
    transition_rules: list[TransitionRule] | None = None,
) -> dict[str, Any]:
    """
    Validate that an update (old → new) is valid.

    Checks:
    1. The new state passes the schema (if provided)
    2. All transition rules are satisfied

    Returns the new dict if valid, raises ValidationError otherwise.

    Example::

        order_schema = Schema({"status": Rule("must be one of pending, paid, shipped, delivered, cancelled")})
        order_transitions = [
            TransitionRule.allowed_transitions("status", {
                "pending":   ["paid", "cancelled"],
                "paid":      ["shipped", "cancelled"],
                "shipped":   ["delivered"],
                "delivered": [],
                "cancelled": [],
            }),
            TransitionRule.immutable("id"),
            TransitionRule.monotone_increase("version"),
        ]
        diff_validate(old_order, new_order, schema=order_schema, transition_rules=order_transitions)
    """
    errors: dict[str, list[str]] = {}

    # Schema check on new state
    if schema is not None:
        schema_errors = schema.errors(new)
        for field, msgs in schema_errors.items():
            errors.setdefault(field, []).extend(msgs)

    # Transition rule checks
    for tr in (transition_rules or []):
        old_val = old.get(tr.field)
        new_val = new.get(tr.field)
        ok, msg = tr.check(old_val, new_val)
        if not ok:
            errors.setdefault(tr.field, []).append(msg)

    if errors:
        raise ValidationError(errors)
    return new


# ══════════════════════════════════════════════════════════════════════════════
# watch() — observe a dict, auto-validate on changes
# ══════════════════════════════════════════════════════════════════════════════

class WatchedDict:
    """
    A dict-like object that validates itself on every write.
    Any violation calls the on_violation callback (default: raise).

    Example::

        d = watch(
            {"name": "Alice", "age": 30},
            schema=Schema({
                "name": Rule("must be a non-empty string"),
                "age":  Rule("must be between 0 and 150"),
            }),
            on_violation=lambda errs: print("INVALID:", errs)
        )
        d["age"] = 25   # OK
        d["age"] = -5   # triggers on_violation
    """
    def __init__(self, data: dict, schema: Schema,
                 on_violation: Callable | None = None):
        object.__setattr__(self, "_data", dict(data))
        object.__setattr__(self, "_schema", schema)
        object.__setattr__(self, "_on_violation", on_violation)
        object.__setattr__(self, "_history", [])
        # Validate initial state
        errs = schema.errors(data)
        if errs:
            self._handle_violation(errs)

    def _handle_violation(self, errors: dict):
        cb = object.__getattribute__(self, "_on_violation")
        if cb:
            cb(errors)
        else:
            raise ValidationError(errors)

    def __setitem__(self, key, value):
        data = object.__getattribute__(self, "_data")
        schema = object.__getattribute__(self, "_schema")
        history = object.__getattribute__(self, "_history")
        old = dict(data)
        data[key] = value
        errs = schema.errors(data)
        if errs:
            data[key] = old.get(key)  # rollback
            self._handle_violation(errs)
        else:
            history.append((time.time(), key, old.get(key), value))

    def __getitem__(self, key):
        return object.__getattribute__(self, "_data")[key]

    def __delitem__(self, key):
        data = object.__getattribute__(self, "_data")
        old = data.pop(key, None)
        schema = object.__getattribute__(self, "_schema")
        errs = schema.errors(data)
        if errs:
            data[key] = old  # rollback
            self._handle_violation(errs)

    def get(self, key, default=None):
        return object.__getattribute__(self, "_data").get(key, default)

    def update(self, other: dict):
        for k, v in other.items():
            self[k] = v

    def to_dict(self) -> dict:
        return dict(object.__getattribute__(self, "_data"))

    def history(self) -> list[tuple]:
        return list(object.__getattribute__(self, "_history"))

    def __repr__(self):
        return f"WatchedDict({object.__getattribute__(self, '_data')!r})"

    def __contains__(self, key):
        return key in object.__getattribute__(self, "_data")

    def keys(self): return object.__getattribute__(self, "_data").keys()
    def values(self): return object.__getattribute__(self, "_data").values()
    def items(self): return object.__getattribute__(self, "_data").items()


def watch(data: dict, schema: Schema,
          on_violation: Callable | None = None) -> WatchedDict:
    """
    Wrap a dict so every mutation is auto-validated.

    Parameters
    ----------
    data : dict
        Initial data.
    schema : Schema
        Validation schema applied on every write.
    on_violation : callable(errors) | None
        Called with the error dict when validation fails.
        If None, raises ValidationError.

    Returns
    -------
    WatchedDict
        A dict-like object that validates itself.
    """
    return WatchedDict(data, schema, on_violation)


# ══════════════════════════════════════════════════════════════════════════════
# generate() — produce valid random values for a rule
# ══════════════════════════════════════════════════════════════════════════════

def generate(rule: str, n: int = 1) -> Any | list[Any]:
    """
    Generate random values that satisfy a given rule.

    Useful for testing, seeding databases, generating mock data.

    Parameters
    ----------
    rule : str
        A rule string (same as used in validate()).
    n : int
        Number of values to generate (1 returns single value, >1 returns list).

    Example::

        generate("must be a valid email")       # 'user_4829@example.com'
        generate("must be between 1 and 100")   # 47
        generate("must be a valid uuid", n=3)   # ['...', '...', '...']
    """
    import uuid, hashlib
    rule_lower = rule.lower()

    def _one():
        # Email
        if "email" in rule_lower:
            user = "user_" + str(random.randint(1000, 99999))
            domains = ["example.com","test.org","sample.net","mock.io","demo.dev"]
            return f"{user}@{random.choice(domains)}"
        # UUID
        if "uuid" in rule_lower:
            return str(uuid.uuid4())
        # URL
        if "url" in rule_lower:
            slugs = ["foo","bar","hello","world","test","demo","api","app"]
            path = "/".join(random.choices(slugs, k=random.randint(1,3)))
            return f"https://{random.choice(['example','test','sample'])}.com/{path}"
        # Password
        if "strong password" in rule_lower:
            chars = string.ascii_uppercase[:5] + string.ascii_lowercase[:5] + string.digits[:5] + "!@#$%"
            base = ''.join(random.choices(string.ascii_lowercase, k=6))
            return base + random.choice(string.ascii_uppercase) + random.choice(string.digits) + random.choice("!@#$%_")
        if "password" in rule_lower:
            return "Secure@" + str(random.randint(100, 999))
        # Slug
        if "slug" in rule_lower:
            words = ["hello","world","foo","bar","test","demo","sample","mock"]
            return "-".join(random.choices(words, k=random.randint(2,4)))
        # Hex color
        if "hex color" in rule_lower:
            return "#{:06X}".format(random.randint(0, 0xFFFFFF))
        # IP
        if "ipv4" in rule_lower:
            return ".".join(str(random.randint(1,254)) for _ in range(4))
        if "ipv6" in rule_lower:
            return ":".join("{:04x}".format(random.randint(0, 0xFFFF)) for _ in range(8))
        if "ip address" in rule_lower or "valid ip" in rule_lower:
            return ".".join(str(random.randint(1,254)) for _ in range(4))
        # MD5/SHA hashes
        if "md5" in rule_lower:
            return hashlib.md5(str(random.random()).encode()).hexdigest()
        if "sha256" in rule_lower:
            return hashlib.sha256(str(random.random()).encode()).hexdigest()
        if "sha1" in rule_lower:
            return hashlib.sha1(str(random.random()).encode()).hexdigest()
        # JWT-like
        if "jwt" in rule_lower:
            def b64(s): return s.replace("+","-").replace("/","_").rstrip("=")
            import base64, json
            h = b64(base64.b64encode(b'{"alg":"HS256"}').decode())
            p = b64(base64.b64encode(json.dumps({"sub": str(uuid.uuid4())}).encode()).decode())
            s = b64(base64.b64encode(str(random.random()).encode()).decode())
            return f"{h}.{p}.{s}"
        # Date
        if "valid date" in rule_lower and "time" not in rule_lower:
            y = random.randint(2000, 2030)
            m = random.randint(1, 12)
            d = random.randint(1, 28)
            return f"{y:04d}-{m:02d}-{d:02d}"
        # Time
        if "valid time" in rule_lower:
            return f"{random.randint(0,23):02d}:{random.randint(0,59):02d}:{random.randint(0,59):02d}"
        # Datetime
        if "valid datetime" in rule_lower:
            y = random.randint(2000, 2030)
            m = random.randint(1, 12)
            d = random.randint(1, 28)
            H = random.randint(0, 23)
            M = random.randint(0, 59)
            return f"{y:04d}-{m:02d}-{d:02d} {H:02d}:{M:02d}:00"
        # Phone
        if "phone" in rule_lower:
            cc = random.choice(["+1","+33","+44","+49","+34"])
            n = "".join(str(random.randint(0,9)) for _ in range(9))
            return f"{cc} {n}"
        # Country code
        if "country code" in rule_lower:
            return random.choice(["US","FR","DE","GB","JP","CA","AU","BR","IN","IT"])
        # Currency code
        if "currency code" in rule_lower:
            return random.choice(["USD","EUR","GBP","JPY","CHF","CAD","AUD"])
        # Language code
        if "language code" in rule_lower:
            return random.choice(["en","fr","de","es","pt","zh","ja","ar","ru","it"])
        # Port
        if "port" in rule_lower:
            return random.randint(1024, 65535)
        # HTTP status
        if "http status" in rule_lower:
            return random.choice([200, 201, 204, 400, 401, 403, 404, 500])
        # HTTP method
        if "http method" in rule_lower:
            return random.choice(["GET","POST","PUT","PATCH","DELETE"])
        # Log level
        if "log level" in rule_lower:
            return random.choice(["DEBUG","INFO","WARNING","ERROR","CRITICAL"])
        # Semver
        if "semver" in rule_lower or "semantic version" in rule_lower:
            return f"{random.randint(0,9)}.{random.randint(0,20)}.{random.randint(0,99)}"
        # Username
        if "username" in rule_lower:
            return "user_" + ''.join(random.choices(string.ascii_lowercase, k=6))
        # Slug
        if "slug" in rule_lower:
            words = ["alpha","beta","gamma","hello","world","foo","bar"]
            return "-".join(random.choices(words, k=2))
        # camelCase
        if "camel" in rule_lower:
            words = ["foo","Bar","Baz","Qux"]
            return words[0].lower() + "".join(w.capitalize() for w in words[1:random.randint(2,3)])
        # snake_case
        if "snake" in rule_lower:
            words = ["foo","bar","baz","qux","hello","world"]
            return "_".join(random.choices(words, k=random.randint(2,3)))
        # Env var
        if "env var" in rule_lower:
            return "MY_" + "".join(random.choices(string.ascii_uppercase, k=6))
        # Python identifier
        if "python identifier" in rule_lower:
            return "var_" + "".join(random.choices(string.ascii_lowercase, k=5))
        # Boolean
        if "boolean" in rule_lower:
            return random.choice([True, False])
        # Positive number
        if "positive" in rule_lower and "number" in rule_lower:
            return random.randint(1, 1000)
        # Percentage
        if "percentage" in rule_lower:
            return random.uniform(0, 100)
        # Probability
        if "probability" in rule_lower:
            return round(random.random(), 4)
        # Latitude
        if "latitude" in rule_lower:
            return round(random.uniform(-90, 90), 6)
        # Longitude
        if "longitude" in rule_lower:
            return round(random.uniform(-180, 180), 6)
        # Integer range
        m = re.search(r"between\s+([\-\d]+)\s+and\s+([\-\d]+)", rule_lower)
        if m:
            lo, hi = int(m.group(1)), int(m.group(2))
            return random.randint(lo, hi)
        # Greater than N
        m = re.search(r"greater than\s+([\-\d]+)", rule_lower)
        if m:
            n_val = int(m.group(1))
            return n_val + random.randint(1, 100)
        # Less than N
        m = re.search(r"less than\s+([\-\d]+)", rule_lower)
        if m:
            n_val = int(m.group(1))
            return n_val - random.randint(1, 100)
        # one of
        m = re.search(r"one of\s+(.+)", rule_lower)
        if m:
            choices = [c.strip() for c in m.group(1).split(",")]
            return random.choice(choices)
        # non-empty string fallback
        if "string" in rule_lower:
            return "sample_" + ''.join(random.choices(string.ascii_lowercase, k=6))
        # integer fallback
        if "integer" in rule_lower or "number" in rule_lower:
            return random.randint(1, 100)
        # Generic fallback
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

    results = [_one() for _ in range(n)]
    return results[0] if n == 1 else results


# ══════════════════════════════════════════════════════════════════════════════
# from_json_schema() — convert JSON Schema → livecheck Schema
# ══════════════════════════════════════════════════════════════════════════════

def from_json_schema(json_schema: dict) -> Schema:
    """
    Convert a JSON Schema dict into a livecheck Schema.

    Supports: type, format, minimum, maximum, minLength, maxLength,
    pattern, enum, required, properties.

    Example::

        js = {
            "type": "object",
            "required": ["email", "age"],
            "properties": {
                "email": {"type": "string", "format": "email"},
                "age":   {"type": "integer", "minimum": 18, "maximum": 120},
                "tags":  {"type": "array", "minItems": 1},
            }
        }
        schema = from_json_schema(js)
    """
    fields: dict[str, list[Rule]] = {}
    props = json_schema.get("properties", {})
    required_fields = set(json_schema.get("required", []))

    _FORMAT_RULES: dict[str, str] = {
        "email":    "must be a valid email",
        "uri":      "must be a valid url",
        "url":      "must be a valid url",
        "uuid":     "must be a valid uuid",
        "date":     "must be a valid date",
        "time":     "must be a valid time",
        "date-time":"must be a valid datetime",
        "ipv4":     "must be a valid ipv4 address",
        "ipv6":     "must be a valid ipv6 address",
        "hostname": "must be a valid hostname",
    }
    _TYPE_RULES: dict[str, str] = {
        "string":  "must be a string",
        "integer": "must be an integer",
        "number":  "must be a number",
        "boolean": "must be a boolean",
        "array":   "must be a list",
        "object":  "must be a dict",
    }

    for field_name, prop in props.items():
        rules: list[str] = []

        if field_name in required_fields:
            rules.append("must be required")

        t = prop.get("type")
        if t and t in _TYPE_RULES:
            rules.append(_TYPE_RULES[t])

        fmt = prop.get("format")
        if fmt and fmt in _FORMAT_RULES:
            rules.append(_FORMAT_RULES[fmt])

        if "minimum" in prop and "maximum" in prop:
            rules.append(f"must be between {prop['minimum']} and {prop['maximum']}")
        elif "minimum" in prop:
            rules.append(f"must be greater than or equal to {prop['minimum']}")
        elif "maximum" in prop:
            rules.append(f"must be less than or equal to {prop['maximum']}")

        if "minLength" in prop and "maxLength" in prop:
            rules.append(f"must have length at least {prop['minLength']}")
            rules.append(f"must have length at most {prop['maxLength']}")
        elif "minLength" in prop:
            rules.append(f"must have length at least {prop['minLength']}")
        elif "maxLength" in prop:
            rules.append(f"must have length at most {prop['maxLength']}")

        if "pattern" in prop:
            rules.append(f"must match pattern '{prop['pattern']}'")

        if "enum" in prop:
            choices = ", ".join(str(e) for e in prop["enum"])
            rules.append(f"must be one of {choices}")

        if "minItems" in prop:
            rules.append(f"must have at least {prop['minItems']} items")
        if "maxItems" in prop:
            rules.append(f"must have at most {prop['maxItems']} items")

        compiled_rules = []
        for rt in rules:
            try:
                compiled_rules.append(Rule(rt))
            except ValueError:
                pass

        if compiled_rules:
            fields[field_name] = compiled_rules

    return Schema(fields)


# ══════════════════════════════════════════════════════════════════════════════
# to_json_schema() — convert livecheck Schema → JSON Schema
# ══════════════════════════════════════════════════════════════════════════════

def to_json_schema(schema: Schema, title: str = "") -> dict:
    """
    Export a livecheck Schema as a JSON Schema dict.

    Example::

        schema = Schema({
            "email": [Rule("must be a non-empty string"), Rule("must be a valid email")],
            "age":   Rule("must be between 18 and 120"),
        })
        js = to_json_schema(schema, title="User")
        import json
        print(json.dumps(js, indent=2))
    """
    props: dict[str, dict] = {}
    required_fields: list[str] = []

    for field_name, rules in schema._fields.items():
        prop: dict = {}
        rule_texts = [r.text for r in rules]

        for rt in rule_texts:
            rl = rt.lower()
            # Type inference
            if "must be an integer" in rl: prop.setdefault("type", "integer")
            elif "must be a float" in rl or "must be a number" in rl: prop.setdefault("type", "number")
            elif "must be a boolean" in rl: prop.setdefault("type", "boolean")
            elif "must be a list" in rl: prop.setdefault("type", "array")
            elif "must be a dict" in rl: prop.setdefault("type", "object")
            elif "must be a string" in rl or "string" in rl: prop.setdefault("type", "string")

            # Format inference
            if "valid email" in rl: prop["format"] = "email"
            elif "valid url" in rl: prop["format"] = "uri"
            elif "valid uuid" in rl: prop["format"] = "uuid"
            elif "valid date" in rl and "time" not in rl: prop["format"] = "date"
            elif "valid datetime" in rl: prop["format"] = "date-time"
            elif "valid time" in rl: prop["format"] = "time"
            elif "valid ipv4" in rl: prop["format"] = "ipv4"
            elif "valid ipv6" in rl: prop["format"] = "ipv6"
            elif "valid hostname" in rl: prop["format"] = "hostname"

            # Numeric bounds
            m = re.search(r"between ([\-\d.]+) and ([\-\d.]+)", rl)
            if m:
                prop["minimum"] = float(m.group(1))
                prop["maximum"] = float(m.group(2))
            m = re.search(r"greater than or equal to ([\-\d.]+)", rl)
            if m: prop["minimum"] = float(m.group(1))
            m = re.search(r"greater than ([\-\d.]+)", rl)
            if m: prop["exclusiveMinimum"] = float(m.group(1))
            m = re.search(r"less than or equal to ([\-\d.]+)", rl)
            if m: prop["maximum"] = float(m.group(1))
            m = re.search(r"less than ([\-\d.]+)", rl)
            if m: prop["exclusiveMaximum"] = float(m.group(1))

            # String length
            m = re.search(r"length at least (\d+)", rl)
            if m: prop["minLength"] = int(m.group(1))
            m = re.search(r"length at most (\d+)", rl)
            if m: prop["maxLength"] = int(m.group(1))

            # Pattern
            m = re.search(r"match pattern '([^']+)'", rl)
            if m: prop["pattern"] = m.group(1)

            # Enum
            m = re.search(r"be one of (.+)", rl)
            if m:
                choices = [c.strip() for c in m.group(1).split(",")]
                prop["enum"] = choices

            # Array items
            m = re.search(r"at least (\d+) items?", rl)
            if m: prop["minItems"] = int(m.group(1))
            m = re.search(r"at most (\d+) items?", rl)
            if m: prop["maxItems"] = int(m.group(1))

            # Required
            if "must be required" in rl or "must not be none" in rl:
                if field_name not in required_fields:
                    required_fields.append(field_name)

        props[field_name] = prop

    result: dict = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": props,
    }
    if required_fields:
        result["required"] = required_fields
    if title:
        result["title"] = title
    return result


# ══════════════════════════════════════════════════════════════════════════════
# async_validate() — async-friendly validate
# ══════════════════════════════════════════════════════════════════════════════

async def async_validate(value: Any, *rules: str) -> Any:
    """
    Async version of validate(). Useful inside async functions and FastAPI/aiohttp handlers.

    Example::

        async def create_user(email: str, age: int):
            await async_validate(email, "must be a valid email")
            await async_validate(age, "must be between 18 and 120")
    """
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: validate(value, *rules))


async def async_schema_validate(data: dict, schema: Schema) -> dict:
    """Async version of schema.validate()."""
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: schema.validate(data))
