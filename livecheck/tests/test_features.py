"""Tests for livecheck features — Pipeline, RuleSet, SchemaBuilder, etc."""
import pytest
import asyncio
from livecheck import (
    validate, ValidationError, Rule, Schema,
    Pipeline, RuleSet, SchemaBuilder, batch_validate,
    ConditionalRule, DependentSchema, TransitionRule, diff_validate,
    watch, generate, from_json_schema, to_json_schema,
    explain, suggest, validate_args, CustomRule, RuleCache,
    merge_schemas, optional, strict_schema, mask,
    assert_valid, assert_invalid, summarize_schema,
    async_validate, debug_rule, profile, report_html,
)


# ── Pipeline ──────────────────────────────────────────────────────────────────

class TestPipeline:
    def test_chain_transforms_and_validate(self):
        result = (Pipeline("  Alice@EXAMPLE.COM  ")
                  .strip().lower()
                  .validate("must be a valid email")
                  .result())
        assert result == "alice@example.com"

    def test_collect_errors_without_raising(self):
        p = Pipeline("bad").validate("must be a valid email")
        assert not p.is_valid()
        assert len(p.errors()) == 1

    def test_clamp(self):
        p = Pipeline(200).clamp(0, 100)
        assert p.value() == 100

    def test_default(self):
        p = Pipeline(None).default("fallback")
        assert p.value() == "fallback"

    def test_cast(self):
        p = Pipeline("42").cast(int)
        assert p.value() == 42

    def test_trace_contains_steps(self):
        p = Pipeline("hello").strip().validate("must be a non-empty string")
        assert "strip" in p.trace()

    def test_result_raises_on_invalid(self):
        with pytest.raises(ValidationError):
            Pipeline("bad").validate("must be a valid email").result()


# ── RuleSet ───────────────────────────────────────────────────────────────────

class TestRuleSet:
    def test_builtin_email_valid(self):
        assert RuleSet.is_valid("alice@example.com", "email")

    def test_builtin_email_invalid(self):
        assert not RuleSet.is_valid("bad", "email")

    def test_register_custom(self):
        RuleSet.register("test_phone_fr", [
            "must be a non-empty string",
            "must be a valid phone number",
        ], overwrite=True)
        assert RuleSet.is_valid("+33612345678", "test_phone_fr")

    def test_list_returns_sorted(self):
        names = RuleSet.list()
        assert names == sorted(names)

    def test_schema_rules_returns_rule_objects(self):
        rules = RuleSet.schema_rules("uuid")
        assert all(isinstance(r, Rule) for r in rules)

    def test_describe_output(self):
        desc = RuleSet.describe("email")
        assert "email" in desc.lower()
        assert "must be a valid email" in desc

    def test_extend(self):
        new_name = RuleSet.extend("email", ["must have length at least 5"], "email_extended")
        rules = RuleSet.get("email_extended")
        assert "must have length at least 5" in rules

    def test_unknown_raises(self):
        with pytest.raises(KeyError):
            RuleSet.get("this_does_not_exist_xyz")


# ── SchemaBuilder ─────────────────────────────────────────────────────────────

class TestSchemaBuilder:
    def test_infers_email(self):
        b = SchemaBuilder()
        b.learn({"email": "alice@example.com"})
        b.learn({"email": "bob@test.org"})
        schema = b.build()
        assert schema.is_valid({"email": "carol@demo.com"})

    def test_infers_int_range(self):
        b = SchemaBuilder()
        for age in [20, 30, 40]:
            b.learn({"age": age})
        schema = b.build()
        assert schema.is_valid({"age": 25})

    def test_infers_enum(self):
        b = SchemaBuilder()
        for role in ["admin", "editor", "viewer"]:
            b.learn({"role": role})
        schema = b.build()
        assert schema.is_valid({"role": "admin"})

    def test_describe_output(self):
        b = SchemaBuilder().learn({"x": 1})
        desc = b.describe()
        assert "x" in desc

    def test_no_samples_raises(self):
        with pytest.raises(ValueError):
            SchemaBuilder().build()


# ── batch_validate ────────────────────────────────────────────────────────────

class TestBatchValidate:
    def test_all_valid(self):
        s = Schema({"n": Rule("must be an integer")})
        report = batch_validate([{"n": 1}, {"n": 2}], s)
        assert report.valid == 2
        assert report.invalid == 0
        assert report.pass_rate == 100.0

    def test_some_invalid(self):
        s = Schema({"n": Rule("must be an integer")})
        report = batch_validate([{"n": 1}, {"n": "x"}, {"n": 3}], s)
        assert report.valid == 2
        assert report.invalid == 1
        assert 1 in report.invalid_rows()

    def test_csv_export(self):
        s = Schema({"email": Rule("must be a valid email")})
        report = batch_validate([{"email": "bad"}], s)
        csv_out = report.to_csv()
        assert "email" in csv_out

    def test_stop_at(self):
        s = Schema({"n": Rule("must be a positive number")})
        data = [{"n": -i} for i in range(1, 100)]
        report = batch_validate(data, s, stop_at=5)
        assert report.invalid <= 5


