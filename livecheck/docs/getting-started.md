# Getting started

## Installation

```bash
pip install livecheck
```

No dependencies required. Python 3.10+.

## First validation

```python
from livecheck import validate

validate(42, "must be between 1 and 100")          # passes
validate("alice@example.com", "must be a valid email")  # passes
validate(-5, "must be a positive number")           # raises ValidationError
```

## Handling errors

```python
from livecheck import validate, ValidationError

try:
    validate(-5, "must be a positive number")
except ValidationError as e:
    print(e.errors)   # {'value': ['Expected a positive number, got -5']}
```

## Multiple rules at once

```python
validate(50, "must be between 1 and 100", "must be even")

# All rules are checked — all errors collected:
try:
    validate(-3, "must be a positive number", "must be even")
except ValidationError as e:
    print(e.errors["value"])
    # ['Expected a positive number, got -3',
    #  'Expected an even number, got -3']
```

## Your first Schema

```python
from livecheck import Schema, Rule, ValidationError

schema = Schema({
    "email":    Rule("must be a valid email"),
    "age":      Rule("must be between 18 and 120"),
    "username": [Rule("must be a non-empty string"),
                 Rule("must have length at least 3")],
    "role":     Rule("must be one of admin, editor, viewer"),
})

# Validate a dict — raises with ALL field errors at once
schema.validate({
    "email":    "alice@example.com",
    "age":      29,
    "username": "alice",
    "role":     "editor",
})

# Non-raising helpers
schema.is_valid(data)   # → True / False
schema.errors(data)     # → {"field": ["msg", …], …}
```

## Typos are handled automatically

```python
validate(42, "mst be positiv nombr")       # auto-corrected
validate("x@y.com", "muts be valide emial")  # auto-corrected
```

## Multilingual rules

```python
validate(42, "doit être positif")          # French
validate(7,  "muss positiv sein")          # German
validate(7,  "debe ser primo")             # Spanish
validate(42, "deve ser positivo")          # Portuguese
```

## Next steps

- [Pattern reference](patterns.md) — all 326 built-in rules
- [Schema guide](schema.md) — schemas, strict mode, optional fields
- [Features](features.md) — Pipeline, RuleSet, generate, watch, and more
- [CLI reference](cli.md) — command-line interface
