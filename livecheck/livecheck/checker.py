"""
livecheck.checker — Static + runtime analysis of an entire function.
The @checked decorator instruments validate() calls to collect ALL errors,
not just the first one, and prints a full report at the end.
"""

from __future__ import annotations
import ast
import inspect
import functools
import textwrap
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable

from .compiler import compile_rule, _fuzzy_normalize, PATTERNS
from .core import ValidationError


@dataclass
class RuleCheck:
    line: int
    rule_text: str
    value: Any
    passed: bool
    error_msg: str = ""
    corrected_from: str = ""


@dataclass
class CheckReport:
    function_name: str
    duration_ms: float
    args_summary: dict[str, Any]
    rule_checks: list[RuleCheck] = field(default_factory=list)
    type_issues: list[str] = field(default_factory=list)
    runtime_error: str | None = None
    static_warnings: list[str] = field(default_factory=list)

    @property
    def total(self): return len(self.rule_checks)
    @property
    def passed(self): return sum(1 for r in self.rule_checks if r.passed)
    @property
    def failed(self): return self.total - self.passed
    @property
    def corrections(self): return sum(1 for r in self.rule_checks if r.corrected_from)
    @property
    def ok(self): return self.failed == 0 and self.runtime_error is None

    def summary(self) -> str:
        lines = []
        W = "⚠️ "; OK = "✅"; ER = "❌"
        lines += [f"\n{'='*62}",
                  f"  livecheck report — {self.function_name}()",
                  f"{'='*62}",
                  f"  Duration : {self.duration_ms:.2f} ms",
                  f"  Rules    : {self.passed}/{self.total} passed",
                  *([ f"  Typos    : {self.corrections} rule(s) auto-corrected"] if self.corrections else []),
                  *([ f"  Warnings : {len(self.static_warnings)} static warning(s)"] if self.static_warnings else []),
                  ""]

        lines.append("  Arguments:")
        for k, v in self.args_summary.items():
            vr = repr(v)
            if len(vr) > 60: vr = vr[:57] + "..."
            lines.append(f"    {k} = {vr}")
        lines.append("")

        if self.static_warnings:
            lines.append("  Static analysis warnings:")
            for w in self.static_warnings:
                lines.append(f"    {W} {w}")
            lines.append("")

        corrections = [r for r in self.rule_checks if r.corrected_from]
        if corrections:
            lines.append("  Auto-corrected typos:")
            for r in corrections:
                lines.append(f"    {W} Line {r.line}: {r.corrected_from!r}")
                lines.append(f"         → interpreted as : {r.rule_text!r}")
            lines.append("")

        lines.append("  Rule checks:")
        for r in self.rule_checks:
            icon = OK if r.passed else ER
            rule_display = r.rule_text
            if r.corrected_from:
                rule_display = f"{r.corrected_from!r} → {r.rule_text!r}"
            lines.append(f"    {icon}  L{r.line:>3}  {rule_display}")
            if not r.passed:
                lines.append(f"           {r.error_msg}")
        lines.append("")

        if self.type_issues:
            lines.append("  Type hint mismatches:")
            for t in self.type_issues:
                lines.append(f"    {W} {t}")
            lines.append("")

        if self.runtime_error:
            lines.append(f"  {ER} Runtime error:")
            for l in self.runtime_error.strip().splitlines():
                lines.append(f"    {l}")
            lines.append("")

        verdict = f"  {OK}  All {self.total} check(s) passed." if self.ok else f"  {ER}  {self.failed}/{self.total} check(s) FAILED."
        lines += [verdict, f"{'='*62}\n"]
        return "\n".join(lines)

    def __repr__(self):
        return f"<CheckReport {self.function_name}: {self.passed}/{self.total} ok>"


# ─── Static analyser ─────────────────────────────────────────────────────────

def _static_analyse(fn: Callable) -> list[str]:
    warnings: list[str] = []
    try:
        src = textwrap.dedent(inspect.getsource(fn))
        tree = ast.parse(src)
    except Exception:
        return []

    class Visitor(ast.NodeVisitor):
        def visit_Call(self, node):
            fname = ""
            if isinstance(node.func, ast.Name): fname = node.func.id
            elif isinstance(node.func, ast.Attribute): fname = node.func.attr
            if fname == "validate" and len(node.args) >= 2:
                for arg in node.args[1:]:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        rt = arg.value
                        norm = _fuzzy_normalize(rt)
                        matched = any(rx.search(rt) or rx.search(norm) for rx,_ in PATTERNS)
                        if not matched:
                            warnings.append(f"Line {arg.lineno}: {rt!r} may not be recognised")
            self.generic_visit(node)

    Visitor().visit(tree)
    return warnings


# ─── Execution context ────────────────────────────────────────────────────────

class _CheckContext:
    _active: "_CheckContext | None" = None

    def __init__(self, fn_name: str):
        self.fn_name = fn_name
        self.checks: list[RuleCheck] = []

    def record(self, line, rule_text, value, passed, error_msg="", corrected_from=""):
        self.checks.append(RuleCheck(line, rule_text, value, passed, error_msg, corrected_from))

    def __enter__(self):
        _CheckContext._active = self
        return self

    def __exit__(self, *_):
        _CheckContext._active = None


