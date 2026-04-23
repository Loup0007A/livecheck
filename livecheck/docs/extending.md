# Extending livecheck

## Adding a custom pattern

```python
from livecheck.compiler import pattern

@pattern(r"must be a valid french phone number", "must be a valid french phone number")
def _fr_phone(m, **kw):
    import re
    rx = re.compile(r"^(\+33|0)[1-9]\d{8}$")
    return lambda v: (
        isinstance(v, str) and bool(rx.match(v)),
        f"Expected French phone number, got {v!r}"
    )

# Now usable everywhere
from livecheck import validate
validate("+33612345678", "must be a valid french phone number")
```

Rules for writing patterns:

1. The decorator's first argument is a **case-insensitive regex** (flags are applied automatically).
2. The second argument is the **canonical description** shown in `list_patterns()`.
3. The factory function receives the regex match `m` — use `m.group(N)` to extract parameters.
4. Return a **lambda `(value) → (bool, str)`** — `True`/`""` on pass, `False`/message on fail.
5. Never raise inside the lambda — always return `(False, message)`.

## Adding i18n aliases

```python
from livecheck import add_i18n_rule

add_i18n_rule("deve ser um cpf válido",       "must match pattern '^\\d{11}$'")
add_i18n_rule("deve ser um cep válido",       "must be a valid postal code")
add_i18n_rule("muss eine PLZ sein",            "must be a valid postal code")
add_i18n_rule("doit être un numéro de siret", "must match pattern '^\\d{14}$'")
```

## Adding typo corrections

```python
from livecheck.compiler import _CORRECTIONS

_CORRECTIONS["longueur minimale"] = "length at least"
_CORRECTIONS["valeur max"]        = "less than or equal to"
```

## Registering a RuleSet

```python
from livecheck import RuleSet

RuleSet.register("eu_vat_number", [
    "must be a non-empty string",
    "must match pattern '^[A-Z]{2}[0-9A-Z]{8,12}$'",
    "must have length at most 14",
])

# Use anywhere
RuleSet.is_valid("FR12345678901", "eu_vat_number")
```

## High-throughput validation with RuleCache

```python
from livecheck import RuleCache

cache = RuleCache()
cache.add("email",    "must be a valid email", "must have length at most 254")
cache.add("age",      "must be an integer",    "must be between 0 and 150")
cache.add("username", "must be a valid username")

# ~1M+ validations/second
for row in csv_rows:
    ok_e, _ = cache.check("email",    row["email"])
    ok_a, _ = cache.check("age",      int(row["age"]))
    ok_u, _ = cache.check("username", row["username"])
```
