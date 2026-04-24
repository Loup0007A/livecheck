# Features guide

## Pipeline — chain transforms & validations

```python
from livecheck import Pipeline

result = (
    Pipeline("  Alice@EXAMPLE.COM  ")
    .strip()
    .lower()
    .validate("must be a valid email")
    .validate("must have length at most 254")
    .result()
)
# "alice@example.com"
```

Methods: `.strip()`, `.lower()`, `.upper()`, `.cast(type)`, `.clamp(lo, hi)`,
`.default(fallback)`, `.transform(fn)`, `.validate(rule)`, `.result()`,
`.value()`, `.is_valid()`, `.errors()`, `.trace()`

## RuleSet — reusable named presets

```python
from livecheck import RuleSet, Schema

# 30+ built-in presets
RuleSet.is_valid("alice@example.com", "email")   # True

# Use in Schema
schema = Schema({
    "email":    RuleSet.schema_rules("email"),
    "password": RuleSet.schema_rules("strong_password"),
})

# Register your own
RuleSet.register("fr_phone", [
    "must be a non-empty string",
    "must be a valid phone number",
    "must have length at most 15",
])

# Extend existing
RuleSet.extend("email", ["must not contain 'noreply'"], new_name="reply_email")
```

Built-in presets: `email`, `password`, `strong_password`, `username`, `url`,
`phone`, `age`, `adult_age`, `price`, `uuid`, `ip`, `date`, `slug`,
`hex_color`, `lat`, `lon`, `percentage`, `country`, `currency`, `jwt`,
`semver`, `credit_card`, `api_key`, `bmi`, `blood_pressure`, `http_status`,
`log_level`, `sku`.

## SchemaBuilder — infer schema from data

```python
from livecheck import SchemaBuilder

builder = SchemaBuilder()
builder.learn({"email": "alice@example.com", "age": 25, "role": "admin"})
builder.learn({"email": "bob@test.org",      "age": 31, "role": "editor"})

print(builder.describe())
schema = builder.build()
schema.is_valid({"email": "carol@demo.com", "age": 27, "role": "admin"})
```

## batch_validate — entire datasets

```python
from livecheck import batch_validate, Schema, Rule

schema = Schema({
    "email": Rule("must be a valid email"),
    "age":   Rule("must be between 18 and 120"),
})
report = batch_validate(users, schema)
print(report.summary())    # text summary
print(report.to_csv())     # export errors as CSV
print(report.pass_rate)    # 98.4
```

## validate_file — CSV & JSONL files

```python
from livecheck import validate_file, Schema, Rule

schema = Schema({
    "email": Rule("must be a valid email"),
    "age":   Rule("must be between 0 and 150"),
})
report = validate_file("users.csv", schema)
report = validate_file("events.jsonl", schema, file_format="jsonl")
```

## watch — auto-validate live dicts

```python
from livecheck import watch, Schema, Rule

d = watch(
    {"name": "Alice", "age": 30},
    schema=Schema({
        "name": Rule("must be a non-empty string"),
        "age":  Rule("must be between 0 and 150"),
    }),
    on_violation=lambda e: print("Blocked:", e),
)
d["age"] = 25   # OK — accepted
d["age"] = -5   # → on_violation, rolled back automatically
```

## generate — create test data

```python
from livecheck import generate

generate("must be a valid email")           # "user_4829@sample.net"
generate("must be between 1 and 100")       # 47
generate("must be a valid password")        # "Secure@422"
generate("must be one of red, green, blue") # "green"
generate("must be a valid email", n=5)      # ["user_1@…", …]
```

## diff_validate — state transitions

```python
from livecheck import diff_validate, TransitionRule

transitions = [
    TransitionRule.allowed_transitions("status", {
        "draft":     ["published", "archived"],
        "published": ["archived"],
        "archived":  [],
    }),
    TransitionRule.immutable("id"),
    TransitionRule.monotone_increase("version"),
]
diff_validate(old, new, transition_rules=transitions)
```

## ConditionalRule

```python
from livecheck import ConditionalRule

r = ConditionalRule(
    condition=lambda v: isinstance(v, str) and "@" in v,
    rule="must be a valid email",
    else_rule="must have length at least 3",
)
```

## DependentSchema

```python
from livecheck import DependentSchema, Rule

schema = DependentSchema(
    fields={
        "role":  Rule("must be one of admin, viewer"),
        "level": Rule("must be an integer"),
    },
    dependencies={
        "level": {
            "role": {
                "admin":    ["must be between 8 and 10"],
                "_default": ["must be between 1 and 3"],
            }
        }
    }
)
```

## JSON Schema interop

```python
from livecheck import from_json_schema, to_json_schema

schema = from_json_schema({
    "type": "object",
    "properties": {
        "email": {"type": "string", "format": "email"},
        "age":   {"type": "integer", "minimum": 18, "maximum": 120},
    }
})

js = to_json_schema(my_schema, title="User")
```

## Async support

```python
from livecheck import async_validate

async def handler(email: str):
    await async_validate(email, "must be a valid email")
```

## @checked — full function analysis

```python
from livecheck import checked, validate

@checked
def register(email: str, age: int):
    validate(email, "muts be valide emial")   # typo auto-corrected
    validate(age,   "must be between 18 and 120")

register("alice@example.com", 25)
# Prints detailed report with timing, corrections, per-line status
```

## @validate_args

```python
from livecheck import validate_args

@validate_args(
    email="must be a valid email",
    age=["must be an integer", "must be between 18 and 120"],
)
def create_user(email, age):
    ...
```

## Testing utilities

```python
from livecheck import assert_valid, assert_invalid

def test_email():
    assert_valid("alice@example.com", "must be a valid email")
    assert_invalid("bad", "must be a valid email")
```

## HTML reports

```python
from livecheck import report_html

html = report_html(data, schema, title="Import Report", output_path="report.html")
```

## Performance

```python
from livecheck import RuleCache, profile

# Pre-compiled cache — fastest path
cache = RuleCache()
cache.add("email", "must be a valid email")
for row in million_rows:
    ok, errs = cache.check("email", row["email"])

# Benchmark
stats = profile("must be a valid email", "alice@example.com", iterations=50_000)
print(f"{1_000_000/stats['avg_us']:,.0f} calls/sec")
```

## Strict schemas & utilities

```python
from livecheck import strict_schema, mask, merge_schemas, optional, summarize_schema

# Reject unknown fields
s = strict_schema({"name": Rule("must be a non-empty string")})

# Mask sensitive fields for logging
safe = mask(data, "password", "ssn")   # → {…, "password": "***"}

# Merge schemas
merged = merge_schemas(base_schema, extra_schema)

# Optional fields
schema = Schema({"bio": optional("must be a non-empty string", "must have length at most 500")})

# Human-readable description
print(summarize_schema(schema))
```