# ── ConditionalRule ───────────────────────────────────────────────────────────

class TestConditionalRule:
    def test_applies_when_condition_true(self):
        r = ConditionalRule(
            condition=lambda v: isinstance(v, str) and "@" in v,
            rule="must be a valid email",
        )
        ok, msg = r.check("bad@noext")
        assert ok is False

    def test_skips_when_condition_false(self):
        r = ConditionalRule(
            condition=lambda v: isinstance(v, str) and "@" in v,
            rule="must be a valid email",
        )
        ok, _ = r.check("hello")
        assert ok is True

    def test_else_rule(self):
        r = ConditionalRule(
            condition=lambda v: isinstance(v, int),
            rule="must be a positive number",
            else_rule="must be a non-empty string",
        )
        ok, _ = r.check(-1)   # int → positive check → fails
        assert ok is False
        ok, _ = r.check("")   # not int → else rule → fails
        assert ok is False
        ok, _ = r.check("hi") # not int → else rule → passes
        assert ok is True


# ── DependentSchema ───────────────────────────────────────────────────────────

class TestDependentSchema:
    @pytest.fixture
    def schema(self):
        return DependentSchema(
            fields={"role": Rule("must be one of admin, viewer"),
                    "level": Rule("must be an integer")},
            dependencies={
                "level": {
                    "role": {
                        "admin":   ["must be between 8 and 10"],
                        "_default":["must be between 1 and 3"],
                    }
                }
            }
        )

    def test_admin_high_level_ok(self, schema):
        assert schema.is_valid({"role": "admin", "level": 9})

    def test_admin_low_level_fails(self, schema):
        assert not schema.is_valid({"role": "admin", "level": 2})

    def test_viewer_low_level_ok(self, schema):
        assert schema.is_valid({"role": "viewer", "level": 2})


# ── diff_validate ─────────────────────────────────────────────────────────────

class TestDiffValidate:
    def test_immutable_field_blocks_change(self):
        old = {"id": "abc", "name": "Alice"}
        new = {"id": "xyz", "name": "Alice"}
        with pytest.raises(ValidationError):
            diff_validate(old, new, transition_rules=[TransitionRule.immutable("id")])

    def test_immutable_field_allows_same(self):
        old = {"id": "abc"}
        new = {"id": "abc"}
        diff_validate(old, new, transition_rules=[TransitionRule.immutable("id")])

    def test_monotone_increase(self):
        with pytest.raises(ValidationError):
            diff_validate({"v": 5}, {"v": 3},
                         transition_rules=[TransitionRule.monotone_increase("v")])

    def test_allowed_transitions(self):
        tr = TransitionRule.allowed_transitions("status", {
            "draft": ["published"], "published": []
        })
        diff_validate({"status":"draft"}, {"status":"published"}, transition_rules=[tr])
        with pytest.raises(ValidationError):
            diff_validate({"status":"published"}, {"status":"draft"}, transition_rules=[tr])


# ── watch ─────────────────────────────────────────────────────────────────────

class TestWatch:
    def test_valid_write_accepted(self):
        d = watch({"x": 1}, Schema({"x": Rule("must be a positive number")}))
        d["x"] = 5
        assert d["x"] == 5

    def test_invalid_write_blocked(self):
        violations = []
        d = watch({"x": 1}, Schema({"x": Rule("must be a positive number")}),
                  on_violation=lambda e: violations.append(e))
        d["x"] = -1
        assert len(violations) == 1
        assert d["x"] == 1   # rolled back

    def test_history_recorded(self):
        d = watch({"x": 1}, Schema({"x": Rule("must be an integer")}))
        d["x"] = 2
        d["x"] = 3
        assert len(d.history()) == 2


# ── generate ──────────────────────────────────────────────────────────────────

class TestGenerate:
    @pytest.mark.parametrize("rule", [
        "must be a valid email",
        "must be a valid uuid",
        "must be between 1 and 100",
        "must be a valid phone number",
        "must be a valid password",
        "must be a valid hex color",
        "must be a valid slug",
        "must be a valid url",
    ])
    def test_generated_value_passes_rule(self, rule):
        value = generate(rule)
        validate(value, rule)

    def test_multiple_values(self):
        values = generate("must be a valid email", n=5)
        assert isinstance(values, list)
        assert len(values) == 5
        for v in values:
            validate(v, "must be a valid email")


# ── JSON Schema conversion ────────────────────────────────────────────────────

class TestJsonSchema:
    def test_from_json_schema(self):
        js = {
            "type": "object",
            "required": ["email"],
            "properties": {
                "email": {"type": "string", "format": "email"},
                "age":   {"type": "integer", "minimum": 18, "maximum": 120},
            }
        }
        schema = from_json_schema(js)
        assert schema.is_valid({"email": "a@b.com", "age": 25})

    def test_to_json_schema(self):
        schema = Schema({
            "email": [Rule("must be a valid email"), Rule("must have length at most 100")],
            "age":   Rule("must be between 18 and 120"),
        })
        js = to_json_schema(schema, title="User")
        assert js["title"] == "User"
        assert "email" in js["properties"]
        assert js["properties"]["email"].get("format") == "email"
        assert js["properties"]["age"]["minimum"] == 18.0


