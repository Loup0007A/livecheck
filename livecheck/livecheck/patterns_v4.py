"""
livecheck patterns v4 — 60+ additional patterns.
Auto-imported by compiler.py via: from .patterns_v4 import *
"""
import re, math
from datetime import datetime
from .compiler import pattern


# ══════════════════════════════════════════════════════════════════════════════
# CROSS-FIELD / CONDITIONAL STRING
# ══════════════════════════════════════════════════════════════════════════════

@pattern(r"must (only )?contain (only )?spaces?$", "must contain only spaces")
def _only_spaces(m, **kw):
    return lambda v: (isinstance(v, str) and len(v) > 0 and all(c == ' ' for c in v),
                      f"Expected only spaces, got {v!r}")

@pattern(r"must (be a )?single (character|char)$", "must be a single character")
def _single_char(m, **kw):
    return lambda v: (isinstance(v, str) and len(v) == 1,
                      f"Expected single character, got {v!r}")

@pattern(r"must (be a )?single (word|token)$", "must be a single word")
def _single_word(m, **kw):
    return lambda v: (isinstance(v, str) and len(v.split()) == 1,
                      f"Expected single word (no spaces), got {v!r}")

@pattern(r"must be (a )?sentence$", "must be a sentence")
def _sentence(m, **kw):
    return lambda v: (isinstance(v, str) and len(v.split()) >= 3
                      and v[0].isupper() and v.rstrip()[-1] in '.!?',
                      f"Expected a sentence (capitalised, ends with punctuation), got {v!r}")

@pattern(r"must (not )?be (a |an )?acronym$", "must be an acronym")
def _acronym(m, **kw):
    return lambda v: (isinstance(v, str) and v.isupper() and v.isalpha() and len(v) <= 10,
                      f"Expected acronym (all uppercase letters), got {v!r}")