# ─── Type hint checker ────────────────────────────────────────────────────────

def _check_types(fn, bound):
    hints = getattr(fn, '__annotations__', {})
    issues = []
    _map = {int: int, float: float, str: str, bool: bool, list: list, dict: dict, tuple: tuple, set: set}
    for param, value in bound.arguments.items():
        if param in hints:
            exp = hints[param]
            if exp in _map and not isinstance(value, _map[exp]):
                issues.append(f"'{param}': annotated {exp.__name__}, got {type(value).__name__} = {value!r}")
    return issues


# ─── Instrumented validate ────────────────────────────────────────────────────

from . import core as _core
_original_validate = _core.validate


def _instrumented_validate(value: Any, *rules) -> Any:
    ctx = _CheckContext._active
    if ctx is None:
        return _original_validate(value, *rules)

    frame = inspect.currentframe()
    # Walk up the call stack until we're outside livecheck internals
    caller_frame = frame.f_back if frame else None
    caller_line = 0
    while caller_frame:
        fname = caller_frame.f_code.co_filename
        if "livecheck" not in fname or caller_frame.f_code.co_name not in ("_instrumented_validate", "_silent_validate", "wrapper"):
            caller_line = caller_frame.f_lineno
            break
        caller_frame = caller_frame.f_back

    # In @checked mode: record everything, NEVER raise — collect all failures
    all_ok = True
    fail_msgs = []
    for rule_obj in rules:
        rule_text = rule_obj if isinstance(rule_obj, str) else getattr(rule_obj, 'text', str(rule_obj))
        original_text = rule_text
        corrected_from = ""

        try:
            fn = compile_rule(rule_text)
        except ValueError:
            normalized = _fuzzy_normalize(rule_text)
            try:
                fn = compile_rule(normalized)
                corrected_from = original_text
                rule_text = normalized
            except ValueError:
                ctx.record(caller_line, original_text, value, False,
                           f"Rule not recognised: {original_text!r}")
                all_ok = False
                fail_msgs.append(f"Rule not recognised: {original_text!r}")
                continue

        ok, msg = fn(value)
        ctx.record(caller_line, rule_text, value, ok, msg, corrected_from)
        if not ok:
            all_ok = False
            fail_msgs.append(msg)

    # Raise a single ValidationError only after recording all rule results
    if not all_ok:
        raise ValidationError({"value": fail_msgs})
    return value


_core.validate = _instrumented_validate


# ─── @checked decorator ───────────────────────────────────────────────────────

def checked(fn: Callable) -> Callable:
    """
    Decorator that instruments a function with full A→Z validation analysis.

    - Captures EVERY validate() call inside the function
    - Auto-corrects typos in rule strings and flags them
    - Checks type hints vs actual argument values
    - Prints a detailed CheckReport after each call
    - Stores report as fn.last_report

    Usage::

        @checked
        def register(email: str, age: int, tags: list):
            validate(email, "must be a valid email")
            validate(age, "must be between 18 and 120")
            validate(tags, "must be a non-empty list")
    """
    static_warns = _static_analyse(fn)
    sig = inspect.signature(fn)

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        try:
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            args_summary = dict(bound.arguments)
            type_issues = _check_types(fn, bound)
        except TypeError as e:
            args_summary = {"*args": args, "**kwargs": kwargs}
            type_issues = [f"Binding error: {e}"]

        runtime_error = None
        result = None

        # Run the whole function, intercepting validate() calls.
        # We catch ValidationError from validate() but keep running
        # so ALL validate() calls are executed (not just the first).
        with _CheckContext(fn.__name__) as ctx:
            try:
                # Temporarily make validate() non-raising inside fn
                # by wrapping it again to swallow ValidationError
                _inner_raises = []

                def _silent_validate(value, *rules):
                    try:
                        return _instrumented_validate(value, *rules)
                    except ValidationError as e:
                        _inner_raises.append(e)
                        return None

                # Patch the function's global namespace temporarily
                globs = fn.__globals__
                old_validate = globs.get("validate")
                globs["validate"] = _silent_validate
                try:
                    result = fn(*args, **kwargs)
                except Exception as e:
                    runtime_error = traceback.format_exc()
                finally:
                    if old_validate is None:
                        globs.pop("validate", None)
                    else:
                        globs["validate"] = old_validate

            except Exception as e:
                runtime_error = traceback.format_exc()

        duration_ms = (time.perf_counter() - t0) * 1000
        report = CheckReport(
            function_name=fn.__name__,
            duration_ms=duration_ms,
            args_summary=args_summary,
            rule_checks=ctx.checks,
            type_issues=type_issues,
            runtime_error=runtime_error,
            static_warnings=static_warns,
        )
        wrapper.last_report = report
        print(report.summary())
        return result

    wrapper.last_report = None
    return wrapper