# ── Tools ─────────────────────────────────────────────────────────────────────

class TestTools:
    def test_custom_rule_pass(self):
        r = CustomRule(lambda v: v % 2 == 0, name="must be even")
        ok, _ = r.check(4)
        assert ok is True

    def test_custom_rule_fail(self):
        r = CustomRule(lambda v: v % 2 == 0, name="must be even", error="Expected even: {value}")
        ok, msg = r.check(3)
        assert ok is False
        assert "3" in msg

    def test_rule_cache(self):
        cache = RuleCache()
        cache.add("email", "must be a valid email")
        ok, errs = cache.check("email", "alice@example.com")
        assert ok is True
        ok, errs = cache.check("email", "bad")
        assert ok is False

    def test_merge_schemas_extend(self):
        s1 = Schema({"a": Rule("must be an integer")})
        s2 = Schema({"a": Rule("must be a positive number"), "b": Rule("must be a string")})
        m = merge_schemas(s1, s2)
        assert "a" in m._fields
        assert "b" in m._fields
        assert len(m._fields["a"]) == 2

    def test_optional_skips_none(self):
        s = Schema({"bio": optional("must be a non-empty string")})
        assert s.is_valid({"bio": None})
        assert s.is_valid({"bio": "hello"})
        assert not s.is_valid({"bio": ""})

    def test_strict_schema_rejects_unknown(self):
        s = strict_schema({"name": Rule("must be a non-empty string")})
        with pytest.raises(ValidationError):
            s.validate({"name": "Alice", "unexpected": "x"})

    def test_mask_redacts_fields(self):
        data = {"email": "a@b.com", "password": "secret"}
        result = mask(data, "password")
        assert result["password"] == "***"
        assert result["email"] == "a@b.com"

    def test_assert_valid_passes(self):
        assert_valid("a@b.com", "must be a valid email")

    def test_assert_valid_raises(self):
        with pytest.raises(AssertionError):
            assert_valid("bad", "must be a valid email")

    def test_assert_invalid_passes(self):
        assert_invalid("bad", "must be a valid email")

    def test_assert_invalid_raises(self):
        with pytest.raises(AssertionError):
            assert_invalid("a@b.com", "must be a valid email")

    def test_summarize_schema(self):
        s = Schema({"x": Rule("must be an integer")})
        out = summarize_schema(s)
        assert "x" in out
        assert "must be an integer" in out

    def test_report_html_structure(self):
        data = [{"email": "a@b.com"}, {"email": "bad"}]
        schema = Schema({"email": Rule("must be a valid email")})
        html = report_html(data, schema)
        assert "<table" in html
        assert "livecheck" in html.lower()

    def test_debug_rule_pass(self):
        out = debug_rule("must be a valid email", "alice@example.com")
        assert "PASS" in out

    def test_debug_rule_typo(self):
        out = debug_rule("muts be valide emial", "alice@example.com")
        assert "correction" in out.lower() or "→" in out

    def test_profile_returns_stats(self):
        stats = profile("must be a valid email", "a@b.com", iterations=100)
        assert "avg_us" in stats
        assert stats["avg_us"] > 0


# ── Fuzzy / i18n ──────────────────────────────────────────────────────────────

class TestFuzzyAndI18n:
    @pytest.mark.parametrize("rule,value", [
        ("muts be a valide emial", "alice@example.com"),
        ("must be positiv nombr",  42),
        ("must have lenght at least 3", "hello"),
        ("must contian only letters", "hello"),
    ])
    def test_typo_correction_passes(self, rule, value):
        validate(value, rule)

    @pytest.mark.parametrize("rule,value", [
        ("doit être positif",             42),
        ("doit être un email valide",     "alice@example.com"),
        ("muss positiv sein",             5),
        ("debe ser primo",                7),
        ("deve ser um email válido",      "a@b.com"),
    ])
    def test_i18n_aliases(self, rule, value):
        validate(value, rule)


# ── async ─────────────────────────────────────────────────────────────────────

class TestAsync:
    def test_async_validate_pass(self):
        asyncio.run(async_validate("alice@example.com", "must be a valid email"))

    def test_async_validate_fail(self):
        with pytest.raises(ValidationError):
            asyncio.run(async_validate("bad", "must be a valid email"))


# ── explain / suggest ─────────────────────────────────────────────────────────

class TestExplainSuggest:
    def test_explain_known_rule(self):
        desc = explain("must be a valid email")
        assert len(desc) > 10
        assert "email" in desc.lower()

    def test_suggest_email_value(self):
        suggestions = suggest("alice@example.com")
        assert any("email" in s for s in suggestions)

    def test_suggest_integer(self):
        suggestions = suggest(42)
        assert any("integer" in s for s in suggestions)

    def test_suggest_list(self):
        suggestions = suggest([1, 2, 3])
        assert any("list" in s for s in suggestions)
