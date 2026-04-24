# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.5.x   | ✅ Yes    |
| < 0.5   | ✗ No     |

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Instead, email **lr000000007@gmail.com**  with:

- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested mitigation

We will acknowledge receipt within 48 hours and aim to release a patch
within 14 days for confirmed vulnerabilities.

## Scope

livecheck validates data **locally** using compiled Python functions.
It makes no network requests at runtime and has no dependencies.

Areas in scope:
- Regex denial-of-service (ReDoS) in pattern matchers
- Arbitrary code execution via crafted rule strings
- Information disclosure via error messages

Out of scope:
- Issues in optional dependencies (`pyyaml`, `pytz`, etc.)
- Vulnerabilities in Python itself
