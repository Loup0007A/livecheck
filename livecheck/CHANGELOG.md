# Changelog

All notable changes to **livecheck** are documented here.  
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).  
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [0.5.0] — 2025-01-01

### Added
- **326 validation patterns** across 10 categories (numbers, strings, types,
  dates, networking, security, medical, e-commerce, collections, developer tooling)
- **`CustomRule`** — wrap any callable as a first-class rule
- **`RuleCache`** — compile-once cache; ~1.1 M validations/second
- **`validate_file()`** — validate CSV or JSONL files row-by-row
- **`report_html()`** — generate self-contained HTML validation reports
- **`debug_rule()`** — step-by-step trace of rule compilation and evaluation
- **`profile()`** — µs-level benchmark with p50/p99 percentiles
- **`merge_schemas()`** — combine multiple schemas (extend / left / right modes)
- **`optional()`** — helper to create lists of nullable Rules
- **`StrictSchema`** / **`strict_schema()`** — reject unknown fields
- **`mask()`** — redact sensitive fields before logging
- **`assert_valid()`** / **`assert_invalid()`** — pytest-friendly assertions
- **`summarize_schema()`** — human-readable schema description
- **CLI** (`python -m livecheck` or `livecheck`): `validate`, `explain`,
  `suggest`, `patterns`, `generate`, `debug`, `file`, `profile` commands
- **PEP 561** `py.typed` marker for full type-checker support
- New patterns: camelCase/PascalCase/snake_case/kebab-case/SCREAMING_SNAKE,
  semantic commit, PyPI/npm name, GitHub URL, ARIA role, WCAG level,
  OTP/TOTP, bcrypt, SQL injection / XSS detection, blood pressure/type,
  ICD-10 code, EAN-13 barcode, ISIN, SWIFT/BIC, DOI, ORCID, arXiv ID,
  16/32/64-bit integers, power-of-two, leap year, contiguous range,
  list-of-type variants, ascending/descending order, and many more

## [0.4.0] — 2024-12-01

### Added
- **`ConditionalRule`** — rule activated only when a condition is met
- **`DependentSchema`** — field rules that vary based on sibling field values
- **`TransitionRule`** / **`diff_validate()`** — validate state transitions
  (immutable fields, append-only lists, allowed state machine moves)
- **`watch()`** / **`WatchedDict`** — auto-validate a dict on every write
- **`generate()`** — produce random valid values for any rule
- **`from_json_schema()`** — convert JSON Schema → livecheck Schema
- **`to_json_schema()`** — export livecheck Schema → JSON Schema
- **`async_validate()`** / **`async_schema_validate()`** — asyncio support
- 80 new patterns: networking (IPv4/IPv6/CIDR/JWT/MD5/SHA256), medical
  (BMI/heart rate/blood pressure/ICD-10/dosage), e-commerce (SKU/UPC/price),
  geolocation, math (Fibonacci/triangular/narcissistic/happy/abundant numbers),
  developer tooling (cron, docker image, k8s name, S3 bucket, env var)

## [0.3.0] — 2024-11-01

### Added
- **`RuleSet`** — 30+ named built-in presets (email, password, uuid, etc.)
- **`Pipeline`** — fluent transform+validate chains with `.strip()`, `.lower()`,
  `.clamp()`, `.cast()`, `.trace()`
- **`explain(rule)`** — natural language explanation of any rule
- **`suggest(value)`** — infer relevant rules from a sample value
- **`batch_validate()`** / **`BatchReport`** — validate entire datasets, export CSV
- **`SchemaBuilder`** — infer a Schema automatically from example dicts
- **`@validate_args`** — inline argument validation decorator
- **i18n** — 80+ rule aliases in French, German, Spanish, Portuguese
- New patterns: date/time (past/future/datetime/timezone/duration),
  security (UUID/JWT/MD5/SHA/IP), formats (slug/hex-color/semver/mac/IBAN)

## [0.2.0] — 2024-10-01

### Added
- **`@checked` decorator** — full A→Z function analysis with typo correction,
  type-hint checking, per-line error report, all rules collected (no short-circuit)
- **Fuzzy normalisation** — 100+ typo corrections, French/Spanish keyword support
- New patterns: prime, perfect square, palindrome, UUID, IP, slug, hex color,
  phone, credit card (Luhn), password strength, date, semver, MAC, IBAN, ISBN,
  postal code, base64, HTML tag, printable characters
- `compile_rule()` and `list_patterns()` public API

## [0.1.0] — 2024-09-01

### Added
- Initial release
- Core `Rule`, `Schema`, `ValidationError`, `validate()` API
- 30 built-in patterns: numbers, strings, types
- Zero runtime dependencies

---

[0.5.0]: https://github.com/yourname/livecheck/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/yourname/livecheck/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/yourname/livecheck/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/yourname/livecheck/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/yourname/livecheck/releases/tag/v0.1.0
