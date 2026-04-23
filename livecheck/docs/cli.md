# CLI reference

After `pip install livecheck-language`, the `livecheck` command is available:

```
livecheck <command> [options]
```

## validate

Validate a single value against one or more rules.

```bash
livecheck validate "alice@example.com" "must be a valid email"
# ✅  VALID   'alice@example.com'
#        ✓  must be a valid email

livecheck validate "bad" "must be a valid email"
# ❌  INVALID 'bad'
#        ✗  Expected valid email, got 'bad'

livecheck validate 42 "must be between 1 and 100" "must be even"
```

Exit code: `0` = valid, `1` = invalid.

## explain

Explain what a rule does in plain English.

```bash
livecheck explain "must be a valid password"
# must be a valid password
#   The value must have 8+ chars, 1 uppercase, 1 lowercase, 1 digit, 1 special char.
```

## suggest

Suggest rules for a given value.

```bash
livecheck suggest "alice@example.com"
# Suggestions for 'alice@example.com':
#   - must be a non-empty string
#   - must be a valid email
#   - must be lowercase
#   - must contain only ascii characters
```

## patterns

List all built-in patterns.

```bash
livecheck patterns
# 326 pattern(s):
#   must all be negative
#   …

livecheck patterns --filter date
# 5 pattern(s):
#   must be a recent date
#   must be a valid date
#   …
```

## generate

Generate random values that satisfy a rule.

```bash
livecheck generate "must be a valid email"
# 'user_4829@sample.net'

livecheck generate "must be a valid email" --count 5
# 'user_1@example.com'
# 'user_2@test.org'
# …
```

## debug

Step-by-step trace of how a rule compiles and evaluates.

```bash
livecheck debug "muts be valide emial" "alice@example.com"
# debug_rule('muts be valide emial', 'alice@example.com')
# ─────────────────────────────────────────────────────
# ⚠ Fuzzy corrections applied:
#   'muts' → 'must'
#   'valide' → 'valid'
#   'emial' → 'email'
# ✓ Pattern matched: r'must be (a? ?valid )?email...'
# ✅ PASS: validate('alice@example.com')
```

## file

Validate an entire CSV or JSON file.

```bash
livecheck file users.csv \
  --rules "email:must be a valid email" \
          "age:must be between 18 and 120"

# File: users.csv
# Rows: 9842/10000 valid (98.4%)
# Errors in 158 row(s): ...

# Also write HTML report
livecheck file users.csv \
  --rules "email:must be a valid email" \
  --html report.html
```

## profile

Measure rule performance.

```bash
livecheck profile "must be a valid email" "alice@example.com" --iter 50000
# Profiling: 'must be a valid email' × 50,000
#   avg:  0.880 µs
#   p50:  0.493 µs
#   p99:  1.189 µs
#   ~1,136,000 validations/second
```
