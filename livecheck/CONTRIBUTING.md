# Contributing to livecheck

Thank you for your interest! All contributions are welcome — bug reports,
new patterns, documentation, translations, and code improvements.

## Quick start

```bash
git clone https://github.com/Loup0007A/livecheck
cd livecheck
pip install -e ".[dev]"
pytest
```

## Adding a new pattern

Patterns live in `livecheck/compiler.py` (core rules) or
`livecheck/patterns_v4.py` (extended rules).

Each pattern is a decorated function:

```python
@pattern(r"must be (a )?positive number", "must be a positive number")
def _positive(m, **kw):
    return lambda v: (
        isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0,
        f"Expected a positive number, got {v!r}"
    )
```

Rules for a good pattern:
1. The regex is case-insensitive (`re.IGNORECASE` is applied automatically).
2. The second argument is the **canonical** human-readable description shown
   in `list_patterns()` and used for fuzzy suggestions.
3. The inner lambda returns `(bool, str)` — a pass/fail flag and an error
   message shown when the rule fails.
4. Never raise inside the lambda — always return `(False, message)`.
5. Add a test in `tests/test_patterns.py`.

## Adding typo corrections / i18n aliases

Add entries to `_CORRECTIONS` in `livecheck/compiler.py` for typo fixes,
or to `_I18N_ALIASES` in `livecheck/extras.py` for language aliases.

## Running tests

```bash
pytest                        # all tests
pytest tests/test_patterns.py # patterns only
pytest -k "email"             # filter by name
pytest --cov=livecheck        # with coverage
```

## Code style

```bash
ruff check livecheck          # lint
ruff format livecheck         # format
mypy livecheck                # type check
```

## Pull request checklist

- [ ] New/changed behaviour has tests
- [ ] `pytest` passes with no failures
- [ ] `ruff check` passes
- [ ] `CHANGELOG.md` updated under `[Unreleased]`
- [ ] Docstring added for public functions/classes

## Reporting bugs

Open an issue and include:
- Python version (`python --version`)
- livecheck version (`python -c "import livecheck-language; print(livecheck.__version__)"`)
- Minimal reproducer (rule text + value that triggers the bug)

## Feature requests

Open an issue with the label `enhancement`. If you're requesting a new
pattern, include the rule text you'd like to write and example values that
should pass and fail.
