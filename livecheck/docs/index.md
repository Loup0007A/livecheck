# livecheck-language

**Natural language data validation for Python.**

```python
from livecheck-language import validate

validate(42, "must be between 1 and 100")
validate("alice@example.com", "must be a valid email")
validate("alice@example.com", "doit être un email valide")  # French
validate("alice@example.com", "muts be valide emial")       # typo — auto-corrected
```

Zero dependencies. Python 3.10+. 326 built-in patterns. Compiles once, runs at 1M+/sec.

[Get started →](getting-started.md){ .md-button .md-button--primary }
[Pattern reference →](patterns.md){ .md-button }

---

## Why livecheck-language?

Unlike Pydantic or Cerberus, livecheck lets you write validation rules in **plain English** (or French, German, Spanish, Portuguese). Rules are compiled to pure Python functions once and evaluated without any overhead.

| Feature | Others | livecheck-language |
|---|---|---|
| Rules as plain English | ✗ | ✓ |
| Typo auto-correction | ✗ | ✓ |
| Multilingual | ✗ | ✓ |
| Zero dependencies | ✗ | ✓ |
| Built-in data generator | ✗ | ✓ |
| Live object watching | ✗ | ✓ |
| HTML reports | ✗ | ✓ |
| CLI | ✗ | ✓ |
