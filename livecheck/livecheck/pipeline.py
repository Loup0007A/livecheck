"""
livecheck.pipeline — Chain validators and transformations.

    result = (
        Pipeline("  Alice@EXAMPLE.COM  ")
        .transform(str.strip)
        .transform(str.lower)
        .validate("must be a valid email")
        .validate("must have length at most 100")
        .result()
    )
"""
from __future__ import annotations
from typing import Any, Callable
from .compiler import compile_rule
from .core import ValidationError


class Pipeline:
    """
    Fluent builder to validate AND transform a value in one chain.

    Steps execute in order; if any validate() step fails, the chain
    records the error but *continues* (collect-all mode).
    Raise all errors at once by calling .result() or .raise_if_invalid().

    Example::

        cleaned_email = (
            Pipeline("  Alice@EXAMPLE.COM  ")
            .transform(str.strip)
            .transform(str.lower)
            .validate("must be a valid email")
            .validate("must have length at most 100")
            .result()
        )
    """

    def __init__(self, value: Any):
        self._value = value
        self._errors: list[str] = []
        self._steps: list[str] = []  # log

    def transform(self, fn: Callable[[Any], Any], label: str = "") -> "Pipeline":
        """Apply a transformation function to the current value."""
        try:
            self._value = fn(self._value)
            self._steps.append(f"transform({label or fn.__name__}) → {self._value!r}")
        except Exception as e:
            self._errors.append(f"Transform error in {label or fn.__name__}: {e}")
        return self

    def validate(self, rule: str) -> "Pipeline":
        """Apply a validation rule (non-raising; errors collected)."""
        from .compiler import compile_rule, _fuzzy_normalize
        try:
            fn = compile_rule(rule)
        except ValueError:
            norm = _fuzzy_normalize(rule)
            try:
                fn = compile_rule(norm)
            except ValueError:
                self._errors.append(f"Unknown rule: {rule!r}")
                return self
        ok, msg = fn(self._value)
        self._steps.append(f"validate({rule!r}) → {'✓' if ok else '✗ ' + msg}")
        if not ok:
            self._errors.append(msg)
        return self

    def default(self, fallback: Any) -> "Pipeline":
        """Replace the value with fallback if current value is falsy."""
        if not self._value:
            self._value = fallback
            self._steps.append(f"default({fallback!r})")
        return self

    def strip(self) -> "Pipeline":
        """Convenience: strip whitespace from string value."""
        return self.transform(lambda v: v.strip() if isinstance(v, str) else v, "strip")

    def lower(self) -> "Pipeline":
        """Convenience: lowercase string."""
        return self.transform(lambda v: v.lower() if isinstance(v, str) else v, "lower")

    def upper(self) -> "Pipeline":
        """Convenience: uppercase string."""
        return self.transform(lambda v: v.upper() if isinstance(v, str) else v, "upper")

    def cast(self, target_type: type) -> "Pipeline":
        """Convenience: cast value to target_type."""
        return self.transform(target_type, f"cast({target_type.__name__})")

    def clamp(self, lo: float, hi: float) -> "Pipeline":
        """Clamp a numeric value to [lo, hi]."""
        def _clamp(v):
            if isinstance(v, (int, float)):
                return max(lo, min(hi, v))
            return v
        return self.transform(_clamp, f"clamp({lo}, {hi})")

    def is_valid(self) -> bool:
        """Return True if no errors accumulated."""
        return len(self._errors) == 0

    def result(self) -> Any:
        """Return the (possibly transformed) value, or raise ValidationError."""
        if self._errors:
            raise ValidationError({"pipeline": self._errors})
        return self._value

    def value(self) -> Any:
        """Return the current value regardless of errors (no raise)."""
        return self._value

    def errors(self) -> list[str]:
        """Return all accumulated errors."""
        return list(self._errors)

    def trace(self) -> str:
        """Return a human-readable trace of all steps."""
        lines = ["Pipeline trace:"]
        for i, step in enumerate(self._steps, 1):
            lines.append(f"  {i}. {step}")
        if self._errors:
            lines.append(f"  ✗ Errors: {self._errors}")
        else:
            lines.append(f"  ✓ Final value: {self._value!r}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        status = "ok" if self.is_valid() else f"{len(self._errors)} error(s)"
        return f"<Pipeline value={self._value!r} [{status}]>"
