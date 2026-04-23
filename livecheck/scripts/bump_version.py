#!/usr/bin/env python3
"""
Bump livecheck version across all files.
Usage: python scripts/bump_version.py [0.6.0 | --patch | --minor | --major]
"""
import re, sys, pathlib

ROOT = pathlib.Path(__file__).parent.parent

def get_version():
    m = re.search(r'__version__\s*=\s*"([^"]+)"',
                  (ROOT / "livecheck" / "__init__.py").read_text())
    return m.group(1) if m else "0.0.0"

def bump(v, part):
    a, b, c = map(int, v.split("."))
    return {"major": f"{a+1}.0.0", "minor": f"{a}.{b+1}.0", "patch": f"{a}.{b}.{c+1}"}[part]

def main():
    args = sys.argv[1:]
    current = get_version()
    if not args:
        print(f"Current: {current}"); sys.exit(0)
    new = bump(current, args[0].lstrip("-")) if args[0].startswith("--") else args[0]
    if not re.match(r"^\d+\.\d+\.\d+$", new):
        print(f"Bad format: {new}"); sys.exit(1)
    print(f"{current} → {new}")
    for p in ["livecheck/__init__.py", "pyproject.toml"]:
        f = ROOT / p
        if f.exists():
            f.write_text(f.read_text().replace(current, new))
            print(f"  ✓ {p}")
    ch = ROOT / "CHANGELOG.md"
    if ch.exists():
        ch.write_text(ch.read_text().replace(
            "# Changelog\n",
            f"# Changelog\n\n## [{new}] — unreleased\n\n### Added\n- \n\n"))
        print("  ✓ CHANGELOG.md")
    print(f"\ngit tag v{new} && git push --tags")

if __name__ == "__main__":
    main()
