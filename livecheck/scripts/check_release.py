#!/usr/bin/env python3
"""
Pre-release checklist — run before `make publish`.
Verifies that everything is in order for a PyPI release.
"""
import sys, re, pathlib, subprocess

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

OK  = "\033[32m✓\033[0m"
ERR = "\033[31m✗\033[0m"
WARN= "\033[33m⚠\033[0m"

checks_passed = 0
checks_failed = 0

def check(label, condition, warning=False):
    global checks_passed, checks_failed
    if condition:
        print(f"  {OK}  {label}")
        checks_passed += 1
    else:
        icon = WARN if warning else ERR
        print(f"  {icon}  {label}")
        if not warning:
            checks_failed += 1

print("\nlivecheck pre-release checklist\n" + "─" * 40)

# 1. Version consistency
try:
    import livecheck
    init_ver = livecheck.__version__
    toml_text = (ROOT / "pyproject.toml").read_text()
    toml_ver = re.search(r'version\s*=\s*"([^"]+)"', toml_text).group(1)
    check(f"Version consistent: {init_ver}", init_ver == toml_ver)
    check(f"Version not 0.0.0",  init_ver != "0.0.0")
except Exception as e:
    print(f"  {ERR}  Version check failed: {e}")
    checks_failed += 1

# 2. Required files
for fname in ["LICENSE", "README.md", "CHANGELOG.md", "pyproject.toml",
              "CONTRIBUTING.md", "SECURITY.md"]:
    check(f"File exists: {fname}", (ROOT / fname).exists())

# 3. py.typed marker
check("py.typed present", (ROOT / "livecheck" / "py.typed").exists())

# 4. README not empty / has content
readme = (ROOT / "README.md").read_text(encoding="utf-8")
check("README has install section", "pip install livecheck" in readme)
check("README has code examples", "```python" in readme)
check(f"README length adequate ({len(readme):,} chars)", len(readme) > 5000)

# 5. CHANGELOG has current version
try:
    import livecheck as _lc
    ver = _lc.__version__
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    check(f"CHANGELOG has [{ver}] entry", f"[{ver}]" in changelog)
except Exception:
    pass

# 6. No placeholder URLs
for fname in ["README.md", "pyproject.toml"]:
    text = (ROOT / fname).read_text(encoding="utf-8")
    has_placeholder = "yourname" in text or "you@example.com" in text
    check(f"{fname}: no placeholder URLs/emails",
          not has_placeholder, warning=True)

# 7. Pattern count
try:
    from livecheck import list_patterns
    n = len(list_patterns())
    check(f"Pattern count: {n} (≥ 300)", n >= 300)
except Exception as e:
    print(f"  {ERR}  Pattern count failed: {e}")
    checks_failed += 1

# 8. Core imports
try:
    from livecheck import (validate, Schema, Rule, ValidationError, Pipeline,
        RuleSet, generate, watch, batch_validate, checked, debug_rule,
        from_json_schema, to_json_schema, assert_valid, report_html)
    check("All public API imports OK", True)
except ImportError as e:
    check(f"Import failed: {e}", False)

# 9. Smoke test
try:
    from livecheck import validate, ValidationError
    validate("alice@example.com", "must be a valid email")
    validate(42, "must be between 1 and 100")
    try:
        validate("bad", "must be a valid email")
    except ValidationError:
        pass
    check("Smoke test passes", True)
except Exception as e:
    check(f"Smoke test failed: {e}", False)

# 10. Tests directory present
check("tests/ directory exists", (ROOT / "tests").is_dir())
check("tests/test_core.py exists", (ROOT / "tests" / "test_core.py").exists())
check("tests/test_patterns.py exists", (ROOT / "tests" / "test_patterns.py").exists())

print()
print(f"Results: {checks_passed} passed, {checks_failed} failed")
if checks_failed == 0:
    print("\n\033[32m✓ Ready to release!\033[0m")
    print("  Run: make build && make publish")
else:
    print(f"\n\033[31m✗ Fix {checks_failed} issue(s) before releasing.\033[0m")
    sys.exit(1)
