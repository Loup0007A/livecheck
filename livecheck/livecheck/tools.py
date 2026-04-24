"""
livecheck.tools — Power utilities:

- CustomRule      : define rules with a lambda / any callable
- RuleCache       : compile-once cache for hot paths
- validate_file() : validate a CSV or JSON file row-by-row
- report_html()   : generate a rich HTML validation report
- debug_rule()    : step-by-step explanation of how a rule matches
- profile()       : measure rule performance
- merge_schemas() : combine two schemas into one
- optional()      : make any rule optional (skip when None/missing)
- strict_schema() : schema that rejects unknown fields
- mask()          : redact sensitive fields in a dict
"""
from __future__ import annotations

import time
import csv
import json
import io
import html as _html
from typing import Any, Callable
from .core import Rule, Schema, ValidationError, validate
from .compiler import compile_rule, _fuzzy_normalize


# ══════════════════════════════════════════════════════════════════════════════
# CustomRule — any callable as a rule
# ══════════════════════════════════════════════════════════════════════════════

class CustomRule:
    """
    Wrap any callable as a livecheck rule.

    The callable must return either:
    - (bool, str)   — (is_valid, error_message)
    - bool          — True/False (auto-generates error message)

    Example::

        even = CustomRule(lambda v: v % 2 == 0, name="must be even",
                          error="Expected even number, got {value}")

        no_bad_words = CustomRule(
            lambda v: not any(w in v.lower() for w in ["spam","scam"]),
            name="must not contain spam words",
        )

        schema = Schema({"number": even, "bio": no_bad_words})
    """
    def __init__(self, fn: Callable, *, name: str = "",
                 error: str = "Custom rule failed for {value!r}",
                 optional: bool = False):
        self._fn = fn
        self.text = name or fn.__name__ or "custom_rule"
        self._error_template = error
        self.optional = optional

    def check(self, value: Any) -> tuple[bool, str]:
        if self.optional and value is None:
            return True, ""
        try:
            result = self._fn(value)
        except Exception as e:
            return False, f"CustomRule raised {type(e).__name__}: {e}"
        if isinstance(result, tuple) and len(result) == 2:
            ok, msg = result
            return bool(ok), (msg if not ok else "")
        ok = bool(result)
        if not ok:
            try:
                msg = self._error_template.format(value=value)
            except Exception:
                msg = self._error_template
        else:
            msg = ""
        return ok, msg

    # Make it usable everywhere a Rule is expected
    def __repr__(self):
        return f"CustomRule({self.text!r})"


# ══════════════════════════════════════════════════════════════════════════════
# RuleCache — compile-once, evaluate many times
# ══════════════════════════════════════════════════════════════════════════════

class RuleCache:
    """
    Pre-compile a set of rules once and reuse them at maximum speed.
    Useful for hot validation paths (e.g. processing millions of rows).

    Example::

        cache = RuleCache()
        cache.add("email", "must be a valid email")
        cache.add("age", "must be between 18 and 120")

        for row in huge_dataset:
            ok, errs = cache.check("email", row["email"])
            ok, errs = cache.check("age", row["age"])
    """
    def __init__(self):
        self._rules: dict[str, list[tuple[str, Any]]] = {}

    def add(self, name: str, *rule_texts: str) -> "RuleCache":
        """Add one or more rules under a named key."""
        compiled = []
        for rt in rule_texts:
            try:
                fn = compile_rule(rt)
            except ValueError:
                norm = _fuzzy_normalize(rt)
                fn = compile_rule(norm)
            compiled.append((rt, fn))
        self._rules.setdefault(name, []).extend(compiled)
        return self

    def check(self, name: str, value: Any) -> tuple[bool, list[str]]:
        """Run all rules for key `name` against `value`. Returns (all_ok, [errors])."""
        errors = []
        for rule_text, fn in self._rules.get(name, []):
            ok, msg = fn(value)
            if not ok:
                errors.append(msg)
        return len(errors) == 0, errors

    def validate(self, name: str, value: Any) -> Any:
        """Like check() but raises ValidationError on failure."""
        ok, errors = self.check(name, value)
        if not ok:
            raise ValidationError({name: errors})
        return value

    def keys(self) -> list[str]:
        return list(self._rules.keys())

    def __repr__(self):
        return f"<RuleCache keys={self.keys()}>"