@pattern(r"must (be )?wrapped in (quotes?|double quotes?|single quotes?)", "must be wrapped in quotes")
def _wrapped_quotes(m, **kw):
    kind = m.group(2).lower()
    if 'double' in kind:
        return lambda v: (isinstance(v, str) and v.startswith('"') and v.endswith('"'),
                          f"Expected double-quoted string, got {v!r}")
    if 'single' in kind:
        return lambda v: (isinstance(v, str) and v.startswith("'") and v.endswith("'"),
                          f"Expected single-quoted string, got {v!r}")
    return lambda v: (isinstance(v, str) and
                      ((v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'"))),
                      f"Expected quoted string, got {v!r}")

@pattern(r"must be (a )?(valid )?emoji", "must be a valid emoji")
def _emoji(m, **kw):
    # Unicode emoji ranges
    def is_emoji(s):
        if not isinstance(s, str) or not s: return False
        return any('\U0001F300' <= c <= '\U0001FAFF' or
                   '\u2600' <= c <= '\u27BF' or
                   '\U0001F900' <= c <= '\U0001F9FF' for c in s)
    return lambda v: (is_emoji(v), f"Expected emoji character, got {v!r}")

@pattern(r"must (not )?contain (any )?emoji", "must not contain emoji")
def _no_emoji(m, **kw):
    has_not = "not" in (m.group(1) or "")
    def has_emoji(s):
        return any('\U0001F300' <= c <= '\U0001FAFF' or
                   '\u2600' <= c <= '\u27BF' or
                   '\U0001F900' <= c <= '\U0001F9FF' for c in s)
    if has_not:
        return lambda v: (isinstance(v, str) and not has_emoji(v),
                          f"Expected no emoji, got {v!r}")
    return lambda v: (isinstance(v, str) and has_emoji(v),
                      f"Expected emoji, got {v!r}")

@pattern(r"must (be )?capitalized$", "must be capitalized")
def _capitalized(m, **kw):
    return lambda v: (isinstance(v, str) and len(v) > 0 and v[0].isupper(),
                      f"Expected capitalized string, got {v!r}")

@pattern(r"must (not )?have (a )?newline", "must not have a newline")
def _newline(m, **kw):
    no = "not" in (m.group(1) or "")
    if no:
        return lambda v: (isinstance(v, str) and '\n' not in v and '\r' not in v,
                          f"Expected no newline, got {v!r}")
    return lambda v: (isinstance(v, str) and ('\n' in v or '\r' in v),
                      f"Expected newline character, got {v!r}")

@pattern(r"must be (a )?(valid )?css class( name)?", "must be a valid css class name")
def _css_class(m, **kw):
    rx = re.compile(r"^-?[a-zA-Z_][a-zA-Z0-9_-]*$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected CSS class name, got {v!r}")

@pattern(r"must be (a )?(valid )?css property", "must be a valid css property")
def _css_property(m, **kw):
    PROPS = {
        "color","background","margin","padding","border","font","display","position",
        "width","height","top","left","right","bottom","overflow","z-index","opacity",
        "transition","transform","animation","flex","grid","content","visibility",
        "cursor","pointer-events","box-shadow","text-align","line-height","font-size",
        "font-weight","font-family","text-decoration","white-space","word-break",
        "letter-spacing","list-style","outline","resize","float","clear","vertical-align"
    }
    return lambda v: (isinstance(v, str) and v.lower().strip() in PROPS,
                      f"Expected CSS property name, got {v!r}")

@pattern(r"must be (a )?(valid )?html attribute", "must be a valid html attribute")
def _html_attr(m, **kw):
    ATTRS = {
        "id","class","style","href","src","alt","title","type","name","value",
        "placeholder","disabled","checked","selected","readonly","required",
        "action","method","enctype","target","rel","lang","dir","tabindex",
        "data-","aria-","role","for","colspan","rowspan","width","height",
        "hidden","autofocus","autocomplete","min","max","step","pattern","size"
    }
    return lambda v: (isinstance(v, str) and (v.lower() in ATTRS or
                      v.startswith("data-") or v.startswith("aria-")),
                      f"Expected HTML attribute name, got {v!r}")

@pattern(r"must be (a )?(valid )?xml tag", "must be a valid xml tag")
def _xml_tag(m, **kw):
    rx = re.compile(r"^[a-zA-Z_:][a-zA-Z0-9_:\-\.]*$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected XML tag name, got {v!r}")

@pattern(r"must be (a )?(valid )?markdown", "must be valid markdown")
def _markdown(m, **kw):
    MARKERS = ['# ','## ','### ','**','__','*','_','`','- ','1. ','> ','[','!']
    return lambda v: (isinstance(v, str) and any(marker in v for marker in MARKERS),
                      f"Expected Markdown-formatted text, got {v!r}")

@pattern(r"must be (a )?(valid )?natural language text", "must be valid natural language text")
def _natural_text(m, **kw):
    def check(v):
        if not isinstance(v, str) or len(v) < 2: return False, f"Expected text, got {v!r}"
        words = v.split()
        if not words: return False, f"Expected words, got empty string"
        avg_len = sum(len(w) for w in words) / len(words)
        return (avg_len >= 2 and avg_len <= 20 and len(words) >= 1,
                f"Expected natural language text, got {v!r}")
    return check


# ══════════════════════════════════════════════════════════════════════════════
# NUMERIC: advanced finance / science
# ══════════════════════════════════════════════════════════════════════════════

@pattern(r"must be (a )?(valid )?interest rate", "must be a valid interest rate")
def _interest_rate(m, **kw):
    return lambda v: (isinstance(v, (int, float)) and not isinstance(v, bool) and 0 <= v <= 100,
                      f"Expected interest rate 0-100%, got {v!r}")

@pattern(r"must be (a )?(valid )?gps (accuracy|precision)?", "must be a valid gps accuracy")
def _gps_accuracy(m, **kw):
    return lambda v: (isinstance(v, (int, float)) and not isinstance(v, bool) and 0 < v <= 100,
                      f"Expected GPS accuracy 0-100m, got {v!r}")

@pattern(r"must be (a )?(valid )?decibel( level)?", "must be a valid decibel level")
def _decibel(m, **kw):
    return lambda v: (isinstance(v, (int, float)) and not isinstance(v, bool) and -140 <= v <= 194,
                      f"Expected decibel level (-140 to 194 dB), got {v!r}")

@pattern(r"must be (a )?(valid )?ph( level)?", "must be a valid ph level")
def _ph(m, **kw):
    return lambda v: (isinstance(v, (int, float)) and not isinstance(v, bool) and 0 <= v <= 14,
                      f"Expected pH 0-14, got {v!r}")

@pattern(r"must be (a )?(valid )?frequency( hz)?", "must be a valid frequency hz")
def _frequency(m, **kw):
    return lambda v: (isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0,
                      f"Expected positive frequency (Hz), got {v!r}")

@pattern(r"must be (a )?(valid )?speed( value)?", "must be a valid speed value")
def _speed(m, **kw):
    return lambda v: (isinstance(v, (int, float)) and not isinstance(v, bool) and 0 <= v <= 300000,
                      f"Expected speed 0-300000, got {v!r}")

@pattern(r"must be (a )?(valid )?altitude", "must be a valid altitude")
def _altitude(m, **kw):
    return lambda v: (isinstance(v, (int, float)) and not isinstance(v, bool) and -420 <= v <= 100000,
                      f"Expected altitude -420 to 100000 meters, got {v!r}")

@pattern(r"must be (a )?non.?negative( number)?", "must be non-negative")
def _nonnegative(m, **kw):
    return lambda v: (isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0,
                      f"Expected non-negative number, got {v!r}")

@pattern(r"must be (a )?signed( integer)?", "must be a signed integer")
def _signed_int(m, **kw):
    return lambda v: (isinstance(v, int) and not isinstance(v, bool),
                      f"Expected signed integer, got {type(v).__name__!r}")

@pattern(r"must be (a )?unsigned( integer)?", "must be an unsigned integer")
def _unsigned_int(m, **kw):
    return lambda v: (isinstance(v, int) and not isinstance(v, bool) and v >= 0,
                      f"Expected unsigned integer, got {v!r}")

@pattern(r"must be (a )?16.?bit integer", "must be a 16-bit integer")
def _int16(m, **kw):
    return lambda v: (isinstance(v, int) and not isinstance(v, bool) and -32768 <= v <= 32767,
                      f"Expected 16-bit integer (-32768 to 32767), got {v!r}")

@pattern(r"must be (a )?32.?bit integer", "must be a 32-bit integer")
def _int32(m, **kw):
    return lambda v: (isinstance(v, int) and not isinstance(v, bool) and -2147483648 <= v <= 2147483647,
                      f"Expected 32-bit integer, got {v!r}")

@pattern(r"must be (a )?64.?bit integer", "must be a 64-bit integer")
def _int64(m, **kw):
    lim = 2**63
    return lambda v: (isinstance(v, int) and not isinstance(v, bool) and -lim <= v < lim,
                      f"Expected 64-bit integer, got {v!r}")

@pattern(r"must be (a )?natural( number)?$", "must be a natural number")
def _natural(m, **kw):
    return lambda v: (isinstance(v, int) and not isinstance(v, bool) and v > 0,
                      f"Expected natural number (1,2,3…), got {v!r}")

@pattern(r"must be (a )?(valid )?angle", "must be a valid angle")
def _angle(m, **kw):
    return lambda v: (isinstance(v, (int, float)) and not isinstance(v, bool) and 0 <= v < 360,
                      f"Expected angle 0-359.99°, got {v!r}")

@pattern(r"must be (a )?(valid )?ratio", "must be a valid ratio")
def _ratio(m, **kw):
    return lambda v: (isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0,
                      f"Expected non-negative ratio, got {v!r}")

@pattern(r"must be (a )?(valid )?z.?score", "must be a valid z-score")
def _zscore(m, **kw):
    return lambda v: (isinstance(v, (int, float)) and not isinstance(v, bool) and -10 <= v <= 10,
                      f"Expected z-score (-10 to 10), got {v!r}")

@pattern(r"must be (a )?power of (two|2)", "must be a power of two")
def _power_of_two(m, **kw):
    return lambda v: (isinstance(v, int) and not isinstance(v, bool) and v > 0 and (v & (v-1)) == 0,
                      f"Expected power of 2 (1,2,4,8,16…), got {v!r}")

@pattern(r"must be (an? )?(even|divisible) power of (two|2)", "must be an even power of two")
def _even_power_two(m, **kw):
    return lambda v: (isinstance(v, int) and not isinstance(v, bool) and v > 0
                      and (v & (v-1)) == 0 and int(math.log2(v)) % 2 == 0,
                      f"Expected even power of 2 (1,4,16,64…), got {v!r}")


# ══════════════════════════════════════════════════════════════════════════════
# DATES: more precision
# ══════════════════════════════════════════════════════════════════════════════

@pattern(r"must be (a )?leap year", "must be a leap year")
def _leap_year(m, **kw):
    def is_leap(v):
        if not isinstance(v, int): return False
        return (v % 4 == 0 and v % 100 != 0) or (v % 400 == 0)
    return lambda v: (is_leap(v), f"Expected leap year, got {v!r}")

@pattern(r"must be (a )?(valid )?fiscal year", "must be a valid fiscal year")
def _fiscal_year(m, **kw):
    rx = re.compile(r"^FY\d{2,4}$", re.IGNORECASE)
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected fiscal year (FY2024, FY24), got {v!r}")

@pattern(r"must be (a )?(valid )?century", "must be a valid century")
def _century(m, **kw):
    return lambda v: (isinstance(v, int) and not isinstance(v, bool) and 1 <= v <= 30,
                      f"Expected century (1-30), got {v!r}")

@pattern(r"must be (a )?(valid )?decade", "must be a valid decade")
def _decade(m, **kw):
    return lambda v: (isinstance(v, int) and not isinstance(v, bool) and
                      1900 <= v <= 2100 and v % 10 == 0,
                      f"Expected decade year (1990, 2000…), got {v!r}")

@pattern(r"must be (a )?recent( date)?", "must be a recent date")
def _recent_date(m, **kw):
    from datetime import date, timedelta
    def check(v):
        threshold = date.today() - timedelta(days=365)
        if isinstance(v, str):
            for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
                try: d = datetime.strptime(v, fmt).date(); break
                except: d = None
            if d is None: return False, f"Cannot parse: {v!r}"
        elif isinstance(v, date): d = v
        else: return False, "Expected date"
        return d >= threshold, f"Expected recent date (within 1 year), got {v!r}"
    return check

@pattern(r"must be (an? )?(age|years? old) between (\d+) and (\d+)", "must be an age between N and N")
def _age_between(m, **kw):
    lo, hi = int(m.group(3)), int(m.group(4))
    return lambda v: (isinstance(v, int) and not isinstance(v, bool) and lo <= v <= hi,
                      f"Expected age between {lo} and {hi}, got {v!r}")


# ══════════════════════════════════════════════════════════════════════════════
# COLLECTIONS: more patterns
# ══════════════════════════════════════════════════════════════════════════════

@pattern(r"must (be )?in ascending order", "must be in ascending order")
def _ascending(m, **kw):
    def check(v):
        if not isinstance(v, (list, tuple)): return False, "Expected list"
        try: return v == sorted(v), f"Expected ascending order, got {v!r}"
        except TypeError: return False, "Elements not comparable"
    return check

@pattern(r"must (be )?in descending order", "must be in descending order")
def _descending(m, **kw):
    def check(v):
        if not isinstance(v, (list, tuple)): return False, "Expected list"
        try: return v == sorted(v, reverse=True), f"Expected descending order, got {v!r}"
        except TypeError: return False, "Elements not comparable"
    return check

@pattern(r"must (have )?no (negative|neg) items?", "must have no negative items")
def _no_neg_items(m, **kw):
    return lambda v: (isinstance(v, (list, tuple)) and all(
        isinstance(i, (int, float)) and not isinstance(i, bool) and i >= 0 for i in v),
        f"Expected no negative items, got {v!r}")

@pattern(r"must (be a )?list of integers?", "must be a list of integers")
def _list_of_int(m, **kw):
    return lambda v: (isinstance(v, list) and all(
        isinstance(i, int) and not isinstance(i, bool) for i in v),
        f"Expected list of integers, got {v!r}")

@pattern(r"must (be a )?list of strings?", "must be a list of strings")
def _list_of_str(m, **kw):
    return lambda v: (isinstance(v, list) and all(isinstance(i, str) for i in v),
                      f"Expected list of strings, got {v!r}")

@pattern(r"must (be a )?list of floats?", "must be a list of floats")
def _list_of_float(m, **kw):
    return lambda v: (isinstance(v, list) and all(isinstance(i, float) for i in v),
                      f"Expected list of floats, got {v!r}")

@pattern(r"must (be a )?list of booleans?", "must be a list of booleans")
def _list_of_bool(m, **kw):
    return lambda v: (isinstance(v, list) and all(isinstance(i, bool) for i in v),
                      f"Expected list of booleans, got {v!r}")

@pattern(r"must (be a )?list of dicts?", "must be a list of dicts")
def _list_of_dict(m, **kw):
    return lambda v: (isinstance(v, list) and all(isinstance(i, dict) for i in v),
                      f"Expected list of dicts, got {v!r}")

@pattern(r"must (have )?all items? (be )?truthy", "must have all items truthy")
def _all_truthy(m, **kw):
    return lambda v: (isinstance(v, (list, tuple)) and all(bool(i) for i in v),
                      f"Expected all truthy items, got {v!r}")

@pattern(r"must (have )?all items? (be )?falsy", "must have all items falsy")
def _all_falsy(m, **kw):
    return lambda v: (isinstance(v, (list, tuple)) and not any(bool(i) for i in v),
                      f"Expected all falsy items, got {v!r}")

@pattern(r"must (have )?no (empty|blank) items?", "must have no empty items")
def _no_empty_items(m, **kw):
    return lambda v: (isinstance(v, (list, tuple)) and all(
        i is not None and i != "" and i != [] and i != {} for i in v),
        f"Expected no empty items, got {v!r}")

@pattern(r"must (be a )?power set", "must be a power set")
def _power_set(m, **kw):
    # Validates that a list of lists forms a valid power set structure
    def check(v):
        if not isinstance(v, list): return False, "Expected list of lists"
        sizes = sorted(len(s) if isinstance(s, (list, set)) else -1 for s in v)
        return all(s >= 0 for s in sizes), f"Expected power set (list of lists/sets), got {v!r}"
    return check

@pattern(r"must (be a )?contiguous (range|sequence)", "must be a contiguous range")
def _contiguous(m, **kw):
    def check(v):
        if not isinstance(v, (list, tuple)) or not v: return False, "Expected non-empty list"
        try:
            s = sorted(v)
            return all(s[i+1] - s[i] == 1 for i in range(len(s)-1)), \
                   f"Expected contiguous integers, got {v!r}"
        except TypeError: return False, "Elements must be comparable integers"
    return check


# ══════════════════════════════════════════════════════════════════════════════
# DICT: deeper checks
# ══════════════════════════════════════════════════════════════════════════════

@pattern(r"must (have )?all (values?|val) be strings?", "must have all values be strings")
def _dict_str_vals(m, **kw):
    return lambda v: (isinstance(v, dict) and all(isinstance(x, str) for x in v.values()),
                      f"Expected all string values, got non-strings in {v!r}")

@pattern(r"must (have )?all (values?|val) be integers?", "must have all values be integers")
def _dict_int_vals(m, **kw):
    return lambda v: (isinstance(v, dict) and all(
        isinstance(x, int) and not isinstance(x, bool) for x in v.values()),
        f"Expected all integer values in dict")

@pattern(r"must (have )?all (values?|val) be positive", "must have all values be positive")
def _dict_pos_vals(m, **kw):
    return lambda v: (isinstance(v, dict) and all(
        isinstance(x, (int, float)) and not isinstance(x, bool) and x > 0 for x in v.values()),
        f"Expected all positive values in dict")

@pattern(r"must (have )?all keys? be strings?", "must have all keys be strings")
def _dict_str_keys(m, **kw):
    return lambda v: (isinstance(v, dict) and all(isinstance(k, str) for k in v.keys()),
                      f"Expected all string keys in dict")

@pattern(r"must be (a )?flat dict(ionary)?", "must be a flat dict")
def _flat_dict(m, **kw):
    return lambda v: (isinstance(v, dict) and all(
        not isinstance(x, (dict, list)) for x in v.values()),
        f"Expected flat dict (no nested dicts/lists)")

@pattern(r"must be (a )?json.?serializable", "must be json-serializable")
def _json_serial(m, **kw):
    import json
    def check(v):
        try: json.dumps(v); return True, ""
        except (TypeError, ValueError) as e: return False, f"Not JSON-serializable: {e}"
    return check


# ══════════════════════════════════════════════════════════════════════════════
# SECURITY / COMPLIANCE
# ══════════════════════════════════════════════════════════════════════════════

@pattern(r"must not (contain|have|include) (a |an )?(sql|sql injection)", "must not contain sql injection")
def _no_sql_inj(m, **kw):
    SQLI = re.compile(
        r"(\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b|\bUNION\b"
        r"|\bEXEC\b|\bSCRIPT\b|--|;|\bOR\b\s+\d+=\d+|\bAND\b\s+\d+=\d+)",
        re.IGNORECASE)
    return lambda v: (isinstance(v, str) and not bool(SQLI.search(v)),
                      f"String contains potential SQL injection patterns")

@pattern(r"must not (contain|have|include) (a |an )?xss", "must not contain xss")
def _no_xss(m, **kw):
    XSS = re.compile(r"<script|javascript:|onerror=|onload=|eval\(|alert\(", re.IGNORECASE)
    return lambda v: (isinstance(v, str) and not bool(XSS.search(v)),
                      f"String contains potential XSS patterns")

@pattern(r"must not (contain|have|include) (a |an )?path traversal", "must not contain path traversal")
def _no_path_trav(m, **kw):
    return lambda v: (isinstance(v, str) and ".." not in v and not v.startswith("/etc/")
                      and not v.startswith("C:\\"),
                      f"String contains path traversal patterns")

@pattern(r"must be (a )?(valid )?bcrypt hash", "must be a valid bcrypt hash")
def _bcrypt(m, **kw):
    rx = re.compile(r"^\$2[aby]\$\d{2}\$.{53}$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected bcrypt hash ($2b$...), got {v!r}")

@pattern(r"must be (a )?(valid )?api key format", "must be a valid api key format")
def _api_key_fmt(m, **kw):
    rx = re.compile(r"^[a-zA-Z0-9_\-]{16,64}$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected API key (16-64 alphanumeric chars), got {v!r}")

@pattern(r"must be (a )?(valid )?bearer token", "must be a valid bearer token")
def _bearer(m, **kw):
    rx = re.compile(r"^Bearer\s+[A-Za-z0-9\-_\.]+$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected 'Bearer <token>', got {v!r}")

@pattern(r"must be (a )?(valid )?basic auth", "must be a valid basic auth")
def _basic_auth(m, **kw):
    import base64
    def check(v):
        if not isinstance(v, str): return False, "Expected string"
        if v.startswith("Basic "):
            v = v[6:]
        try:
            decoded = base64.b64decode(v).decode()
            return ":" in decoded, f"Expected base64 'user:pass', got {v!r}"
        except Exception:
            return False, f"Expected valid Basic Auth, got {v!r}"
    return check

@pattern(r"must (not )?have (a )?null byte", "must not have a null byte")
def _no_null_byte(m, **kw):
    no = "not" in (m.group(1) or "")
    if no:
        return lambda v: (isinstance(v, str) and '\x00' not in v,
                          f"Expected no null byte, got {v!r}")
    return lambda v: (isinstance(v, str) and '\x00' in v, f"Expected null byte")

@pattern(r"must be (a )?(valid )?otp( code)?", "must be a valid otp code")
def _otp(m, **kw):
    return lambda v: (isinstance(v, str) and v.isdigit() and len(v) in (6, 8),
                      f"Expected 6 or 8 digit OTP, got {v!r}")

@pattern(r"must be (a )?(valid )?totp( code)?", "must be a valid totp code")
def _totp(m, **kw):
    return lambda v: (isinstance(v, str) and v.isdigit() and len(v) == 6,
                      f"Expected 6-digit TOTP, got {v!r}")


# ══════════════════════════════════════════════════════════════════════════════
# GEOGRAPHIC / PHYSICAL
# ══════════════════════════════════════════════════════════════════════════════

@pattern(r"must be (a )?(valid )?zip code", "must be a valid zip code")
def _zip_code(m, **kw):
    rx = re.compile(r"^\d{5}(-\d{4})?$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected US ZIP code (XXXXX or XXXXX-XXXX), got {v!r}")

@pattern(r"must be (a )?(valid )?uk postcode", "must be a valid uk postcode")
def _uk_postcode(m, **kw):
    rx = re.compile(r"^[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}$", re.IGNORECASE)
    return lambda v: (isinstance(v, str) and bool(rx.match(v.strip())),
                      f"Expected UK postcode (e.g. SW1A 1AA), got {v!r}")

@pattern(r"must be (a )?(valid )?french postcode", "must be a valid french postcode")
def _fr_postcode(m, **kw):
    rx = re.compile(r"^(0[1-9]|[1-8]\d|9[0-5])\d{3}$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected French postal code (01000-95999), got {v!r}")

@pattern(r"must be (a )?(valid )?canadian postcode", "must be a valid canadian postcode")
def _ca_postcode(m, **kw):
    rx = re.compile(r"^[A-Z]\d[A-Z]\s?\d[A-Z]\d$", re.IGNORECASE)
    return lambda v: (isinstance(v, str) and bool(rx.match(v.strip())),
                      f"Expected Canadian postal code (A1A 1A1), got {v!r}")

@pattern(r"must be (a )?(valid )?us state( code)?", "must be a valid us state code")
def _us_state(m, **kw):
    STATES = {
        "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA","KS",
        "KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ","NM","NY",
        "NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT","VA","WA","WV",
        "WI","WY","DC","AS","GU","MP","PR","VI"
    }
    return lambda v: (isinstance(v, str) and v.upper() in STATES,
                      f"Expected US state code (CA, NY, TX…), got {v!r}")

@pattern(r"must be (a )?(valid )?timezone offset", "must be a valid timezone offset")
def _tz_offset(m, **kw):
    rx = re.compile(r"^[+-](?:0[0-9]|1[0-4]):[0-5][0-9]$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected timezone offset (+HH:MM), got {v!r}")

@pattern(r"must be (a )?(valid )?magnetic declination", "must be a valid magnetic declination")
def _mag_decl(m, **kw):
    return lambda v: (isinstance(v, (int, float)) and not isinstance(v, bool) and -180 <= v <= 180,
                      f"Expected magnetic declination (-180 to 180), got {v!r}")


# ══════════════════════════════════════════════════════════════════════════════
# DEVELOPER PRODUCTIVITY
# ══════════════════════════════════════════════════════════════════════════════

@pattern(r"must be (a )?(valid )?git branch( name)?", "must be a valid git branch name")
def _git_branch(m, **kw):
    rx = re.compile(r"^(?!.*\.\.)(?!.*@\{)(?!/)(?!.*/$)(?!\.)[\w\.\-/]+$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)) and not v.endswith(".lock"),
                      f"Expected git branch name, got {v!r}")

@pattern(r"must be (a )?(valid )?semantic commit( message)?", "must be a valid semantic commit message")
def _semantic_commit(m, **kw):
    rx = re.compile(r"^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)(\(.+\))?!?:\s.+")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected semantic commit (feat: …, fix: …), got {v!r}")

@pattern(r"must be (a )?(valid )?changelog entry", "must be a valid changelog entry")
def _changelog(m, **kw):
    rx = re.compile(r"^## \[[\d.]+\]")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected changelog entry (## [X.Y.Z]), got {v!r}")

@pattern(r"must be (a )?(valid )?pypi package name", "must be a valid pypi package name")
def _pypi_name(m, **kw):
    rx = re.compile(r"^([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9._-]*[a-zA-Z0-9])$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)) and len(v) <= 214,
                      f"Expected PyPI package name, got {v!r}")

@pattern(r"must be (a )?(valid )?npm package name", "must be a valid npm package name")
def _npm_name(m, **kw):
    rx = re.compile(r"^(@[a-z0-9-]+/)?[a-z0-9][a-z0-9._-]{0,213}$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected npm package name, got {v!r}")

@pattern(r"must be (a )?(valid )?github (repo |repository )?url", "must be a valid github repo url")
def _github_url(m, **kw):
    rx = re.compile(r"^https?://github\.com/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+/?$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected GitHub repo URL, got {v!r}")

@pattern(r"must be (a )?(valid )?terraform (resource )?name", "must be a valid terraform resource name")
def _tf_name(m, **kw):
    rx = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_-]*$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected Terraform resource name, got {v!r}")

@pattern(r"must be (a )?(valid )?yaml( string)?", "must be valid yaml")
def _yaml(m, **kw):
    def check(v):
        if not isinstance(v, str): return False, "Expected string"
        try:
            import yaml
            yaml.safe_load(v)
            return True, ""
        except ImportError:
            # fallback: basic structural check
            return (v.strip() != "" and not v.strip().startswith("{"),
                    f"Expected YAML string, got {v!r}")
        except Exception as e:
            return False, f"Invalid YAML: {e}"
    return check

@pattern(r"must be (a )?(valid )?toml( string)?", "must be valid toml")
def _toml(m, **kw):
    def check(v):
        if not isinstance(v, str): return False, "Expected string"
        try:
            import tomllib
            tomllib.loads(v)
            return True, ""
        except ImportError:
            try:
                import tomli
                tomli.loads(v)
                return True, ""
            except ImportError:
                rx = re.compile(r"^\[?[a-zA-Z]")
                return bool(rx.match(v.strip())), f"Expected TOML, got {v!r}"
        except Exception as e:
            return False, f"Invalid TOML: {e}"
    return check


# ══════════════════════════════════════════════════════════════════════════════
# ACCESSIBILITY / UX
# ══════════════════════════════════════════════════════════════════════════════

@pattern(r"must be (a )?(valid )?aria (role|label)", "must be a valid aria role")
def _aria_role(m, **kw):
    ROLES = {
        "alert","alertdialog","application","article","banner","button","cell",
        "checkbox","columnheader","combobox","complementary","contentinfo","definition",
        "dialog","directory","document","feed","figure","form","grid","gridcell","group",
        "heading","img","link","list","listbox","listitem","log","main","marquee","math",
        "menu","menubar","menuitem","menuitemcheckbox","menuitemradio","navigation",
        "none","note","option","presentation","progressbar","radio","radiogroup","region",
        "row","rowgroup","rowheader","scrollbar","search","searchbox","separator",
        "slider","spinbutton","status","switch","tab","table","tablist","tabpanel",
        "term","textbox","timer","toolbar","tooltip","tree","treegrid","treeitem"
    }
    return lambda v: (isinstance(v, str) and v.lower() in ROLES,
                      f"Expected ARIA role, got {v!r}")

@pattern(r"must be (a )?(valid )?wcag (level|grade)", "must be a valid wcag level")
def _wcag(m, **kw):
    LEVELS = {"A","AA","AAA","a","aa","aaa"}
    return lambda v: (isinstance(v, str) and v in LEVELS,
                      f"Expected WCAG level (A, AA, AAA), got {v!r}")

@pattern(r"must be (a )?(valid )?reading level", "must be a valid reading level")
def _reading_level(m, **kw):
    LEVELS = {"beginner","elementary","intermediate","advanced","expert",
              "A1","A2","B1","B2","C1","C2"}
    return lambda v: (isinstance(v, str) and v in LEVELS,
                      f"Expected reading level, got {v!r}")
