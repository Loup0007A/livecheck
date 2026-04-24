"""
livecheck CLI — validate data from the command line.

Usage:
    python -m livecheck validate "alice@example.com" "must be a valid email"
    python -m livecheck validate 42 "must be between 1 and 100" "must be even"
    python -m livecheck explain "must be a valid email"
    python -m livecheck suggest "alice@example.com"
    python -m livecheck patterns [--filter email]
    python -m livecheck generate "must be a valid email" --count 5
    python -m livecheck debug "must be a valid email" "alice@example.com"
    python -m livecheck file users.csv --rules email:"must be a valid email" age:"must be between 18 and 120"
    python -m livecheck profile "must be a valid email" "alice@example.com" --iter 10000
"""

import sys
import json
import argparse


def _parse_value(s: str):
    """Try to coerce CLI string arg to Python type."""
    for converter in (int, float):
        try:
            return converter(s)
        except ValueError:
            pass
    if s.lower() in ('true', 'yes'): return True
    if s.lower() in ('false', 'no'): return False
    if s.lower() in ('null', 'none'): return None
    if s.startswith('[') or s.startswith('{'):
        try: return json.loads(s)
        except Exception: pass
    return s


def _color(text: str, code: str) -> str:
    if sys.stdout.isatty():
        return f"\033[{code}m{text}\033[0m"
    return text

OK  = lambda t: _color(t, "32")
ERR = lambda t: _color(t, "31")
DIM = lambda t: _color(t, "2")
BLD = lambda t: _color(t, "1")


def cmd_validate(args):
    from livecheck import validate, ValidationError
    value = _parse_value(args.value)
    try:
        validate(value, *args.rules)
        print(OK(f"✅  VALID   {value!r}"))
        for r in args.rules:
            print(DIM(f"       ✓  {r}"))
        return 0
    except ValidationError as e:
        print(ERR(f"❌  INVALID {value!r}"))
        for r in args.rules:
            print(DIM(f"       ✓  {r}"))
        for field, msgs in e.errors.items():
            for msg in msgs:
                print(ERR(f"       ✗  {msg}"))
        return 1


def cmd_explain(args):
    from livecheck import explain
    for rule in args.rules:
        print(BLD(rule))
        print(f"  {explain(rule)}")
        print()
    return 0


def cmd_suggest(args):
    from livecheck import suggest
    value = _parse_value(args.value)
    print(f"Suggestions for {value!r}:")
    for s in suggest(value, max_results=args.max or 10):
        print(f"  - {s}")
    return 0


def cmd_patterns(args):
    from livecheck import list_patterns
    patterns = list_patterns()
    if args.filter:
        patterns = [p for p in patterns if args.filter.lower() in p.lower()]
    print(f"{len(patterns)} pattern(s):")
    for p in patterns:
        print(f"  {p}")
    return 0


def cmd_generate(args):
    from livecheck import generate
    rule = args.rule
    n = args.count or 1
    if n == 1:
        val = generate(rule)
        print(repr(val))
    else:
        vals = generate(rule, n=n)
        for v in vals:
            print(repr(v))
    return 0


def cmd_debug(args):
    from livecheck import debug_rule
    rule = args.rule
    value = _parse_value(args.value)
    print(debug_rule(rule, value))
    return 0


def cmd_file(args):
    from livecheck import Schema, Rule, validate_file

    rules_dict = {}
    for entry in (args.rules or []):
        if ':' not in entry:
            print(ERR(f"Rule format must be field:rule_text, got: {entry!r}"), file=sys.stderr)
            return 1
        field, rule_text = entry.split(':', 1)
        rules_dict.setdefault(field.strip(), []).append(Rule(rule_text.strip()))

    schema = Schema(rules_dict)
    report = validate_file(args.path, schema)
    print(report.summary())

    if args.html:
        with open(args.html, 'w', encoding='utf-8') as f:
            from livecheck import report_html
            import csv, json as _json
            rows = []
            try:
                with open(args.path, encoding='utf-8') as fh:
                    reader = csv.DictReader(fh)
                    rows = [dict(r) for r in reader]
            except Exception:
                pass
            html = report_html(rows, schema, title=f"livecheck — {args.path}")
            f.write(html)
        print(f"\nHTML report written to: {args.html}")

    return 0 if report.invalid_rows == 0 else 1


def cmd_profile(args):
    from livecheck import profile
    rule = args.rule
    value = _parse_value(args.value)
    n = args.iter or 10000
    print(f"Profiling: {rule!r} × {n:,}")
    stats = profile(rule, value, iterations=n)
    print(f"  avg:  {stats['avg_us']:.3f} µs")
    print(f"  p50:  {stats['p50_us']:.3f} µs")
    print(f"  p99:  {stats['p99_us']:.3f} µs")
    print(f"  min:  {stats['min_us']:.3f} µs")
    print(f"  max:  {stats['max_us']:.3f} µs")
    calls_per_sec = 1_000_000 / stats['avg_us']
    print(f"  ~{calls_per_sec:,.0f} validations/second")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="livecheck",
        description="Natural language data validation",
    )
    sub = parser.add_subparsers(dest="command")

    # validate
    p_val = sub.add_parser("validate", help="Validate a value against rules")
    p_val.add_argument("value", help="Value to validate")
    p_val.add_argument("rules", nargs="+", help="Rule strings")

    # explain
    p_exp = sub.add_parser("explain", help="Explain what a rule does")
    p_exp.add_argument("rules", nargs="+", help="Rule strings to explain")

    # suggest
    p_sug = sub.add_parser("suggest", help="Suggest rules for a value")
    p_sug.add_argument("value", help="Value to suggest rules for")
    p_sug.add_argument("--max", type=int, default=10, help="Max suggestions")

    # patterns
    p_pat = sub.add_parser("patterns", help="List all supported patterns")
    p_pat.add_argument("--filter", help="Filter by keyword")

    # generate
    p_gen = sub.add_parser("generate", help="Generate valid random values")
    p_gen.add_argument("rule", help="Rule to generate data for")
    p_gen.add_argument("--count", "-n", type=int, default=1)

    # debug
    p_dbg = sub.add_parser("debug", help="Debug how a rule compiles and evaluates")
    p_dbg.add_argument("rule", help="Rule text")
    p_dbg.add_argument("value", help="Value to test")

    # file
    p_file = sub.add_parser("file", help="Validate a CSV or JSON file")
    p_file.add_argument("path", help="Path to file")
    p_file.add_argument("--rules", nargs="+", help="field:rule pairs", metavar="FIELD:RULE")
    p_file.add_argument("--html", help="Write HTML report to this path")

    # profile
    p_prof = sub.add_parser("profile", help="Measure rule performance")
    p_prof.add_argument("rule", help="Rule text")
    p_prof.add_argument("value", help="Value to test")
    p_prof.add_argument("--iter", type=int, default=10000)

    args = parser.parse_args(argv)

    dispatch = {
        "validate": cmd_validate,
        "explain":  cmd_explain,
        "suggest":  cmd_suggest,
        "patterns": cmd_patterns,
        "generate": cmd_generate,
        "debug":    cmd_debug,
        "file":     cmd_file,
        "profile":  cmd_profile,
    }

    if not args.command:
        parser.print_help()
        return 0

    return dispatch[args.command](args) or 0


if __name__ == "__main__":
    sys.exit(main())
