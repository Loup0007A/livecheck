"""
livecheck — Natural language data validation for Python.

Write rules in plain English (or French/German/Spanish/Portuguese/Italian).
Handles typos. Analyses entire functions. Builds schemas from data.
Generates test data. Watches live objects. Converts JSON Schema.
CLI, HTML reports, CSV/JSON file validation, custom rules, and more.

Quick start::

    from livecheck import validate, Schema, Rule, RuleSet, Pipeline

    validate(42, "must be between 1 and 100")
    validate("alice@example.com", "doit être un email valide")   # French

    schema = Schema({
        "email": RuleSet.schema_rules("email"),
        "age":   Rule("must be between 18 and 120"),
    })
    schema.validate({"email": "x@y.com", "age": 30})
"""

from .core import Rule, Schema, ValidationError, validate
from .compiler import compile_rule, list_patterns
from .checker import checked, CheckReport
from .pipeline import Pipeline
from .extras import (
    explain, suggest,
    batch_validate, BatchReport,
    SchemaBuilder,
    validate_args,
    add_i18n_rule, list_i18n_aliases,
)
from .ruleset import RuleSet
from .advanced import (
    ConditionalRule,
    DependentSchema,
    TransitionRule,
    diff_validate,
    watch, WatchedDict,
    generate,
    from_json_schema, to_json_schema,
    async_validate, async_schema_validate,
)
from .tools import (
    CustomRule,
    RuleCache,
    validate_file,
    report_html,
    debug_rule,
    profile,
    merge_schemas,
    optional,
    StrictSchema, strict_schema,
    mask,
    assert_valid, assert_invalid,
    summarize_schema,
)

__version__ = "0.5.0"
__all__ = [
    # Core
    "Rule", "Schema", "ValidationError", "validate",
    # Compiler
    "compile_rule", "list_patterns",
    # Checker
    "checked", "CheckReport",
    # Pipeline
    "Pipeline",
    # Extras
    "explain", "suggest",
    "batch_validate", "BatchReport",
    "SchemaBuilder",
    "validate_args",
    "add_i18n_rule", "list_i18n_aliases",
    # RuleSet
    "RuleSet",
    # Advanced
    "ConditionalRule",
    "DependentSchema",
    "TransitionRule",
    "diff_validate",
    "watch", "WatchedDict",
    "generate",
    "from_json_schema", "to_json_schema",
    "async_validate", "async_schema_validate",
    # Tools
    "CustomRule",
    "RuleCache",
    "validate_file",
    "report_html",
    "debug_rule",
    "profile",
    "merge_schemas",
    "optional",
    "StrictSchema", "strict_schema",
    "mask",
    "assert_valid", "assert_invalid",
    "summarize_schema",
]
