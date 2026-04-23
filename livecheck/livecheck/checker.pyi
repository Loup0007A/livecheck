from typing import Any, Callable
from dataclasses import dataclass, field

@dataclass
class RuleCheck:
    line: int
    rule_text: str
    value: Any
    passed: bool
    error_msg: str
    corrected_from: str

@dataclass
class CheckReport:
    function_name: str
    duration_ms: float
    args_summary: dict[str, Any]
    rule_checks: list[RuleCheck]
    type_issues: list[str]
    runtime_error: str | None
    static_warnings: list[str]
    @property
    def total(self) -> int: ...
    @property
    def passed(self) -> int: ...
    @property
    def failed(self) -> int: ...
    @property
    def corrections(self) -> int: ...
    @property
    def ok(self) -> bool: ...
    def summary(self) -> str: ...

def checked(fn: Callable) -> Callable: ...