# ══════════════════════════════════════════════════════════════════════════════
# validate_file() — CSV / JSON file validation
# ══════════════════════════════════════════════════════════════════════════════

from dataclasses import dataclass, field as dc_field

@dataclass
class FileValidationReport:
    filename: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    errors_by_row: dict[int, dict[str, list[str]]] = dc_field(default_factory=dict)
    parse_errors: list[str] = dc_field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        return (self.valid_rows / self.total_rows * 100) if self.total_rows else 0.0

    def summary(self) -> str:
        lines = [
            f"\n{'='*60}",
            f"  File: {self.filename}",
            f"  Rows: {self.valid_rows}/{self.total_rows} valid ({self.pass_rate:.1f}%)",
        ]
        if self.parse_errors:
            lines.append(f"  Parse errors: {len(self.parse_errors)}")
        for row_i, field_errs in list(self.errors_by_row.items())[:10]:
            lines.append(f"  Row {row_i}:")
            for fld, msgs in field_errs.items():
                for msg in msgs:
                    lines.append(f"    [{fld}] {msg}")
        if len(self.errors_by_row) > 10:
            lines.append(f"  ... and {len(self.errors_by_row)-10} more invalid rows")
        lines.append("="*60)
        return "\n".join(lines)


def validate_file(
    path: str,
    schema: Schema,
    *,
    file_format: str = "auto",
    encoding: str = "utf-8",
    delimiter: str = ",",
    stop_at: int | None = None,
) -> FileValidationReport:
    """
    Validate a CSV or JSON file row-by-row against a schema.

    Parameters
    ----------
    path : str
        Path to the file.
    schema : Schema
        Schema to validate each row.
    file_format : str
        'csv', 'json', 'jsonl', or 'auto' (detect from extension).
    encoding : str
        File encoding (default 'utf-8').
    delimiter : str
        CSV delimiter (default ',').
    stop_at : int | None
        Stop after N invalid rows.

    Returns
    -------
    FileValidationReport

    Example::

        schema = Schema({"email": Rule("must be a valid email"), "age": Rule("must be between 18 and 120")})
        report = validate_file("users.csv", schema)
        print(report.summary())
    """
    import os
    filename = os.path.basename(path)

    if file_format == "auto":
        ext = path.lower().rsplit(".", 1)[-1]
        file_format = {"csv": "csv", "json": "json", "jsonl": "jsonl", "ndjson": "jsonl"}.get(ext, "csv")

    rows: list[dict] = []
    parse_errors: list[str] = []

    try:
        with open(path, encoding=encoding) as f:
            if file_format == "csv":
                reader = csv.DictReader(f, delimiter=delimiter)
                rows = [dict(row) for row in reader]
            elif file_format == "json":
                data = json.load(f)
                rows = data if isinstance(data, list) else [data]
            elif file_format == "jsonl":
                for i, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        parse_errors.append(f"Line {i}: {e}")
    except FileNotFoundError:
        return FileValidationReport(filename, 0, 0, 0, {}, [f"File not found: {path}"])
    except Exception as e:
        return FileValidationReport(filename, 0, 0, 0, {}, [str(e)])

    # Cast CSV strings to numbers where schema expects numbers
    # (CSV always reads strings; try numeric coercion)
    coerced_rows = []
    for row in rows:
        new_row = {}
        for k, v in row.items():
            if isinstance(v, str):
                try:
                    new_row[k] = int(v)
                    continue
                except ValueError:
                    pass
                try:
                    new_row[k] = float(v)
                    continue
                except ValueError:
                    pass
            new_row[k] = v
        coerced_rows.append(new_row)

    from .extras import batch_validate
    batch = batch_validate(coerced_rows, schema, stop_at=stop_at)

    return FileValidationReport(
        filename=filename,
        total_rows=batch.total,
        valid_rows=batch.valid,
        invalid_rows=batch.invalid,
        errors_by_row=batch.errors_by_row,
        parse_errors=parse_errors,
    )


