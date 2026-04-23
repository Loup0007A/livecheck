# livecheck

> **Natural language data validation for Python.**
> Write rules in plain English. Handles typos. Zero dependencies.

[![PyPI version](https://img.shields.io/pypi/v/livecheck-language.svg)](https://pypi.org/project/livecheck-language/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Zero dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen.svg)](pyproject.toml)

```python
from livecheck-language import validate, Schema, Rule

validate(42, "must be between 1 and 100")
validate("alice@example.com", "must be a valid email")
validate("alice@example.com", "doit être un email valide")  # French
validate("alice@example.com", "muts be valide emial")       # typo — auto-corrected

schema = Schema({
    "email":    Rule("must be a valid email"),
    "age":      Rule("must be between 18 and 120"),
    "username": [Rule("must be a non-empty string"), Rule("must have length at least 3")],
    "role":     Rule("must be one of admin, editor, viewer"),
})
schema.validate({"email": "alice@example.com", "age": 29, "username": "alice", "role": "editor"})
```

---

## Install

```bash
pip install livecheck-language
```

No dependencies. Python 3.10+.

---

## Why livecheck?

| Feature | Pydantic | Cerberus | Marshmallow | **livecheck-language** |
|---|---|---|---|---|
| Write rules as… | Python types | Dict schemas | Class definitions | **Plain English** |
| Zero dependencies | ✗ | ✗ | ✗ | **✓** |
| Typo correction | ✗ | ✗ | ✗ | **✓** |
| Multilingual rules | ✗ | ✗ | ✗ | **✓** |
| Built-in data generator | ✗ | ✗ | ✗ | **✓** |
| Live object watching | ✗ | ✗ | ✗ | **✓** |
| HTML reports | ✗ | ✗ | ✗ | **✓** |
| CLI included | ✗ | ✗ | ✗ | **✓** |
| Compile once, run at 1M+/s | — | — | — | **✓** |

Rules compile to pure Python functions **once** — no AI, no network, no overhead at runtime.

---

## Table of contents

- [Core API](#core-api)
- [326 built-in patterns](#326-built-in-patterns)
- [Fuzzy matching & typos](#fuzzy-matching--typos)
- [Multilingual rules (i18n)](#multilingual-rules-i18n)
- [Schema](#schema)
- [Pipeline](#pipeline)
- [RuleSet — named presets](#ruleset--named-presets)
- [CustomRule](#customrule)
- [SchemaBuilder — infer from data](#schemabuilder--infer-from-data)
- [batch_validate — datasets](#batch_validate--datasets)
- [validate_file — CSV & JSON](#validate_file--csv--json)
- [watch — live objects](#watch--live-objects)
- [generate — test data](#generate--test-data)
- [diff_validate — state transitions](#diff_validate--state-transitions)
- [ConditionalRule & DependentSchema](#conditionalrule--dependentschema)
- [JSON Schema interop](#json-schema-interop)
- [Async support](#async-support)
- [@checked — full function analysis](#checked--full-function-analysis)
- [@validate_args](#validate_args)
- [Testing utilities](#testing-utilities)
- [HTML reports](#html-reports)
- [Debug & profiling](#debug--profiling)
- [CLI](#cli)
- [Extending livecheck](#extending-livecheck)

---

## Core API

```python
from livecheck-language import validate, Rule, Schema, ValidationError

# Single value — raises ValidationError on failure
validate(42, "must be between 1 and 100")
validate("alice@example.com", "must be a valid email")

# Multiple rules for one value
validate(50, "must be between 1 and 100", "must be even")

# Rule object
r = Rule("must be a valid email")
ok, msg = r.check("alice@example.com")   # (True, '')
ok, msg = r.check("bad")                 # (False, "Expected valid email…")

# Optional rule — skipped when value is None
Rule("must be a valid email", optional=True).check(None)  # (True, '')
```

---

## 326 built-in patterns

### Numbers
```
must be a positive number         must be a negative number
must be between X and Y           must be greater than N
must be less than N               must be greater than or equal to N
must be less than or equal to N   must equal N
must be an integer                must be a float
must be even                      must be odd
must be a multiple of N           must be divisible by N
must be a prime number            must be a perfect square
must be a perfect number          must be a fibonacci number
must be a triangular number       must be a narcissistic number
must be a happy number            must be an abundant number
must be non-zero                  must be finite
must be a number                  must be a percentage
must be a probability             must be a power of N
must be a power of two            must be a byte value (0-255)
must be a 16-bit integer          must be a 32-bit integer
must be a 64-bit integer          must be a natural number
must be a safe integer            must be a whole number
must be non-negative              must be a valid unix timestamp
must be in scientific notation    must be a valid angle
must be a valid latitude          must be a valid longitude
must be a valid probability       must be a valid bmi
must be a valid heart rate        must be a valid body temperature
must be a valid ph level          must be a valid altitude
must be a valid port number       must have at most N decimal places
```

### Strings — identity & format
```
must be a non-empty string        must be a valid email
must be a valid url               must be a valid uuid
must be a valid slug              must be a valid hex color
must be a valid color value       must be a valid color in rgb
must be a palindrome              must be trimmed
must be lowercase / uppercase     must be title case
must be camelCase string          must be PascalCase string
must be snake_case string         must be kebab-case string
must be SCREAMING_SNAKE_CASE      must be an acronym
must be a sentence                must be capitalized
must be a single character        must be a single word
must be wrapped in quotes         must be a valid emoji
must be a valid markdown
```

### Strings — network & identity
```
must be a valid ip address        must be a valid ipv4 address
must be a valid ipv6 address      must be a valid hostname
must be a valid domain name       must be a valid mac address
must be a valid cidr              must be a valid jwt token
must be a valid md5 hash          must be a valid sha1 hash
must be a valid sha256 hash       must be a valid bcrypt hash
must be a valid bearer token      must be a valid basic auth
must be a valid api key format    must be a valid strong api key
must be a valid oauth scope
```

### Strings — dates & time
```
must be a valid date              must be a valid time
must be a valid datetime          must be an iso 8601 date string
must be a valid semver            must be a valid timezone
must be a valid duration          must be a valid cron expression
must be a valid weekday           must be a weekend
must be a weekday date            must be in the past
must be in the future             must be a recent date
must be a valid year              must be a valid month
must be a valid day               must be a valid quarter
must be a valid fiscal year       must be a leap year
```

### Strings — structured content
```
must be valid json                must be valid base64
must be valid yaml                must be valid toml
must be a valid python identifier must be a valid env var name
must be a valid sql table name    must be a valid pypi package name
must be a valid npm package name  must be a valid git commit hash
must be a valid git branch name   must be a valid semantic commit message
must be a valid github repo url   must be a valid docker image name
must be a valid kubernetes name   must be a valid s3 bucket name
must be a valid terraform name    must be a valid namespace
must be a valid package name      must be a valid semver range
must be a valid mime type         must be a valid locale
must be a valid html tag          must be a valid html attribute
must be a valid xml tag           must be a valid aria role
must be a valid wcag level        must be a valid css class name
```

### Strings — business & identity
```
must be a valid phone number      must be a valid credit card number
must be a valid password          must be a valid strong password
must be a valid iban              must be a valid swift code
must be a valid isbn              must be a valid ean-13 barcode
must be a valid isin              must be a valid doi
must be a valid orcid             must be a valid arxiv id
must be a valid ssn               must be a valid vin number
must be a valid otp code          must be a valid totp code
must be a valid currency code     must be a valid country code
must be a valid language code     must be a valid us state code
must be a valid zip code          must be a valid uk postcode
must be a valid french postcode   must be a valid postal code
must be a valid username          must be a valid hashtag
must be a valid twitter handle    must be a valid geohash
must be a valid what3words address
```

### Strings — medical & health
```
must be a valid blood type        must be a valid blood pressure
must be a valid icd-10 code       must be a valid drug dosage
must be a valid npi number
```

### Strings — security
```
must not contain sql injection    must not contain xss
must not contain path traversal   must be a valid pii free string
must not have a null byte
```

### Strings — e-commerce
```
must be a valid sku               must be a valid upc code
must be a valid tracking number   must be a valid coupon code
must be a valid price             must be a valid quantity
```

### Collections
```
must be a list                    must be a sorted list
must be a non-empty list          must be a list of integers
must be a list of strings         must be a list of floats
must be a list of booleans        must be a list of dicts
must have unique items            must not have duplicates
must have at least N items        must have at most N items
must have exactly N items         must be a flat list
must be in ascending order        must be in descending order
must be strictly increasing       must be strictly decreasing
must be monotone increasing       must be a contiguous range
must be a matrix                  must be a square matrix
must be a subset of [a, b, c]     must be a superset of [a, b, c]
must all be positive              must all be negative
must have no null values          must have no empty items
must have all items truthy        must have all items falsy
must have sum of N                must have average of N
must contain the value N          must contain the item 'x'
must have min of N                must have max of N
```

### Dicts
```
must be a dict                    must be a non-empty dict
must contain the key 'name'       must have N keys
must have all keys in 'a, b, c'   must have no empty values
must have all values be strings   must have all values be integers
must be a flat dict               must be json-serializable
```

### Types
```
must be a boolean                 must be none
must not be none                  must be truthy / falsy
must be a tuple                   must be a set
must be required                  must be callable
```

---

## Fuzzy matching & typos

livecheck-language auto-corrects common typos and misspellings before compiling:

```python
validate(42,  "mst be positiv nombr")      # → "must be a positive number"
validate("x@y.com", "muts be valide emial") # → "must be a valid email"
validate(5,   "doit etre entre 1 and 10")  # → French "must be between 1 and 10"
```

Over 150 corrections are built in. You can add your own:

```python
from livecheck-language.compiler import _CORRECTIONS
_CORRECTIONS["valeur"] = "value"
```

---

## Multilingual rules (i18n)

Rules work in **French, German, Spanish, and Portuguese** out of the box:

```python
# French
validate(42, "doit être positif")
validate("alice@example.com", "doit être un email valide")
validate(7,  "doit être un nombre premier")

# German
validate(42, "muss positiv sein")
validate("x@y.com", "muss eine gültige e-mail sein")

# Spanish
validate(7, "debe ser primo")
validate("x@y.com", "debe ser un email válido")

# Portuguese
validate(42, "deve ser positivo")
validate("x@y.com", "deve ser um email válido")
```

Add your own aliases:

```python
from livecheck-language import add_i18n_rule
add_i18n_rule("deve ser um cpf válido", "must match pattern '[0-9]{11}'")
```

---

## Schema

```python
from livecheck-language import Schema, Rule

schema = Schema({
    "email":    Rule("must be a valid email"),
    "age":      [Rule("must be an integer"), Rule("must be between 18 and 120")],
    "bio":      Rule("must be a non-empty string", optional=True),  # skipped if None
})

schema.validate(data)          # raises ValidationError with ALL field errors
schema.is_valid(data)          # → True / False
schema.errors(data)            # → {"field": ["error msg", …], …}
schema.validate(data, strict=True)  # also rejects unknown fields
```

---

## Pipeline

Chain transformations and validations fluently:

```python
from livecheck-language import Pipeline

result = (
    Pipeline("  Alice@EXAMPLE.COM  ")
    .strip()                              # → "Alice@EXAMPLE.COM"
    .lower()                              # → "alice@example.com"
    .validate("must be a valid email")
    .validate("must have length at most 254")
    .result()                             # raises if any rule failed
)
# "alice@example.com"

p = Pipeline(200).clamp(0, 100)          # → 100
p = Pipeline("42").cast(int)             # → 42
p = Pipeline(None).default("fallback")  # → "fallback"
print(p.trace())                         # step-by-step log
```

---

## RuleSet — named presets

30+ built-in presets; register your own:

```python
from livecheck-language import RuleSet, Schema

# Use a preset
RuleSet.is_valid("alice@example.com", "email")   # True
RuleSet.validate("weak", "password")             # raises ValidationError

# Use presets in Schema
schema = Schema({
    "email":    RuleSet.schema_rules("email"),
    "password": RuleSet.schema_rules("strong_password"),
    "age":      RuleSet.schema_rules("adult_age"),
    "country":  RuleSet.schema_rules("country"),
})

# Register custom preset
RuleSet.register("eu_vat", [
    "must be a non-empty string",
    "must match pattern '^[A-Z]{2}[0-9A-Z]{8,12}$'",
])

# Extend existing preset
RuleSet.extend("email", ["must not contain 'noreply'"], new_name="reply_email")
```

Built-in presets: `email`, `password`, `strong_password`, `username`, `url`,
`phone`, `age`, `adult_age`, `price`, `uuid`, `ip`, `date`, `slug`, `hex_color`,
`lat`, `lon`, `percentage`, `country`, `currency`, `jwt`, `semver`, `credit_card`,
`api_key`, `bmi`, `blood_pressure`, `http_status`, `log_level`, `sku`.

---

## CustomRule

Wrap any callable as a first-class rule:

```python
from livecheck-language import CustomRule, Schema

profanity_free = CustomRule(
    lambda v: not any(w in v.lower() for w in ["spam", "scam"]),
    name="must not contain spam words",
    error="String contains forbidden words: {value!r}",
)

in_stock = CustomRule(
    lambda v: v.get("stock", 0) > 0,
    name="must be in stock",
)

schema = Schema({
    "bio":     profanity_free,
    "product": in_stock,
})
```

---

## SchemaBuilder — infer from data

Automatically infer a schema from sample records:

```python
from livecheck-language import SchemaBuilder

builder = SchemaBuilder()
builder.learn({"email": "alice@example.com", "age": 25, "role": "admin"})
builder.learn({"email": "bob@test.org",      "age": 31, "role": "editor"})
builder.learn({"email": "carol@demo.net",    "age": 22, "role": "viewer"})

print(builder.describe())
# Inferred schema from 3 sample(s):
#   age:   must be between 22 and 31, must be an integer
#   email: must be a valid email, must be lowercase
#   role:  must be one of admin, editor, viewer

schema = builder.build()
schema.is_valid({"email": "new@user.com", "age": 28, "role": "admin"})  # True
```

---

## batch_validate — datasets

```python
from livecheck-language import batch_validate, Schema, Rule

schema = Schema({
    "email": Rule("must be a valid email"),
    "age":   Rule("must be between 18 and 120"),
})

report = batch_validate(users, schema)
print(report.summary())
# Batch validation: 9842/10000 valid (98.4%)
# Errors in 158 row(s):
#   Row 3: [email] Expected valid email…

print(report.to_csv())        # export errors as CSV
print(report.invalid_rows())  # [3, 7, 12, …]
```

---

## validate_file — CSV & JSON

```python
from livecheck-language import validate_file, Schema, Rule

schema = Schema({
    "email": Rule("must be a valid email"),
    "age":   Rule("must be between 0 and 150"),
})

report = validate_file("users.csv", schema)
print(report.summary())
# File: users.csv
# Rows: 9842/10000 valid (98.4%)

# Also supports JSON and JSONL
report = validate_file("events.jsonl", schema, file_format="jsonl")
```

---

## watch — live objects

Auto-validate a dict on every write. Rolls back invalid changes:

```python
from livecheck-language import watch, Schema, Rule

d = watch(
    {"name": "Alice", "age": 30},
    schema=Schema({
        "name": Rule("must be a non-empty string"),
        "age":  Rule("must be between 0 and 150"),
    }),
    on_violation=lambda errors: print("Invalid write blocked:", errors),
)

d["age"] = 25    # OK
d["age"] = -5    # → on_violation called, rolled back to 25
d["name"] = "Bob"
print(d.history())  # [(timestamp, field, old_val, new_val), …]
```

---

## generate — test data

Generate random values that satisfy any rule:

```python
from livecheck-language import generate

generate("must be a valid email")         # "user_4829@sample.net"
generate("must be between 1 and 100")     # 47
generate("must be a valid uuid")          # "f892d015-60f2-4d79-…"
generate("must be a valid hex color")     # "#3F8A2C"
generate("must be a valid password")      # "Secure@422"
generate("must be one of red, green, blue") # "green"

generate("must be a valid email", n=5)   # ["user_1@…", "user_2@…", …]
```

---

## diff_validate — state transitions

Enforce valid transitions between old and new states:

```python
from livecheck-language import diff_validate, TransitionRule, Schema, Rule

order_schema = Schema({
    "status": Rule("must be one of pending, paid, shipped, delivered, cancelled"),
})
transitions = [
    TransitionRule.allowed_transitions("status", {
        "pending":   ["paid", "cancelled"],
        "paid":      ["shipped", "cancelled"],
        "shipped":   ["delivered"],
        "delivered": [],
    }),
    TransitionRule.immutable("id"),
    TransitionRule.monotone_increase("version"),
    TransitionRule.append_only("items"),
    TransitionRule.no_delete("customer_email"),
]

diff_validate(old_order, new_order, schema=order_schema, transition_rules=transitions)
```

---

## ConditionalRule & DependentSchema

```python
from livecheck-language import ConditionalRule, DependentSchema, Rule

# Rule that only applies when condition is met
r = ConditionalRule(
    condition=lambda v: isinstance(v, str) and "@" in v,
    rule="must be a valid email",
    else_rule="must have length at least 3",
)

# Schema where rules vary based on another field's value
schema = DependentSchema(
    fields={
        "role":  Rule("must be one of admin, editor, viewer"),
        "level": Rule("must be an integer"),
    },
    dependencies={
        "level": {
            "role": {
                "admin":    ["must be between 8 and 10"],
                "editor":   ["must be between 4 and 7"],
                "_default": ["must be between 1 and 3"],
            }
        }
    }
)
```

---

## JSON Schema interop

```python
from livecheck-language import from_json_schema, to_json_schema, Schema, Rule
import json

# Import from JSON Schema
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

# Export to JSON Schema
schema2 = Schema({
    "email": [Rule("must be a valid email"), Rule("must have length at most 254")],
    "age":   Rule("must be between 18 and 120"),
})
print(json.dumps(to_json_schema(schema2, title="User"), indent=2))
```

---

## Async support

```python
from livecheck-language import async_validate, async_schema_validate

async def create_user(email: str, age: int):
    await async_validate(email, "must be a valid email")
    await async_validate(age, "must be between 18 and 120")

# With FastAPI
from fastapi import HTTPException
async def register(body: dict):
    try:
        await async_schema_validate(body, user_schema)
    except ValidationError as e:
        raise HTTPException(422, detail=e.errors)
```

---

## @checked — full function analysis

Instrument an entire function: captures every `validate()` call, auto-corrects
typos in rules, checks type hints, and prints a detailed report after each call.

```python
from livecheck-language import checked, validate

@checked
def register_user(email: str, age: int, username: str):
    validate(email, "muts be valide emial")      # typo — auto-corrected
    validate(age,   "must be between 18 and 120")
    validate(username, "must have length at least 3")

register_user("alice@example.com", 25, "alice")
# ════════════════════════════════════════════════════════════
#   livecheck-language report — register_user()
# ════════════════════════════════════════════════════════════
#   Duration : 0.41 ms   Rules : 3/3 passed   Typos : 1 auto-corrected
#
#   Auto-corrected typos:
#     ⚠ Line 7: 'muts be valide emial' → 'must be a valid email'
#
#   Rule checks:
#     ✅  L  7  muts be valide emial
#     ✅  L  8  must be between 18 and 120
#     ✅  L  9  must have length at least 3
#
#   ✅  All 3 check(s) passed.
```

---

## @validate_args

Validate function arguments before the body runs:

```python
from livecheck-language import validate_args

@validate_args(
    email="must be a valid email",
    age=["must be an integer", "must be between 18 and 120"],
    tags=["must be a list", "must have at least 1 items"],
)
def create_account(email, age, tags):
    ...  # only reached if all args are valid
```

---

## Testing utilities

```python
from livecheck-language import assert_valid, assert_invalid

# In pytest tests
def test_email_validation():
    assert_valid("alice@example.com", "must be a valid email")
    assert_invalid("not-an-email",    "must be a valid email")

def test_age_range():
    assert_valid(25, "must be between 18 and 120")
    assert_invalid(200, "must be between 18 and 120")
```

---

## HTML reports

```python
from livecheck-language import report_html, Schema, Rule

schema = Schema({
    "email": Rule("must be a valid email"),
    "age":   Rule("must be between 18 and 120"),
})

html = report_html(
    users,                            # list of dicts
    schema,
    title="User Import Report",
    output_path="report.html",        # also writes to file
)
```

The generated report is a self-contained HTML file with a summary card,
pass-rate bar, per-row status table, and detailed error list.

---

## Debug & profiling

```python
from livecheck-language import debug_rule, profile

# Step-by-step trace
print(debug_rule("muts be valide emial", "alice@example.com"))
# ⚠ Fuzzy corrections: 'muts'→'must', 'valide'→'valid', 'emial'→'email'
# ✓ Pattern matched: r'must be (a? ?valid )?email( address)?'
# ✅ PASS: validate('alice@example.com')

# Benchmark
stats = profile("must be a valid email", "alice@example.com", iterations=50_000)
print(f"avg {stats['avg_us']:.2f} µs — ~{1_000_000/stats['avg_us']:,.0f} calls/sec")
# avg 0.88 µs — ~1,136,000 calls/sec
```

---

## CLI

```bash
# Validate a value
livecheck validate "alice@example.com" "must be a valid email"
livecheck validate 42 "must be between 1 and 100" "must be even"

# Explain a rule
livecheck explain "must be a valid password"

# Suggest rules for a value
livecheck suggest "alice@example.com"

# List all patterns (optional filter)
livecheck patterns --filter date

# Generate valid test data
livecheck generate "must be a valid email" --count 5

# Debug how a rule compiles
livecheck debug "muts be valide emial" "alice@example.com"

# Validate a CSV file
livecheck file users.csv \
  --rules "email:must be a valid email" "age:must be between 18 and 120" \
  --html report.html

# Benchmark a rule
livecheck profile "must be a valid email" "alice@example.com" --iter 50000
```

---

## Extending livecheck

### Custom patterns

```python
from livecheck-language.compiler import pattern

@pattern(r"must be a french phone number", "must be a french phone number")
def _fr_phone(m, **kw):
    import re
    rx = re.compile(r"^(\+33|0)[1-9]\d{8}$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected French phone number, got {v!r}")
```

### Using RuleCache for high-throughput

```python
from livecheck-language import RuleCache

cache = RuleCache()
cache.add("email", "must be a valid email", "must have length at most 254")
cache.add("age",   "must be an integer", "must be between 0 and 150")

# Hot path: ~1M+ validations/second
for row in huge_csv:
    ok, errors = cache.check("email", row["email"])
    ok, errors = cache.check("age", int(row["age"]))
```

### StrictSchema — reject unknown fields

```python
from livecheck-language import strict_schema, Rule

schema = strict_schema({
    "name": Rule("must be a non-empty string"),
    "age":  Rule("must be between 0 and 120"),
})
schema.validate({"name": "Alice", "age": 30, "extra": "oops"})
# ValidationError: extra: Unknown field
```

### Masking sensitive data for logging

```python
from livecheck-language import mask

safe = mask(user_data, "password", "ssn", "credit_card")
logger.info("User data: %s", safe)  # passwords appear as "***"
```

---

## License

[MIT](LICENSE) — free for commercial and personal use.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). All contributions welcome.

## Changelog

See [CHANGELOG.md](CHANGELOG.md).