# ══════════════════════════════════════════════════════════════════════════════
# report_html() — generate a beautiful HTML validation report
# ══════════════════════════════════════════════════════════════════════════════

def report_html(
    data: list[dict] | dict,
    schema: Schema,
    *,
    title: str = "livecheck Validation Report",
    output_path: str | None = None,
) -> str:
    """
    Generate a rich, self-contained HTML validation report.

    Parameters
    ----------
    data : list[dict] | dict
        Data to validate (single dict or list of dicts).
    schema : Schema
        The schema to validate against.
    title : str
        Report title shown in the HTML.
    output_path : str | None
        If given, write HTML to this file path.

    Returns
    -------
    str
        The HTML string.

    Example::

        html = report_html(users, schema, title="User Import Report")
        with open("report.html", "w") as f:
            f.write(html)
    """
    from .extras import batch_validate

    if isinstance(data, dict):
        data = [data]

    report = batch_validate(data, schema)

    rows_html = ""
    for i, row in enumerate(data):
        row_errors = report.errors_by_row.get(i, {})
        status = "✅" if not row_errors else "❌"
        status_cls = "ok" if not row_errors else "err"
        cells = ""
        for key, val in row.items():
            errs = row_errors.get(key, [])
            cell_cls = "cell-err" if errs else "cell-ok"
            tip = " | ".join(errs) if errs else ""
            safe_val = _html.escape(str(val))
            cells += f'<td class="{cell_cls}" title="{_html.escape(tip)}">{safe_val}</td>'
        rows_html += f'<tr class="{status_cls}"><td>{i+1}</td><td>{status}</td>{cells}</tr>'

    headers = ""
    if data:
        for k in data[0].keys():
            headers += f"<th>{_html.escape(k)}</th>"

    error_details = ""
    for row_i, field_errs in list(report.errors_by_row.items())[:50]:
        error_details += f'<div class="err-block"><strong>Row {row_i + 1}</strong><ul>'
        for fld, msgs in field_errs.items():
            for msg in msgs:
                error_details += f'<li><code>{_html.escape(fld)}</code>: {_html.escape(msg)}</li>'
        error_details += '</ul></div>'

    pass_pct = f"{report.pass_rate:.1f}"
    bar_color = "#22c55e" if report.pass_rate >= 90 else "#f59e0b" if report.pass_rate >= 60 else "#ef4444"

    html_out = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_html.escape(title)}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         margin: 0; background: #f8fafc; color: #0f172a; }}
  .header {{ background: #1e293b; color: #f1f5f9; padding: 2rem 3rem; }}
  .header h1 {{ margin: 0 0 .5rem; font-size: 1.75rem; }}
  .header p {{ margin: 0; opacity: .7; font-size: .9rem; }}
  .cards {{ display: flex; gap: 1.5rem; padding: 2rem 3rem; flex-wrap: wrap; }}
  .card {{ background: #fff; border-radius: 12px; padding: 1.25rem 1.5rem;
           box-shadow: 0 1px 3px #0001; min-width: 140px; }}
  .card .num {{ font-size: 2rem; font-weight: 700; }}
  .card .lbl {{ font-size: .8rem; color: #64748b; margin-top: .25rem; }}
  .card.green .num {{ color: #16a34a; }}
  .card.red   .num {{ color: #dc2626; }}
  .card.blue  .num {{ color: #2563eb; }}
  .bar-wrap {{ padding: 0 3rem 2rem; }}
  .bar-bg {{ background: #e2e8f0; border-radius: 99px; height: 12px; overflow: hidden; }}
  .bar-fill {{ height: 100%; border-radius: 99px; background: {bar_color};
               width: {pass_pct}%; transition: width .6s; }}
  .bar-label {{ font-size: .85rem; color: #64748b; margin-top: .4rem; }}
  .section {{ padding: 0 3rem 2rem; }}
  .section h2 {{ font-size: 1.1rem; color: #334155; margin-bottom: 1rem; }}
  table {{ width: 100%; border-collapse: collapse; background: #fff;
           border-radius: 10px; overflow: hidden;
           box-shadow: 0 1px 3px #0001; font-size: .85rem; }}
  th {{ background: #f1f5f9; padding: .6rem .75rem; text-align: left;
        color: #475569; font-weight: 600; border-bottom: 1px solid #e2e8f0; }}
  td {{ padding: .55rem .75rem; border-bottom: 1px solid #f1f5f9; }}
  tr.ok td {{ background: #f0fdf4; }}
  tr.err td {{ background: #fff7f7; }}
  td.cell-err {{ background: #fee2e2; color: #991b1b; cursor: help; }}
  .err-block {{ background: #fff; border-left: 4px solid #ef4444;
                border-radius: 0 8px 8px 0; padding: .75rem 1rem;
                margin-bottom: .75rem; box-shadow: 0 1px 2px #0001; }}
  .err-block ul {{ margin: .35rem 0 0 1rem; padding: 0; font-size: .85rem; color: #7f1d1d; }}
  code {{ background: #f1f5f9; padding: 2px 5px; border-radius: 4px; font-size: .8rem; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 99px;
            font-size: .75rem; font-weight: 600; }}
  .badge.ok  {{ background: #dcfce7; color: #166534; }}
  .badge.err {{ background: #fee2e2; color: #991b1b; }}
  footer {{ padding: 2rem 3rem; font-size: .8rem; color: #94a3b8; }}
</style>
</head>
<body>
<div class="header">
  <h1>{_html.escape(title)}</h1>
  <p>Generated by <strong>livecheck</strong> · {report.total} records validated</p>
</div>
<div class="cards">
  <div class="card blue"><div class="num">{report.total}</div><div class="lbl">Total rows</div></div>
  <div class="card green"><div class="num">{report.valid}</div><div class="lbl">Valid</div></div>
  <div class="card red"><div class="num">{report.invalid}</div><div class="lbl">Invalid</div></div>
  <div class="card"><div class="num">{pass_pct}%</div><div class="lbl">Pass rate</div></div>
</div>
<div class="bar-wrap">
  <div class="bar-bg"><div class="bar-fill"></div></div>
  <div class="bar-label">{pass_pct}% of rows passed all validation rules</div>
</div>
{"" if not report.errors_by_row else f'<div class="section"><h2>Error details</h2>{error_details}</div>'}
<div class="section">
  <h2>Data table</h2>
  <table>
    <thead><tr><th>#</th><th>Status</th>{headers}</tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
</div>
<footer>livecheck validation report · {report.total} rows · {report.valid} valid · {report.invalid} invalid</footer>
</body></html>"""

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_out)

    return html_out


# ══════════════════════════════════════════════════════════════════════════════
# debug_rule() — explain how a rule matches step by step
# ══════════════════════════════════════════════════════════════════════════════

def debug_rule(rule_text: str, value: Any) -> str:
    """
    Step-by-step explanation of how a rule is compiled and evaluated.

    Example::

        print(debug_rule("must be a valid email", "alice@example.com"))
        print(debug_rule("muts be valide emial", "notanemail"))
    """
    from .compiler import PATTERNS, _fuzzy_normalize, _CORRECTIONS
    lines = [f"debug_rule({rule_text!r}, {value!r})", "─"*52]

    original = rule_text.strip().rstrip(".")
    normalized = _fuzzy_normalize(original)

    if normalized != original:
        corrections = []
        for w in original.split():
            if w.lower() in _CORRECTIONS:
                corrections.append(f"  '{w}' → '{_CORRECTIONS[w.lower()]}'")
        lines.append("⚠ Fuzzy corrections applied:")
        lines.extend(corrections)
        lines.append(f"  Normalised: '{normalized}'")
    else:
        lines.append("✓ No fuzzy correction needed")

    matched_rx = None
    matched_fn = None
    used_text = original

    for attempt in [original, normalized]:
        for rx, fn in PATTERNS:
            m = rx.search(attempt)
            if m:
                matched_rx = rx
                matched_fn = fn
                used_text = attempt
                break
        if matched_rx:
            break

    if not matched_rx:
        lines.append(f"✗ No pattern matched '{original}'")
        return "\n".join(lines)

    lines.append(f"✓ Pattern matched: r'{matched_rx.pattern}'")
    m = matched_rx.search(used_text)
    groups = [g for g in m.groups() if g]
    if groups:
        lines.append(f"  Captured groups: {groups}")

    validator = matched_fn(m)
    lines.append(f"✓ Validator compiled: {getattr(validator, '__doc__', matched_fn.__name__)}")

    ok, msg = validator(value)
    lines.append(f"\n{'✅ PASS' if ok else '❌ FAIL'}: validate({value!r})")
    if not ok:
        lines.append(f"  Error: {msg}")

    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
# profile() — measure rule performance
# ══════════════════════════════════════════════════════════════════════════════

def profile(rule_text: str, value: Any, iterations: int = 10_000) -> dict:
    """
    Measure how fast a rule validates a value.

    Returns a dict with min/max/avg time in microseconds.

    Example::

        stats = profile("must be a valid email", "alice@example.com", iterations=50_000)
        print(f"avg: {stats['avg_us']:.2f} µs/call")
    """
    fn = compile_rule(_fuzzy_normalize(rule_text))
    times = []

    # Warmup
    for _ in range(min(100, iterations)):
        fn(value)

    for _ in range(iterations):
        t0 = time.perf_counter_ns()
        fn(value)
        times.append(time.perf_counter_ns() - t0)

    times.sort()
    return {
        "rule": rule_text,
        "value": repr(value),
        "iterations": iterations,
        "min_us":  times[0] / 1000,
        "max_us":  times[-1] / 1000,
        "avg_us":  sum(times) / len(times) / 1000,
        "p50_us":  times[len(times)//2] / 1000,
        "p99_us":  times[int(len(times)*0.99)] / 1000,
    }


# ══════════════════════════════════════════════════════════════════════════════
# merge_schemas() — combine two schemas
# ══════════════════════════════════════════════════════════════════════════════

def merge_schemas(*schemas: Schema, on_conflict: str = "extend") -> Schema:
    """
    Merge multiple schemas into one.

    Parameters
    ----------
    *schemas : Schema
        Two or more schemas to merge.
    on_conflict : str
        'extend' — combine rules for shared fields (default)
        'left'   — keep left schema's rules on conflict
        'right'  — keep right schema's rules on conflict

    Example::

        base = Schema({"email": Rule("must be a valid email")})
        extra = Schema({"email": Rule("must have length at most 100"), "age": Rule("must be between 0 and 120")})
        merged = merge_schemas(base, extra)
    """
    merged_fields: dict[str, list] = {}

    for schema in schemas:
        for field_name, rules in schema._fields.items():
            if field_name not in merged_fields:
                merged_fields[field_name] = list(rules)
            else:
                if on_conflict == "extend":
                    merged_fields[field_name].extend(rules)
                elif on_conflict == "right":
                    merged_fields[field_name] = list(rules)
                # on_conflict == "left" → keep existing, do nothing

    new_schema = object.__new__(Schema)
    new_schema._fields = merged_fields
    return new_schema


# ══════════════════════════════════════════════════════════════════════════════
# optional() — make rules skip when value is None/missing
# ══════════════════════════════════════════════════════════════════════════════

def optional(*rule_texts: str) -> list[Rule]:
    """
    Create a list of optional Rules that skip validation when value is None.

    Example::

        schema = Schema({
            "email":   Rule("must be a valid email"),           # required
            "bio":     optional("must be a non-empty string",   # optional
                                "must have length at most 500"),
        })
    """
    return [Rule(rt, optional=True) for rt in rule_texts]


# ══════════════════════════════════════════════════════════════════════════════
# strict_schema() — rejects any unknown field
# ══════════════════════════════════════════════════════════════════════════════

class StrictSchema(Schema):
    """
    A Schema that raises ValidationError for any unknown field in the data.

    Example::

        schema = StrictSchema({
            "name": Rule("must be a non-empty string"),
            "age":  Rule("must be an integer"),
        })
        schema.validate({"name": "Alice", "age": 30, "extra": "oops"})
        # ValidationError: extra: Unknown field
    """
    def validate(self, data: dict[str, Any], *, strict: bool = True) -> dict[str, Any]:
        return super().validate(data, strict=True)


def strict_schema(fields: dict) -> StrictSchema:
    """Convenience constructor for StrictSchema."""
    return StrictSchema(fields)


# ══════════════════════════════════════════════════════════════════════════════
# mask() — redact sensitive fields
# ══════════════════════════════════════════════════════════════════════════════

def mask(data: dict, *sensitive_fields: str, replacement: str = "***") -> dict:
    """
    Return a copy of `data` with sensitive fields redacted.
    Useful for safe logging after validation.

    Example::

        safe = mask(user_data, "password", "ssn", "credit_card")
        print(safe)  # {"email": "alice@example.com", "password": "***", "ssn": "***"}
    """
    out = dict(data)
    for field in sensitive_fields:
        if field in out:
            out[field] = replacement
    return out


# ══════════════════════════════════════════════════════════════════════════════
# assert_valid() — test-friendly assertion
# ══════════════════════════════════════════════════════════════════════════════

def assert_valid(value: Any, *rules: str, msg: str = "") -> None:
    """
    Assert that a value passes all rules. Raises AssertionError (not ValidationError).
    Designed for use in test suites (pytest, unittest).

    Example::

        def test_email():
            assert_valid("alice@example.com", "must be a valid email")

        def test_age():
            assert_valid(25, "must be between 18 and 120", "must be an integer")
    """
    try:
        validate(value, *rules)
    except ValidationError as e:
        errors = [m for msgs in e.errors.values() for m in msgs]
        raise AssertionError(
            msg or f"assert_valid({value!r}) failed:\n" + "\n".join(f"  - {e}" for e in errors)
        )


def assert_invalid(value: Any, *rules: str, msg: str = "") -> None:
    """
    Assert that a value FAILS at least one rule. Raises AssertionError if it passes.
    Useful for negative testing.

    Example::

        def test_bad_email():
            assert_invalid("notanemail", "must be a valid email")
    """
    try:
        validate(value, *rules)
        raise AssertionError(
            msg or f"assert_invalid({value!r}) expected failure but all rules passed"
        )
    except ValidationError:
        pass  # expected — good


# ══════════════════════════════════════════════════════════════════════════════
# summarize_schema() — human-readable schema description
# ══════════════════════════════════════════════════════════════════════════════

def summarize_schema(schema: Schema, *, indent: int = 2) -> str:
    """
    Print a human-readable summary of all fields and rules in a schema.

    Example::

        print(summarize_schema(user_schema))
        # Schema (4 fields):
        #   email (2 rules):
        #     - must be a non-empty string
        #     - must be a valid email
        #   age (1 rule):
        #     - must be between 18 and 120
    """
    pad = " " * indent
    lines = [f"Schema ({len(schema._fields)} fields):"]
    for field_name, rules in schema._fields.items():
        rule_names = []
        for r in rules:
            if isinstance(r, Rule):
                rule_names.append(r.text)
            elif isinstance(r, CustomRule):
                rule_names.append(r.text)
            else:
                rule_names.append(str(r))
        n = len(rule_names)
        lines.append(f"{pad}{field_name} ({n} rule{'s' if n != 1 else ''}):")
        for rn in rule_names:
            lines.append(f"{pad}{pad}- {rn}")
    return "\n".join(lines)
