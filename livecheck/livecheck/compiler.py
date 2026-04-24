"""
Compiles natural language rules into Python validator functions.
Includes fuzzy matching for typos + French/Spanish keyword support.
"""
# patterns_v4 is imported at the END of this file (after PATTERNS list exists)

import re
import math
import ipaddress
from datetime import datetime
from typing import Callable, Any

PATTERNS: list[tuple[re.Pattern, Callable]] = []
_CANONICAL_RULES: list[str] = []

def pattern(regex: str, canonical: str = ""):
    def decorator(fn):
        PATTERNS.append((re.compile(regex, re.IGNORECASE), fn))
        _CANONICAL_RULES.append(canonical or regex)
        return fn
    return decorator

# ── Fuzzy normalization ───────────────────────────────────────────────────────

_CORRECTIONS: dict[str, str] = {
    "mst":"must","muts":"must","msut":"must","mus":"must","muust":"must",
    "doit":"must","devoir":"must","muss":"must","debe":"must",
    "bee":"be","etre":"be","être":"be","ser":"be",
    "positiv":"positive","positve":"positive","positif":"positive","poistive":"positive",
    "negatif":"negative","negatve":"negative","negativ":"negative",
    "numer":"number","numbr":"number","numbre":"number","nombre":"number","nomber":"number",
    "interger":"integer","intger":"integer","entier":"integer","integeer":"integer",
    "stirng":"string","strng":"string","sting":"string","chaine":"string","chaîne":"string",
    "emial":"email","eamil":"email","emaol":"email","courriel":"email","e-mail":"email",
    "valide":"valid","valied":"valid","vaid":"valid",
    "betwen":"between","betwene":"between","btween":"between","beteen":"between","entre":"between",
    "greeter":"greater","grater":"greater","superieur":"greater","supérieur":"greater",
    "lees":"less","inferieur":"less","inférieur":"less",
    "lenght":"length","lengt":"length","lenth":"length","longeur":"length","longueur":"length",
    "contian":"contain","contein":"contain","contenir":"contain",
    "letres":"letters","lettres":"letters","lettes":"letters",
    "digts":"digits","chiffres":"digits","chifres":"digits",
    "uppercas":"uppercase","upercase":"uppercase","majuscule":"uppercase","majuscules":"uppercase",
    "lowercas":"lowercase","lowerase":"lowercase","minuscule":"lowercase","minuscules":"lowercase",
    "uniqe":"unique","uniuqe":"unique",
    "requierd":"required","requred":"required","requis":"required",
    "alphanumerc":"alphanumeric","alphanumerique":"alphanumeric","alphanum":"alphanumeric",
    "booleen":"boolean","boolena":"boolean",
    "liste":"list","lsit":"list",
    "utl":"url","ulr":"url","lien":"url",
    "phoen":"phone","téléphone":"phone","telephone":"phone",
    "nto":"not","pas":"not",
    "emtpy":"empty","empyt":"empty","vide":"empty",
    "equla":"equal","eqaul":"equal","egal":"equal","égal":"equal",
    "divisble":"divisible","divisibl":"divisible",
    "multipe":"multiple","mutiple":"multiple",
    "palindrom":"palindrome","paldinrome":"palindrome",
    "trimed":"trimmed","trimmmed":"trimmed",
    "asci":"ascii","acii":"ascii",
    "jsno":"json","jons":"json",
    "uudi":"uuid","uuiid":"uuid",
    "adresse":"address","adress":"address",
    "carte":"card","credt":"credit",
    "pasword":"password","passord":"password",
    "mdp":"password",
    "slgu":"slug","slugg":"slug",
    "hexa":"hex","hexadecimal":"hex","hexadécimal":"hex",
    "prmie":"prime","priem":"prime","premier":"prime",
    "sqaure":"square","carré":"square",
    "soreted":"sorted","trié":"sorted","trie":"sorted",
    "truhy":"truthy","falshy":"falsy",
    "atleast":"at least",
    "atmost":"at most",
    "dat":"date","daten":"date",
}

def _fuzzy_normalize(text: str) -> str:
    text = text.strip().rstrip(".")
    # multi-word phrases first
    for wrong, right in sorted(_CORRECTIONS.items(), key=lambda x: -len(x[0])):
        if " " in wrong:
            text = re.sub(re.escape(wrong), right, text, flags=re.IGNORECASE)
    words = text.split()
    return " ".join(_CORRECTIONS.get(w.lower(), w) for w in words)

def _levenshtein(a: str, b: str) -> int:
    if len(a) < len(b): return _levenshtein(b, a)
    if not b: return len(a)
    prev = list(range(len(b)+1))
    for i, ca in enumerate(a):
        curr = [i+1]
        for j, cb in enumerate(b):
            curr.append(min(prev[j+1]+1, curr[j]+1, prev[j]+(0 if ca==cb else 1)))
        prev = curr
    return prev[-1]

def _suggest_closest(text: str) -> str:
    best, best_d = None, 999
    tl = text.lower()
    for canon in _CANONICAL_RULES:
        d = _levenshtein(tl, canon.lower())
        if d < best_d: best_d, best = d, canon
    if best and best_d < max(8, len(text)//3):
        return f'  Did you mean: "{best}"?'
    return ""

# ══════════════════════════════════════════════════════════════════════════════
# NUMBER RULES
# ══════════════════════════════════════════════════════════════════════════════

@pattern(r"must be (a )?positive (number|integer|float)?", "must be a positive number")
def _positive(m, **kw):
    return lambda v: (isinstance(v,(int,float)) and not isinstance(v,bool) and v>0, f"Expected positive, got {v!r}")

@pattern(r"must be (a )?negative (number|integer|float)?", "must be a negative number")
def _negative(m, **kw):
    return lambda v: (isinstance(v,(int,float)) and not isinstance(v,bool) and v<0, f"Expected negative, got {v!r}")

@pattern(r"must be between (\-?\d+(?:\.\d+)?) and (\-?\d+(?:\.\d+)?)", "must be between X and Y")
def _between(m, **kw):
    lo, hi = float(m.group(1)), float(m.group(2))
    return lambda v: (isinstance(v,(int,float)) and not isinstance(v,bool) and lo<=v<=hi, f"Expected between {lo} and {hi}, got {v!r}")

@pattern(r"must be (greater|more|larger) than (\-?\d+(?:\.\d+)?)", "must be greater than N")
def _gt(m, **kw):
    n = float(m.group(2))
    return lambda v: (isinstance(v,(int,float)) and not isinstance(v,bool) and v>n, f"Expected > {n}, got {v!r}")

@pattern(r"must be (less|smaller|fewer) than (\-?\d+(?:\.\d+)?)", "must be less than N")
def _lt(m, **kw):
    n = float(m.group(2))
    return lambda v: (isinstance(v,(int,float)) and not isinstance(v,bool) and v<n, f"Expected < {n}, got {v!r}")

@pattern(r"must be (greater|more) than or equal to (\-?\d+(?:\.\d+)?)", "must be greater than or equal to N")
def _gte(m, **kw):
    n = float(m.group(2))
    return lambda v: (isinstance(v,(int,float)) and not isinstance(v,bool) and v>=n, f"Expected >= {n}, got {v!r}")

@pattern(r"must be (less|smaller) than or equal to (\-?\d+(?:\.\d+)?)", "must be less than or equal to N")
def _lte(m, **kw):
    n = float(m.group(2))
    return lambda v: (isinstance(v,(int,float)) and not isinstance(v,bool) and v<=n, f"Expected <= {n}, got {v!r}")

@pattern(r"must be (an? )?integer", "must be an integer")
def _integer(m, **kw):
    return lambda v: (isinstance(v,int) and not isinstance(v,bool), f"Expected integer, got {type(v).__name__!r}")

@pattern(r"must be (a )?float", "must be a float")
def _float_rule(m, **kw):
    return lambda v: (isinstance(v,float), f"Expected float, got {type(v).__name__!r}")

@pattern(r"must be (a )?even (number|integer)?", "must be even")
def _even(m, **kw):
    return lambda v: (isinstance(v,int) and not isinstance(v,bool) and v%2==0, f"Expected even, got {v!r}")

@pattern(r"must be (a )?odd (number|integer)?", "must be odd")
def _odd(m, **kw):
    return lambda v: (isinstance(v,int) and not isinstance(v,bool) and v%2!=0, f"Expected odd, got {v!r}")

@pattern(r"must be (a )?multiple of (\d+)", "must be a multiple of N")
def _multiple_of(m, **kw):
    n = int(m.group(2))
    return lambda v: (isinstance(v,int) and not isinstance(v,bool) and v%n==0, f"Expected multiple of {n}, got {v!r}")

@pattern(r"must be divisible by (\d+)", "must be divisible by N")
def _divisible(m, **kw):
    n = int(m.group(1))
    return lambda v: (isinstance(v,int) and not isinstance(v,bool) and n!=0 and v%n==0, f"Expected divisible by {n}, got {v!r}")

@pattern(r"must be (a )?prime( number)?", "must be a prime number")
def _prime(m, **kw):
    def is_prime(n):
        if not isinstance(n,int) or isinstance(n,bool) or n<2: return False
        if n<4: return True
        if n%2==0 or n%3==0: return False
        i=5
        while i*i<=n:
            if n%i==0 or n%(i+2)==0: return False
            i+=6
        return True
    return lambda v: (is_prime(v), f"Expected prime, got {v!r}")

@pattern(r"must be (a )?perfect square", "must be a perfect square")
def _perfect_square(m, **kw):
    return lambda v: (isinstance(v,int) and not isinstance(v,bool) and v>=0 and int(math.isqrt(v))**2==v, f"Expected perfect square, got {v!r}")

@pattern(r"must be (a )?non.?zero( number)?", "must be non-zero")
def _nonzero(m, **kw):
    return lambda v: (isinstance(v,(int,float)) and not isinstance(v,bool) and v!=0, f"Expected non-zero, got {v!r}")

@pattern(r"must be (a )?finite( number)?", "must be finite")
def _finite(m, **kw):
    return lambda v: (isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v), f"Expected finite, got {v!r}")

@pattern(r"must be (a )?(number|numeric)", "must be a number")
def _number(m, **kw):
    return lambda v: (isinstance(v,(int,float)) and not isinstance(v,bool), f"Expected number, got {type(v).__name__!r}")

@pattern(r"must be (a )?percentage", "must be a percentage")
def _percentage(m, **kw):
    return lambda v: (isinstance(v,(int,float)) and not isinstance(v,bool) and 0<=v<=100, f"Expected 0-100, got {v!r}")

@pattern(r"must equal (\-?\d+(?:\.\d+)?)", "must equal N")
def _equal_num(m, **kw):
    n = float(m.group(1))
    return lambda v: (isinstance(v,(int,float)) and not isinstance(v,bool) and v==n, f"Expected {n}, got {v!r}")

@pattern(r"must be (a )?power of (\d+)", "must be a power of N")
def _power_of(m, **kw):
    base = int(m.group(2))
    def check(v):
        if not isinstance(v,int) or isinstance(v,bool) or v<1: return False,f"Expected power of {base}, got {v!r}"
        if v==1: return True,""
        x=v
        while x%base==0: x//=base
        return x==1, f"Expected power of {base}, got {v!r}"
    return check

@pattern(r"must be (in )?range\((\d+),\s*(\d+)\)", "must be in range(start, end)")
def _range(m, **kw):
    lo, hi = int(m.group(2)), int(m.group(3))
    return lambda v: (isinstance(v,int) and not isinstance(v,bool) and lo<=v<hi, f"Expected in range({lo},{hi}), got {v!r}")

@pattern(r"must be (a )?whole number", "must be a whole number")
def _whole(m, **kw):
    return lambda v: (isinstance(v,(int,float)) and not isinstance(v,bool) and float(v)==int(float(v)), f"Expected whole number, got {v!r}")

# ══════════════════════════════════════════════════════════════════════════════
# STRING RULES
# ══════════════════════════════════════════════════════════════════════════════

@pattern(r"must be (a )?(non[\-\s]?empty )?string", "must be a non-empty string")
def _string(m, **kw):
    nonempty = "non" in (m.group(2) or "")
    if nonempty:
        return lambda v: (isinstance(v,str) and len(v)>0, f"Expected non-empty string, got {v!r}")
    return lambda v: (isinstance(v,str), f"Expected string, got {type(v).__name__!r}")

@pattern(r"must (have length|be) (at least|no shorter than|minimum) (\d+)", "must have length at least N")
def _min_len(m, **kw):
    n = int(m.group(3))
    return lambda v: (hasattr(v,'__len__') and len(v)>=n, f"Expected length >= {n}, got {len(v) if hasattr(v,'__len__') else '?'}")

@pattern(r"must (have length|be) (at most|no longer than|maximum) (\d+)", "must have length at most N")
def _max_len(m, **kw):
    n = int(m.group(3))
    return lambda v: (hasattr(v,'__len__') and len(v)<=n, f"Expected length <= {n}, got {len(v) if hasattr(v,'__len__') else '?'}")

@pattern(r"must (have length|be exactly) (\d+)( characters?| chars?| items?| elements?)?", "must have length exactly N")
def _exact_len(m, **kw):
    n = int(m.group(2))
    return lambda v: (hasattr(v,'__len__') and len(v)==n, f"Expected length = {n}, got {len(v) if hasattr(v,'__len__') else '?'}")

@pattern(r"must be (a? ?valid )?email( address)?", "must be a valid email")
def _email(m, **kw):
    rx = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
    return lambda v: (isinstance(v,str) and bool(rx.match(v)), f"Expected valid email, got {v!r}")

@pattern(r"must be (a valid )?url", "must be a valid url")
def _url(m, **kw):
    rx = re.compile(r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE)
    return lambda v: (isinstance(v,str) and bool(rx.match(v)), f"Expected valid URL, got {v!r}")

@pattern(r"must (only )?contain (only )?letters", "must contain only letters")
def _letters(m, **kw):
    return lambda v: (isinstance(v,str) and v.isalpha(), f"Expected only letters, got {v!r}")

@pattern(r"must (only )?contain (only )?digits", "must contain only digits")
def _digits(m, **kw):
    return lambda v: (isinstance(v,str) and v.isdigit(), f"Expected only digits, got {v!r}")

@pattern(r"must (only )?contain (only )?alphanumeric", "must contain only alphanumeric characters")
def _alnum(m, **kw):
    return lambda v: (isinstance(v,str) and v.isalnum(), f"Expected alphanumeric, got {v!r}")

@pattern(r"must start with [\"']?([^\"'\s][^\"']*)[\"']?", "must start with 'prefix'")
def _startswith(m, **kw):
    prefix = m.group(1).strip()
    return lambda v: (isinstance(v,str) and v.startswith(prefix), f"Expected starts with {prefix!r}, got {v!r}")

@pattern(r"must end with [\"']?([^\"'\s][^\"']*)[\"']?", "must end with 'suffix'")
def _endswith(m, **kw):
    suffix = m.group(1).strip()
    return lambda v: (isinstance(v,str) and v.endswith(suffix), f"Expected ends with {suffix!r}, got {v!r}")

@pattern(r"must match (pattern |regex )?[\"']?([^\"']+)[\"']?", "must match pattern 'regex'")
def _regex(m, **kw):
    p = m.group(2)
    rx = re.compile(p)
    return lambda v: (isinstance(v,str) and bool(rx.search(v)), f"Does not match {p!r}: {v!r}")

@pattern(r"must be (one of) [\"']?([^\"']+)[\"']?|must be in [\"']([^\"']+)[\"']", "must be one of a, b, c")
def _oneof(m, **kw):
    raw = m.group(2) or m.group(3) or ""
    choices = [c.strip().strip("'\"") for c in raw.split(",")]
    return lambda v: (v in choices, f"Expected one of {choices}, got {v!r}")

@pattern(r"must be (lowercase|lower case|lower)", "must be lowercase")
def _lower(m, **kw):
    return lambda v: (isinstance(v,str) and v==v.lower(), f"Expected lowercase, got {v!r}")

@pattern(r"must be (uppercase|upper case|upper)", "must be uppercase")
def _upper(m, **kw):
    return lambda v: (isinstance(v,str) and v==v.upper(), f"Expected uppercase, got {v!r}")

@pattern(r"must be (a )?(valid )?json", "must be valid json")
def _json(m, **kw):
    import json
    def _check(v):
        if not isinstance(v,str): return False, f"Expected JSON string, got {type(v).__name__!r}"
        try: json.loads(v); return True,""
        except: return False, f"Expected valid JSON, got {v!r}"
    return _check

@pattern(r"must be (a )?(valid )?uuid", "must be a valid uuid")
def _uuid(m, **kw):
    rx = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)
    return lambda v: (isinstance(v,str) and bool(rx.match(v)), f"Expected UUID, got {v!r}")

@pattern(r"must be (a )?(valid )?ip( address)?", "must be a valid IP address")
def _ip(m, **kw):
    def _check(v):
        if not isinstance(v,str): return False, f"Expected string, got {type(v).__name__!r}"
        try: ipaddress.ip_address(v); return True,""
        except ValueError: return False, f"Expected valid IP address, got {v!r}"
    return _check

@pattern(r"must be (a )?(valid )?slug", "must be a valid slug")
def _slug(m, **kw):
    rx = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    return lambda v: (isinstance(v,str) and bool(rx.match(v)), f"Expected URL slug, got {v!r}")

@pattern(r"must be (a )?(valid )?hex( color)?", "must be a valid hex color")
def _hex_color(m, **kw):
    rx = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
    return lambda v: (isinstance(v,str) and bool(rx.match(v)), f"Expected hex color, got {v!r}")

@pattern(r"must be (a )?palindrome", "must be a palindrome")
def _palindrome(m, **kw):
    return lambda v: (isinstance(v,str) and v==v[::-1], f"Expected palindrome, got {v!r}")

@pattern(r"must be (properly )?trimmed", "must be trimmed")
def _trimmed(m, **kw):
    return lambda v: (isinstance(v,str) and v==v.strip(), f"Expected trimmed string, got {v!r}")

@pattern(r"must (only )?contain (only )?ascii", "must contain only ascii characters")
def _ascii(m, **kw):
    return lambda v: (isinstance(v,str) and v.isascii(), f"Expected ASCII only, got {v!r}")

@pattern(r"must (contain|include) [\"']([^\"']+)[\"']", "must contain 'substring'")
def _contains_substr(m, **kw):
    sub = m.group(2)
    return lambda v: (isinstance(v,str) and sub in v, f"Expected contains {sub!r}, got {v!r}")

@pattern(r"must not (contain|include) [\"']([^\"']+)[\"']", "must not contain 'substring'")
def _not_contains(m, **kw):
    sub = m.group(2)
    return lambda v: (isinstance(v,str) and sub not in v, f"Expected NOT containing {sub!r}, got {v!r}")

@pattern(r"must be (a )?(valid )?phone( number)?", "must be a valid phone number")
def _phone(m, **kw):
    rx = re.compile(r"^\+?[\d\s\-().]{7,20}$")
    return lambda v: (isinstance(v,str) and bool(rx.match(v)), f"Expected phone number, got {v!r}")

@pattern(r"must be (a )?(valid )?credit card( number)?", "must be a valid credit card number")
def _credit_card(m, **kw):
    def luhn(v):
        if not isinstance(v,str): return False
        d = v.replace(" ","").replace("-","")
        if not d.isdigit() or not (13<=len(d)<=19): return False
        total=0
        for i,c in enumerate(reversed(d)):
            n=int(c)
            if i%2==1:
                n*=2
                if n>9: n-=9
            total+=n
        return total%10==0
    return lambda v: (luhn(v), f"Expected valid credit card (Luhn), got {v!r}")

@pattern(r"must be (a )?(valid )?password", "must be a valid password")
def _password(m, **kw):
    def check(v):
        if not isinstance(v,str): return False, f"Expected string"
        errs=[]
        if len(v)<8: errs.append("min 8 chars")
        if not re.search(r"[A-Z]",v): errs.append("one uppercase")
        if not re.search(r"[a-z]",v): errs.append("one lowercase")
        if not re.search(r"\d",v): errs.append("one digit")
        if not re.search(r"[^a-zA-Z0-9]",v): errs.append("one special char")
        return (not errs), (f"Password missing: {', '.join(errs)}" if errs else "")
    return check

@pattern(r"must be (a )?(valid )?date( string)?", "must be a valid date")
def _date(m, **kw):
    def check(v):
        if not isinstance(v,str): return False, f"Expected date string"
        for fmt in ("%Y-%m-%d","%d/%m/%Y","%m/%d/%Y","%d-%m-%Y","%Y/%m/%d"):
            try: datetime.strptime(v,fmt); return True,""
            except: pass
        return False, f"Expected valid date (e.g. 2024-01-15), got {v!r}"
    return check

@pattern(r"must be (a )?(valid )?time( string)?", "must be a valid time")
def _time(m, **kw):
    rx = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)(:[0-5]\d)?$")
    return lambda v: (isinstance(v,str) and bool(rx.match(v)), f"Expected time HH:MM[:SS], got {v!r}")

@pattern(r"must be (a )?(valid )?semver", "must be a valid semver")
def _semver(m, **kw):
    rx = re.compile(r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?(\+[a-zA-Z0-9.]+)?$")
    return lambda v: (isinstance(v,str) and bool(rx.match(v)), f"Expected semver (1.2.3), got {v!r}")

@pattern(r"must be (a )?(valid )?mac address", "must be a valid mac address")
def _mac(m, **kw):
    rx = re.compile(r"^([0-9A-Fa-f]{2}[:\-]){5}[0-9A-Fa-f]{2}$")
    return lambda v: (isinstance(v,str) and bool(rx.match(v)), f"Expected MAC address, got {v!r}")

@pattern(r"must be (a )?(valid )?isbn", "must be a valid isbn")
def _isbn(m, **kw):
    rx = re.compile(r"^(?:97[89]-)?\d{1,5}-\d{1,7}-\d{1,7}-[\dX]$")
    return lambda v: (isinstance(v,str) and bool(rx.match(v)), f"Expected ISBN, got {v!r}")

@pattern(r"must be (a )?(valid )?postal code", "must be a valid postal code")
def _postal(m, **kw):
    rx = re.compile(r"^\d{4,10}(-\d{4})?$")
    return lambda v: (isinstance(v,str) and bool(rx.match(v)), f"Expected postal code, got {v!r}")

@pattern(r"must have no whitespace", "must have no whitespace")
def _no_ws(m, **kw):
    return lambda v: (isinstance(v,str) and not any(c.isspace() for c in v), f"Expected no whitespace, got {v!r}")

@pattern(r"must be (title|title[\s\-]?case)", "must be title case")
def _title_case(m, **kw):
    return lambda v: (isinstance(v,str) and v==v.title(), f"Expected title case, got {v!r}")

@pattern(r"must (only )?contain (only )?printable( characters?)?", "must contain only printable characters")
def _printable(m, **kw):
    return lambda v: (isinstance(v,str) and v.isprintable(), f"Expected printable chars only, got {v!r}")

@pattern(r"must be (a )?(valid )?iban", "must be a valid iban")
def _iban(m, **kw):
    rx = re.compile(r"^[A-Z]{2}\d{2}[A-Z0-9]{4,}$")
    return lambda v: (isinstance(v,str) and bool(rx.match(v.replace(" ",""))), f"Expected IBAN, got {v!r}")

@pattern(r"must be (a )?(valid )?color name", "must be a valid color name")
def _color_name(m, **kw):
    COLORS = {"red","green","blue","yellow","orange","purple","pink","black","white","gray","grey","brown","cyan","magenta","lime","navy","maroon","olive","teal","silver","gold"}
    return lambda v: (isinstance(v,str) and v.lower() in COLORS, f"Expected a color name, got {v!r}")

@pattern(r"must be (a )?(valid )?base64", "must be valid base64")
def _base64(m, **kw):
    rx = re.compile(r"^[A-Za-z0-9+/]*={0,2}$")
    return lambda v: (isinstance(v,str) and bool(rx.match(v)) and len(v)%4==0, f"Expected base64 string, got {v!r}")

@pattern(r"must be (a )?(valid )?html tag", "must be a valid html tag")
def _html_tag(m, **kw):
    TAGS = {"a","abbr","address","article","aside","audio","b","blockquote","body","br","button","canvas","caption","cite","code","col","colgroup","data","datalist","dd","del","details","dfn","dialog","div","dl","dt","em","embed","fieldset","figcaption","figure","footer","form","h1","h2","h3","h4","h5","h6","head","header","hr","html","i","iframe","img","input","ins","kbd","label","legend","li","link","main","map","mark","menu","meta","meter","nav","noscript","object","ol","optgroup","option","output","p","picture","pre","progress","q","rp","rt","ruby","s","samp","script","section","select","small","source","span","strong","style","sub","summary","sup","table","tbody","td","template","textarea","tfoot","th","thead","time","title","tr","track","u","ul","var","video","wbr"}
    return lambda v: (isinstance(v,str) and v.lower() in TAGS, f"Expected HTML tag name, got {v!r}")

# ══════════════════════════════════════════════════════════════════════════════
# TYPE / STRUCTURE RULES
# ══════════════════════════════════════════════════════════════════════════════

@pattern(r"must be (a )?(boolean|bool)", "must be a boolean")
def _bool(m, **kw):
    return lambda v: (isinstance(v,bool), f"Expected boolean, got {type(v).__name__!r}")

@pattern(r"must be (a )?list", "must be a list")
def _list(m, **kw):
    return lambda v: (isinstance(v,list), f"Expected list, got {type(v).__name__!r}")

@pattern(r"must be (a )?dict(ionary)?", "must be a dict")
def _dict(m, **kw):
    return lambda v: (isinstance(v,dict), f"Expected dict, got {type(v).__name__!r}")

@pattern(r"must be (a )?tuple", "must be a tuple")
def _tuple(m, **kw):
    return lambda v: (isinstance(v,tuple), f"Expected tuple, got {type(v).__name__!r}")

@pattern(r"must be (a )?set", "must be a set")
def _set(m, **kw):
    return lambda v: (isinstance(v,set), f"Expected set, got {type(v).__name__!r}")

@pattern(r"must not be (none|null|empty)", "must not be none")
def _notnone(m, **kw):
    return lambda v: (v is not None and v!="" and v!=[] and v!={}, f"Must not be None/empty, got {v!r}")

@pattern(r"must be (none|null)", "must be none")
def _isnone(m, **kw):
    return lambda v: (v is None, f"Expected None, got {v!r}")

@pattern(r"must be (truthy|true)", "must be truthy")
def _truthy(m, **kw):
    return lambda v: (bool(v), f"Expected truthy, got {v!r}")

@pattern(r"must be (falsy|false)", "must be falsy")
def _falsy(m, **kw):
    return lambda v: (not bool(v), f"Expected falsy, got {v!r}")

@pattern(r"must be (a )?non.?empty list", "must be a non-empty list")
def _nonempty_list(m, **kw):
    return lambda v: (isinstance(v,list) and len(v)>0, f"Expected non-empty list, got {v!r}")

@pattern(r"must be (a )?non.?empty dict(ionary)?", "must be a non-empty dict")
def _nonempty_dict(m, **kw):
    return lambda v: (isinstance(v,dict) and len(v)>0, f"Expected non-empty dict, got {v!r}")

@pattern(r"must have (at least )?(\d+) items?( or more)?", "must have at least N items")
def _min_items(m, **kw):
    n = int(m.group(2))
    return lambda v: (hasattr(v,'__len__') and len(v)>=n, f"Expected >= {n} items, got {len(v) if hasattr(v,'__len__') else '?'}")

@pattern(r"must have (at most )?(\d+) items?( or fewer)?", "must have at most N items")
def _max_items(m, **kw):
    n = int(m.group(2))
    return lambda v: (hasattr(v,'__len__') and len(v)<=n, f"Expected <= {n} items, got {len(v) if hasattr(v,'__len__') else '?'}")

@pattern(r"must have (exactly )?(\d+) items?", "must have exactly N items")
def _exact_items(m, **kw):
    n = int(m.group(2))
    return lambda v: (hasattr(v,'__len__') and len(v)==n, f"Expected exactly {n} items, got {len(v) if hasattr(v,'__len__') else '?'}")

@pattern(r"must be (a )?callable", "must be callable")
def _callable_rule(m, **kw):
    return lambda v: (callable(v), f"Expected callable, got {type(v).__name__!r}")

@pattern(r"must be (a )?sorted( list)?", "must be a sorted list")
def _sorted(m, **kw):
    def check(v):
        if not isinstance(v,list): return False, f"Expected list"
        try: return v==sorted(v), f"Expected sorted list, got {v!r}"
        except TypeError: return False, "List elements not comparable"
    return check

@pattern(r"must have (only )?unique( items?| elements?| values?)?", "must have unique items")
def _unique(m, **kw):
    return lambda v: (isinstance(v,(list,tuple)) and len(v)==len(set(v)), f"Expected unique items, got duplicates in {v!r}")

@pattern(r"must contain (the key|key) [\"']([^\"']+)[\"']", "must contain the key 'name'")
def _has_key(m, **kw):
    key = m.group(2)
    return lambda v: (isinstance(v,dict) and key in v, f"Expected key {key!r} in dict, got {list(v.keys()) if isinstance(v,dict) else v!r}")

@pattern(r"must be (a )?required( field)?", "must be required")
def _required(m, **kw):
    return lambda v: (v is not None and v!="" and v!=[] and v!={}, f"Field is required, got {v!r}")

# ══════════════════════════════════════════════════════════════════════════════
# COMPILER
# ══════════════════════════════════════════════════════════════════════════════

def compile_rule(text: str) -> Callable[[Any], tuple[bool, str]]:
    """
    Compile a natural language rule string into a validator function.
    Handles typos and French/Spanish keywords automatically.
    """
    original = text.strip().rstrip(".")
    normalized = _fuzzy_normalize(original)
    for attempt in [original, normalized]:
        for compiled_rx, factory in PATTERNS:
            m = compiled_rx.search(attempt)
            if m:
                fn = factory(m)
                fn.__doc__ = original
                return fn
    suggestion = _suggest_closest(normalized)
    raise ValueError(
        f"Could not compile rule: {original!r}\n"
        f"{suggestion}\n"
        "Call livecheck.list_patterns() to see all supported rules."
    )

def list_patterns() -> list[str]:
    """Return all supported canonical rule descriptions."""
    return sorted(set(_CANONICAL_RULES))


# ══════════════════════════════════════════════════════════════════════════════
# ── EXTENDED RULES v2 ─────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

# ── File & Path rules ─────────────────────────────────────────────────────────

@pattern(r"must be (a )?(valid )?file path", "must be a valid file path")
def _filepath(m, **kw):
    import os
    return lambda v: (isinstance(v, str) and len(v) > 0 and not any(c in v for c in '\0'),
                      f"Expected a file path, got {v!r}")

@pattern(r"must (have |be a valid )?(file )?extension (of |in )?[\"']?([^\"']+)[\"']?", "must have extension '.ext'")
def _file_ext(m, **kw):
    exts_raw = (m.group(4) or "").strip()
    exts = [e.strip().lower().lstrip(".") for e in exts_raw.replace(",", " ").split()]
    return lambda v: (isinstance(v, str) and any(v.lower().endswith("." + e) for e in exts),
                      f"Expected file with extension {exts}, got {v!r}")

@pattern(r"must be (a )?existing (file|path)", "must be an existing file")
def _existing_file(m, **kw):
    import os
    return lambda v: (isinstance(v, str) and os.path.exists(v),
                      f"Path does not exist: {v!r}")

@pattern(r"must be (an? )?absolute (path|file path)", "must be an absolute path")
def _abs_path(m, **kw):
    import os
    return lambda v: (isinstance(v, str) and os.path.isabs(v),
                      f"Expected absolute path, got {v!r}")

# ── Date / Time advanced ──────────────────────────────────────────────────────

@pattern(r"must be (in the )?past", "must be in the past")
def _in_past(m, **kw):
    from datetime import date as _date
    def check(v):
        if isinstance(v, str):
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
                try:
                    d = datetime.strptime(v, fmt).date(); break
                except: d = None
            if d is None: return False, f"Cannot parse date: {v!r}"
        elif isinstance(v, (_date, datetime)): d = v if isinstance(v, _date) else v.date()
        else: return False, f"Expected a date, got {type(v).__name__!r}"
        return d < _date.today(), f"Expected past date, got {v!r}"
    return check

@pattern(r"must be (in the )?future", "must be in the future")
def _in_future(m, **kw):
    from datetime import date as _date
    def check(v):
        if isinstance(v, str):
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
                try:
                    d = datetime.strptime(v, fmt).date(); break
                except: d = None
            if d is None: return False, f"Cannot parse date: {v!r}"
        elif isinstance(v, (_date, datetime)): d = v if isinstance(v, _date) else v.date()
        else: return False, f"Expected a date, got {type(v).__name__!r}"
        return d > _date.today(), f"Expected future date, got {v!r}"
    return check

@pattern(r"must be (a )?(valid )?datetime", "must be a valid datetime")
def _datetime_rule(m, **kw):
    def check(v):
        if not isinstance(v, str): return False, f"Expected datetime string"
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ",
                    "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M:%S"):
            try: datetime.strptime(v, fmt); return True, ""
            except: pass
        return False, f"Expected datetime string, got {v!r}"
    return check

@pattern(r"must be (a )?(valid )?year", "must be a valid year")
def _year(m, **kw):
    return lambda v: (isinstance(v, int) and 1000 <= v <= 9999,
                      f"Expected a year (1000-9999), got {v!r}")

@pattern(r"must be (a )?(valid )?month", "must be a valid month")
def _month(m, **kw):
    return lambda v: (isinstance(v, int) and 1 <= v <= 12,
                      f"Expected a month (1-12), got {v!r}")

@pattern(r"must be (a )?(valid )?day", "must be a valid day")
def _day(m, **kw):
    return lambda v: (isinstance(v, int) and 1 <= v <= 31,
                      f"Expected a day (1-31), got {v!r}")

@pattern(r"must be (a )?(valid )?weekday(?! date)", "must be a valid weekday")
def _weekday(m, **kw):
    DAYS = {"monday","tuesday","wednesday","thursday","friday","saturday","sunday",
            "mon","tue","wed","thu","fri","sat","sun",
            "lundi","mardi","mercredi","jeudi","vendredi","samedi","dimanche"}
    return lambda v: (isinstance(v, str) and v.lower() in DAYS,
                      f"Expected a weekday name, got {v!r}")

@pattern(r"must be (a )?(valid )?timezone", "must be a valid timezone")
def _timezone(m, **kw):
    def check(v):
        if not isinstance(v, str): return False, f"Expected timezone string"
        try:
            import zoneinfo
            zoneinfo.ZoneInfo(v); return True, ""
        except Exception:
            try:
                import pytz
                pytz.timezone(v); return True, ""
            except Exception:
                return False, f"Expected valid timezone (e.g. 'Europe/Paris'), got {v!r}"
    return check

@pattern(r"must be (a )?(valid )?duration", "must be a valid duration")
def _duration(m, **kw):
    rx = re.compile(r"^(\d+d)?(\d+h)?(\d+m)?(\d+s)?$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)) and len(v) > 0,
                      f"Expected duration (e.g. 1h30m, 2d), got {v!r}")

# ── Network & Security ────────────────────────────────────────────────────────

@pattern(r"must be (a )?(valid )?ipv4( address)?", "must be a valid ipv4 address")
def _ipv4(m, **kw):
    def check(v):
        if not isinstance(v, str): return False, f"Expected string"
        try: ipaddress.IPv4Address(v); return True, ""
        except: return False, f"Expected IPv4 address, got {v!r}"
    return check

@pattern(r"must be (a )?(valid )?ipv6( address)?", "must be a valid ipv6 address")
def _ipv6(m, **kw):
    def check(v):
        if not isinstance(v, str): return False, f"Expected string"
        try: ipaddress.IPv6Address(v); return True, ""
        except: return False, f"Expected IPv6 address, got {v!r}"
    return check

@pattern(r"must be (a )?(valid )?cidr", "must be a valid cidr")
def _cidr(m, **kw):
    def check(v):
        if not isinstance(v, str): return False, f"Expected string"
        try: ipaddress.ip_network(v, strict=False); return True, ""
        except: return False, f"Expected CIDR notation (e.g. 192.168.0.0/24), got {v!r}"
    return check

@pattern(r"must be (a )?(valid )?hostname", "must be a valid hostname")
def _hostname(m, **kw):
    rx = re.compile(r"^(?!-)[a-zA-Z0-9\-]{1,63}(?<!-)(\.[a-zA-Z0-9\-]{1,63})*$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)) and len(v) <= 253,
                      f"Expected valid hostname, got {v!r}")

@pattern(r"must be (a )?(valid )?port( number)?", "must be a valid port number")
def _port(m, **kw):
    return lambda v: (isinstance(v, int) and 0 <= v <= 65535,
                      f"Expected port 0-65535, got {v!r}")

@pattern(r"must be (a )?(valid )?md5( hash)?", "must be a valid md5 hash")
def _md5(m, **kw):
    rx = re.compile(r"^[a-f0-9]{32}$", re.IGNORECASE)
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected MD5 hash (32 hex chars), got {v!r}")

@pattern(r"must be (a )?(valid )?sha1( hash)?", "must be a valid sha1 hash")
def _sha1(m, **kw):
    rx = re.compile(r"^[a-f0-9]{40}$", re.IGNORECASE)
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected SHA1 hash (40 hex chars), got {v!r}")

@pattern(r"must be (a )?(valid )?sha256( hash)?", "must be a valid sha256 hash")
def _sha256(m, **kw):
    rx = re.compile(r"^[a-f0-9]{64}$", re.IGNORECASE)
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected SHA256 hash (64 hex chars), got {v!r}")

@pattern(r"must be (a )?(valid )?jwt( token)?", "must be a valid jwt token")
def _jwt(m, **kw):
    rx = re.compile(r"^[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]*$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected JWT (3 base64url parts separated by dots), got {v!r}")

@pattern(r"must be (a )?(valid )?domain( name)?", "must be a valid domain name")
def _domain(m, **kw):
    rx = re.compile(r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected domain name, got {v!r}")

@pattern(r"must be (a )?(valid )?user.?agent", "must be a valid user agent")
def _useragent(m, **kw):
    return lambda v: (isinstance(v, str) and len(v) >= 10 and any(
        kw in v for kw in ["Mozilla","Chrome","Safari","Firefox","Edge","Opera","curl","Python"]),
                      f"Expected user agent string, got {v!r}")

# ── Science & Math ────────────────────────────────────────────────────────────

@pattern(r"must be (a )?(valid )?latitude", "must be a valid latitude")
def _latitude(m, **kw):
    return lambda v: (isinstance(v, (int, float)) and not isinstance(v, bool) and -90 <= v <= 90,
                      f"Expected latitude (-90 to 90), got {v!r}")

@pattern(r"must be (a )?(valid )?longitude", "must be a valid longitude")
def _longitude(m, **kw):
    return lambda v: (isinstance(v, (int, float)) and not isinstance(v, bool) and -180 <= v <= 180,
                      f"Expected longitude (-180 to 180), got {v!r}")

@pattern(r"must be (a )?(valid )?coordinates?", "must be valid coordinates")
def _coordinates(m, **kw):
    def check(v):
        if isinstance(v, (list, tuple)) and len(v) == 2:
            lat, lon = v
            if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return True, ""
        return False, f"Expected [lat, lon] coordinates, got {v!r}"
    return check

@pattern(r"must be (a )?(valid )?probability", "must be a valid probability")
def _probability(m, **kw):
    return lambda v: (isinstance(v, (int, float)) and not isinstance(v, bool) and 0.0 <= v <= 1.0,
                      f"Expected probability (0.0-1.0), got {v!r}")

@pattern(r"must have (at most )?(\d+) decimal places?", "must have at most N decimal places")
def _decimal_places(m, **kw):
    n = int(m.group(2))
    def check(v):
        if not isinstance(v, (int, float)): return False, f"Expected number"
        s = str(v)
        if "." not in s: return True, ""
        decimals = len(s.split(".")[1])
        return decimals <= n, f"Expected at most {n} decimal places, got {decimals} in {v!r}"
    return check

@pattern(r"must be (a )?fibonacci( number)?", "must be a fibonacci number")
def _fibonacci(m, **kw):
    def is_fib(n):
        if not isinstance(n, int) or isinstance(n, bool) or n < 0: return False
        def is_perfect_square(x): return int(math.isqrt(x))**2 == x
        return is_perfect_square(5*n*n + 4) or is_perfect_square(5*n*n - 4)
    return lambda v: (is_fib(v), f"Expected a Fibonacci number, got {v!r}")

@pattern(r"must be (a )?roman numeral", "must be a roman numeral")
def _roman(m, **kw):
    rx = re.compile(r"^M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$", re.IGNORECASE)
    return lambda v: (isinstance(v, str) and bool(rx.match(v)) and len(v) > 0,
                      f"Expected Roman numeral, got {v!r}")

@pattern(r"must be (a )?binary( string)?", "must be a binary string")
def _binary(m, **kw):
    rx = re.compile(r"^(0b)?[01]+$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected binary string (0s and 1s), got {v!r}")

@pattern(r"must be (an? )?(octal|octet)( string)?", "must be an octal string")
def _octal(m, **kw):
    rx = re.compile(r"^(0o)?[0-7]+$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected octal string, got {v!r}")

@pattern(r"must be (a )?(hexadecimal|hex) string", "must be a hexadecimal string")
def _hex_string(m, **kw):
    rx = re.compile(r"^(0x)?[0-9a-fA-F]+$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected hexadecimal string, got {v!r}")

# ── Finance ───────────────────────────────────────────────────────────────────

@pattern(r"must be (a )?(valid )?currency( code)?", "must be a valid currency code")
def _currency(m, **kw):
    CODES = {"USD","EUR","GBP","JPY","CHF","CAD","AUD","CNY","INR","BRL","MXN",
             "KRW","SGD","HKD","NOK","SEK","DKK","NZD","ZAR","RUB","TRY","PLN",
             "CZK","HUF","ILS","AED","SAR","THB","IDR","MYR","PHP","VND","PKR",
             "EGP","NGN","KWD","QAR","MAD","DZD","TND","LBP","JOD","BHD","OMR"}
    return lambda v: (isinstance(v, str) and v.upper() in CODES,
                      f"Expected ISO 4217 currency code, got {v!r}")

@pattern(r"must be (a )?(valid )?country code", "must be a valid country code")
def _country_code(m, **kw):
    CODES = {
        "AF","AL","DZ","AD","AO","AG","AR","AM","AU","AT","AZ","BS","BH","BD","BB",
        "BY","BE","BZ","BJ","BT","BO","BA","BW","BR","BN","BG","BF","BI","CV","KH",
        "CM","CA","CF","TD","CL","CN","CO","KM","CG","CD","CR","HR","CU","CY","CZ",
        "DK","DJ","DM","DO","EC","EG","SV","GQ","ER","EE","SZ","ET","FJ","FI","FR",
        "GA","GM","GE","DE","GH","GR","GD","GT","GN","GW","GY","HT","HN","HU","IS",
        "IN","ID","IR","IQ","IE","IL","IT","JM","JP","JO","KZ","KE","KI","KP","KR",
        "KW","KG","LA","LV","LB","LS","LR","LY","LI","LT","LU","MG","MW","MY","MV",
        "ML","MT","MH","MR","MU","MX","FM","MD","MC","MN","ME","MA","MZ","MM","NA",
        "NR","NP","NL","NZ","NI","NE","NG","MK","NO","OM","PK","PW","PA","PG","PY",
        "PE","PH","PL","PT","QA","RO","RU","RW","KN","LC","VC","WS","SM","ST","SA",
        "SN","RS","SC","SL","SG","SK","SI","SB","SO","ZA","SS","ES","LK","SD","SR",
        "SE","CH","SY","TW","TJ","TZ","TH","TL","TG","TO","TT","TN","TR","TM","TV",
        "UG","UA","AE","GB","US","UY","UZ","VU","VE","VN","YE","ZM","ZW"
    }
    return lambda v: (isinstance(v, str) and v.upper() in CODES,
                      f"Expected ISO 3166-1 alpha-2 country code, got {v!r}")

@pattern(r"must be (a )?(valid )?language code", "must be a valid language code")
def _lang_code(m, **kw):
    CODES = {"af","sq","am","ar","hy","az","eu","be","bn","bs","bg","ca","zh","hr","cs",
             "da","nl","en","et","fi","fr","gl","ka","de","el","gu","ht","ha","he","hi",
             "hu","is","id","ga","it","ja","kn","kk","km","ko","ku","ky","lo","lv","lt",
             "lb","mk","mg","ms","ml","mt","mi","mr","mn","my","ne","no","or","ps","fa",
             "pl","pt","pa","ro","ru","sm","sr","sk","sl","so","es","sw","sv","tl","tg",
             "ta","tt","te","th","tr","tk","uk","ur","uz","vi","cy","xh","yi","yo","zu"}
    return lambda v: (isinstance(v, str) and v.lower() in CODES,
                      f"Expected ISO 639-1 language code, got {v!r}")

@pattern(r"must be (a )?positive (amount|price|cost)", "must be a positive amount")
def _positive_amount(m, **kw):
    return lambda v: (isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0,
                      f"Expected positive amount, got {v!r}")

@pattern(r"must have (at most )?2 decimal places?", "must have at most 2 decimal places")
def _two_decimals(m, **kw):
    def check(v):
        if not isinstance(v, (int, float)): return False, "Expected number"
        s = format(v, 'f').rstrip('0')
        if '.' not in s: return True, ""
        return len(s.split('.')[1]) <= 2, f"Expected max 2 decimal places, got {v!r}"
    return check

# ── Text / NLP ────────────────────────────────────────────────────────────────

@pattern(r"must not (have|contain) (consecutive )?spaces", "must not have consecutive spaces")
def _no_consecutive_spaces(m, **kw):
    return lambda v: (isinstance(v, str) and "  " not in v,
                      f"Expected no consecutive spaces, got {v!r}")

@pattern(r"must (have|contain) (at least )?(\d+) words?", "must have at least N words")
def _min_words(m, **kw):
    n = int(m.group(3))
    return lambda v: (isinstance(v, str) and len(v.split()) >= n,
                      f"Expected at least {n} words, got {len(v.split())} in {v!r}")

@pattern(r"must (have|contain) (at most )?(\d+) words?", "must have at most N words")
def _max_words(m, **kw):
    n = int(m.group(3))
    return lambda v: (isinstance(v, str) and len(v.split()) <= n,
                      f"Expected at most {n} words, got {len(v.split())} in {v!r}")

@pattern(r"must (not )?have (any )?special characters?", "must not have special characters")
def _no_special(m, **kw):
    has_not = "not" in (m.group(1) or "")
    rx = re.compile(r"[^a-zA-Z0-9\s]")
    if has_not:
        return lambda v: (isinstance(v, str) and not rx.search(v),
                          f"Expected no special characters, got {v!r}")
    return lambda v: (isinstance(v, str) and bool(rx.search(v)),
                      f"Expected special characters, got {v!r}")

@pattern(r"must be (a )?(valid )?username", "must be a valid username")
def _username(m, **kw):
    rx = re.compile(r"^[a-zA-Z0-9_\-\.]{3,30}$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected valid username (3-30 chars, letters/digits/_-.), got {v!r}")

@pattern(r"must be (a )?(valid )?hashtag", "must be a valid hashtag")
def _hashtag(m, **kw):
    rx = re.compile(r"^#[a-zA-Z][a-zA-Z0-9_]{0,99}$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected hashtag (#word), got {v!r}")

@pattern(r"must be (a )?(valid )?twitter handle", "must be a valid twitter handle")
def _twitter(m, **kw):
    rx = re.compile(r"^@[a-zA-Z0-9_]{1,15}$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected Twitter handle (@name), got {v!r}")

@pattern(r"must be (a )?(valid )?html( string)?", "must be valid html")
def _html_string(m, **kw):
    rx = re.compile(r"<[^>]+>")
    return lambda v: (isinstance(v, str) and bool(rx.search(v)),
                      f"Expected HTML string with tags, got {v!r}")

@pattern(r"must not (start|begin) with (a )?number", "must not start with a number")
def _not_start_number(m, **kw):
    return lambda v: (isinstance(v, str) and len(v) > 0 and not v[0].isdigit(),
                      f"Expected string not starting with digit, got {v!r}")

@pattern(r"must (start|begin) with (a )?uppercase", "must start with uppercase")
def _starts_uppercase(m, **kw):
    return lambda v: (isinstance(v, str) and len(v) > 0 and v[0].isupper(),
                      f"Expected string starting with uppercase, got {v!r}")

@pattern(r"must be (a )?(valid )?mime type", "must be a valid mime type")
def _mime(m, **kw):
    rx = re.compile(r"^(application|audio|font|image|model|text|video|multipart)/[a-zA-Z0-9!#$&\-^_.+]+$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected MIME type (e.g. image/jpeg), got {v!r}")

@pattern(r"must be (a )?(valid )?locale", "must be a valid locale")
def _locale(m, **kw):
    rx = re.compile(r"^[a-z]{2,3}(_[A-Z]{2})?$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected locale (e.g. en_US, fr_FR), got {v!r}")

# ── Collection advanced ───────────────────────────────────────────────────────

@pattern(r"must (only )?contain (only )?(numbers?|numeric) items?", "must contain only numeric items")
def _all_numbers(m, **kw):
    return lambda v: (isinstance(v, (list, tuple)) and all(isinstance(i, (int, float)) and not isinstance(i, bool) for i in v),
                      f"Expected all numeric items, got {v!r}")

@pattern(r"must (only )?contain (only )?string items?", "must contain only string items")
def _all_strings(m, **kw):
    return lambda v: (isinstance(v, (list, tuple)) and all(isinstance(i, str) for i in v),
                      f"Expected all string items, got {v!r}")

@pattern(r"must be (a )?subset of \[([^\]]+)\]", "must be a subset of [a, b, c]")
def _subset(m, **kw):
    raw = m.group(2)
    allowed = set(s.strip().strip("'\"") for s in raw.split(","))
    return lambda v: (isinstance(v, (list, set, tuple)) and set(v).issubset(allowed),
                      f"Expected subset of {allowed}, got {v!r}")

@pattern(r"must (not )?have (any )?duplicates?", "must not have duplicates")
def _no_duplicates(m, **kw):
    return lambda v: (isinstance(v, (list, tuple)) and len(v) == len(set(v)),
                      f"Expected no duplicates, got {v!r}")

@pattern(r"must be (a )?non.?empty set", "must be a non-empty set")
def _nonempty_set(m, **kw):
    return lambda v: (isinstance(v, set) and len(v) > 0,
                      f"Expected non-empty set, got {v!r}")

@pattern(r"must (be a )?flat list", "must be a flat list")
def _flat_list(m, **kw):
    return lambda v: (isinstance(v, list) and all(not isinstance(i, (list, tuple, dict)) for i in v),
                      f"Expected flat list (no nested collections), got {v!r}")

@pattern(r"must (be )?reversed( of)? \[([^\]]+)\]", "must be reversed list")
def _reversed_list(m, **kw):
    raw = m.group(3)
    expected = [s.strip().strip("'\"") for s in raw.split(",")]
    rev = list(reversed(expected))
    return lambda v: (v == rev, f"Expected {rev}, got {v!r}")

# ── Misc practical ────────────────────────────────────────────────────────────

@pattern(r"must be (a )?(valid )?semantic version", "must be a valid semantic version")
def _semver2(m, **kw):
    rx = re.compile(r"^\d+\.\d+\.\d+")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected semantic version X.Y.Z, got {v!r}")

@pattern(r"must be (a )?(valid )?cron( expression)?", "must be a valid cron expression")
def _cron(m, **kw):
    rx = re.compile(r"^(\*|[0-9,\-*/]+)\s+(\*|[0-9,\-*/]+)\s+(\*|[0-9,\-*/]+)\s+(\*|[0-9,\-*/]+)\s+(\*|[0-9,\-*/]+)$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v.strip())),
                      f"Expected cron expression (5 fields), got {v!r}")

@pattern(r"must be (a )?(valid )?git (commit )?hash", "must be a valid git commit hash")
def _git_hash(m, **kw):
    rx = re.compile(r"^[0-9a-f]{7,40}$", re.IGNORECASE)
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected git hash (7-40 hex chars), got {v!r}")

@pattern(r"must be (a )?(valid )?docker image", "must be a valid docker image name")
def _docker_image(m, **kw):
    rx = re.compile(r"^[a-z0-9]+(?:[._\-/][a-z0-9]+)*(:[a-zA-Z0-9._\-]+)?$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected docker image name, got {v!r}")

@pattern(r"must be (a )?(valid )?env var( name)?", "must be a valid env var name")
def _env_var(m, **kw):
    rx = re.compile(r"^[A-Z_][A-Z0-9_]*$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected env var name (UPPER_CASE), got {v!r}")

@pattern(r"must be (a )?(valid )?python identifier", "must be a valid python identifier")
def _py_identifier(m, **kw):
    import keyword
    return lambda v: (isinstance(v, str) and v.isidentifier() and not keyword.iskeyword(v),
                      f"Expected Python identifier, got {v!r}")

@pattern(r"must be (a )?(valid )?sql table name", "must be a valid sql table name")
def _sql_table(m, **kw):
    rx = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]{0,63}$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected SQL table name, got {v!r}")

@pattern(r"must be (a )?(valid )?color( value)?", "must be a valid color value")
def _color_value(m, **kw):
    def check(v):
        if not isinstance(v, str): return False, f"Expected string"
        v = v.strip()
        if re.match(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$", v): return True, ""
        if re.match(r"^rgb\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*\)$", v): return True, ""
        if re.match(r"^rgba\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*[\d.]+\s*\)$", v): return True, ""
        if re.match(r"^hsl\(\s*\d{1,3}\s*,\s*\d{1,3}%\s*,\s*\d{1,3}%\s*\)$", v): return True, ""
        NAMES = {"red","green","blue","black","white","yellow","orange","purple","pink","gray","grey","brown","cyan","magenta"}
        if v.lower() in NAMES: return True, ""
        return False, f"Expected CSS color (#hex, rgb(), hsl(), or name), got {v!r}"
    return check

@pattern(r"must be (a )?(valid )?semantic html", "must be valid semantic html")
def _semantic_html(m, **kw):
    SEMANTIC = {"header","footer","main","nav","section","article","aside","figure","figcaption","details","summary","time","mark","address"}
    rx = re.compile(r"<(" + "|".join(SEMANTIC) + r")[\s>]", re.IGNORECASE)
    return lambda v: (isinstance(v, str) and bool(rx.search(v)),
                      f"Expected semantic HTML (header/footer/main/nav/etc.), got {v!r}")

@pattern(r"must be (a )?(positive )?whole (number|integer) or zero", "must be a whole number or zero")
def _whole_or_zero(m, **kw):
    return lambda v: (isinstance(v, int) and not isinstance(v, bool) and v >= 0,
                      f"Expected non-negative integer, got {v!r}")

@pattern(r"must be (an? )?(exact )?multiple of (\d+(?:\.\d+)?)", "must be an exact multiple of N.N")
def _multiple_float(m, **kw):
    n = float(m.group(3))
    return lambda v: (isinstance(v, (int, float)) and not isinstance(v, bool) and abs(v % n) < 1e-9,
                      f"Expected multiple of {n}, got {v!r}")



# ══════════════════════════════════════════════════════════════════════════════
# ── EXTENDED RULES v3 — 80+ new patterns ─────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

# ── String: advanced format ───────────────────────────────────────────────────

@pattern(r"must be (a )?(valid )?ssn", "must be a valid ssn")
def _ssn(m, **kw):
    rx = re.compile(r"^\d{3}-\d{2}-\d{4}$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)) and not v.startswith("000")
                      and v[4:6] != "00" and v[7:] != "0000",
                      f"Expected US SSN (XXX-XX-XXXX), got {v!r}")

@pattern(r"must be (a )?(valid )?vin( number)?", "must be a valid vin number")
def _vin(m, **kw):
    rx = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$", re.IGNORECASE)
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected 17-char VIN number, got {v!r}")

@pattern(r"must be (a )?(valid )?swift( code)?", "must be a valid swift code")
def _swift(m, **kw):
    rx = re.compile(r"^[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v.upper())),
                      f"Expected SWIFT/BIC code (8 or 11 chars), got {v!r}")

@pattern(r"must be (a )?(valid )?ean(-?13)?( barcode)?", "must be a valid ean-13 barcode")
def _ean13(m, **kw):
    def check(v):
        if not isinstance(v, str) or not v.isdigit() or len(v) != 13:
            return False, f"Expected 13-digit EAN-13, got {v!r}"
        total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(v[:12]))
        check_digit = (10 - (total % 10)) % 10
        return int(v[-1]) == check_digit, f"EAN-13 checksum failed for {v!r}"
    return check

@pattern(r"must be (a )?(valid )?isin", "must be a valid isin")
def _isin(m, **kw):
    rx = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected ISIN (2 letters + 9 alphanumeric + 1 digit), got {v!r}")

@pattern(r"must be (a )?(valid )?doi", "must be a valid doi")
def _doi(m, **kw):
    rx = re.compile(r"^10\.\d{4,9}/[-._;()/:A-Z0-9]+$", re.IGNORECASE)
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected DOI (e.g. 10.1000/xyz123), got {v!r}")

@pattern(r"must be (a )?(valid )?orcid", "must be a valid orcid")
def _orcid(m, **kw):
    rx = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected ORCID (XXXX-XXXX-XXXX-XXXX), got {v!r}")

@pattern(r"must be (a )?(valid )?arxiv id", "must be a valid arxiv id")
def _arxiv(m, **kw):
    rx = re.compile(r"^\d{4}\.\d{4,5}(v\d+)?$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected arXiv ID (e.g. 2301.00001), got {v!r}")

@pattern(r"must be (a )?(valid )?npi( number)?", "must be a valid npi number")
def _npi(m, **kw):
    rx = re.compile(r"^\d{10}$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected 10-digit NPI number, got {v!r}")

@pattern(r"must be (a )?(valid )?pii free string", "must be a valid pii free string")
def _pii_free(m, **kw):
    patterns = [
        re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+"),               # email
        re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),                   # SSN
        re.compile(r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b"),  # credit card
        re.compile(r"\b\d{3}[\s\-]\d{3}[\s\-]\d{4}\b"),         # US phone
    ]
    return lambda v: (isinstance(v, str) and not any(p.search(v) for p in patterns),
                      f"String appears to contain PII (email, SSN, card number, or phone)")

@pattern(r"must be (a )?camel ?case( string)?", "must be camelCase string")
def _camelcase(m, **kw):
    rx = re.compile(r"^[a-z][a-zA-Z0-9]*$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected camelCase, got {v!r}")

@pattern(r"must be (a )?pascal ?case( string)?", "must be PascalCase string")
def _pascalcase(m, **kw):
    rx = re.compile(r"^[A-Z][a-zA-Z0-9]*$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected PascalCase, got {v!r}")

@pattern(r"must be (a )?snake[_\s-]?case( string)?", "must be snake_case string")
def _snakecase(m, **kw):
    rx = re.compile(r"^[a-z][a-z0-9_]*$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected snake_case, got {v!r}")

@pattern(r"must be (a )?kebab[_\s-]?case( string)?", "must be kebab-case string")
def _kebabcase(m, **kw):
    rx = re.compile(r"^[a-z][a-z0-9\-]*$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected kebab-case, got {v!r}")

@pattern(r"must be (a )?screaming[_\s-]?snake[_\s-]?case( string)?", "must be SCREAMING_SNAKE_CASE string")
def _screamingsnake(m, **kw):
    rx = re.compile(r"^[A-Z][A-Z0-9_]*$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected SCREAMING_SNAKE_CASE, got {v!r}")

@pattern(r"must be (a )?(valid )?strong password", "must be a valid strong password")
def _strong_password(m, **kw):
    def check(v):
        if not isinstance(v, str): return False, "Expected string"
        errs = []
        if len(v) < 12:      errs.append("min 12 chars")
        if not re.search(r"[A-Z]", v): errs.append("uppercase letter")
        if not re.search(r"[a-z]", v): errs.append("lowercase letter")
        if not re.search(r"\d", v):    errs.append("digit")
        if not re.search(r"[^a-zA-Z0-9]", v): errs.append("special char")
        if re.search(r"(.)\1{2,}", v): errs.append("no 3+ repeated chars")
        common = {"password","123456","qwerty","letmein","admin","welcome"}
        if v.lower() in common: errs.append("not a common password")
        return (not errs), (f"Strong password missing: {', '.join(errs)}" if errs else "")
    return check

@pattern(r"must be (a )?(valid )?semaphore name", "must be a valid semaphore name")
def _semaphore(m, **kw):
    rx = re.compile(r"^/[a-zA-Z0-9_\-]{1,30}$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected POSIX semaphore name (/name), got {v!r}")

@pattern(r"must be (a )?(valid )?topic name", "must be a valid topic name")
def _topic(m, **kw):
    rx = re.compile(r"^[a-zA-Z0-9_\-\.]{1,249}$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected topic name (alphanumeric, _-.), got {v!r}")

@pattern(r"must be (a )?(valid )?s3 bucket name", "must be a valid s3 bucket name")
def _s3_bucket(m, **kw):
    rx = re.compile(r"^[a-z0-9][a-z0-9\-]{1,61}[a-z0-9]$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)) and ".." not in v,
                      f"Expected S3 bucket name (3-63 lowercase chars), got {v!r}")

@pattern(r"must be (a )?(valid )?kubernetes name", "must be a valid kubernetes name")
def _k8s_name(m, **kw):
    rx = re.compile(r"^[a-z0-9][a-z0-9\-]{0,251}[a-z0-9]$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected Kubernetes name (lowercase, hyphens), got {v!r}")

@pattern(r"must be (a )?(valid )?aws (account )?id", "must be a valid aws account id")
def _aws_id(m, **kw):
    rx = re.compile(r"^\d{12}$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected 12-digit AWS account ID, got {v!r}")

@pattern(r"must be (a )?(valid )?azure (resource )?id", "must be a valid azure resource id")
def _azure_id(m, **kw):
    rx = re.compile(r"^/subscriptions/[0-9a-f\-]+/", re.IGNORECASE)
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected Azure resource ID, got {v!r}")

# ── Medical / Health ──────────────────────────────────────────────────────────

@pattern(r"must be (a )?(valid )?bmi", "must be a valid bmi")
def _bmi(m, **kw):
    return lambda v: (isinstance(v, (int, float)) and not isinstance(v, bool) and 10.0 <= v <= 80.0,
                      f"Expected BMI (10-80), got {v!r}")

@pattern(r"must be (a )?(valid )?blood pressure", "must be a valid blood pressure")
def _blood_pressure(m, **kw):
    rx = re.compile(r"^(\d{2,3})/(\d{2,3})$")
    def check(v):
        if not isinstance(v, str): return False, f"Expected string like '120/80'"
        m2 = rx.match(v)
        if not m2: return False, f"Expected blood pressure (SYS/DIA), got {v!r}"
        sys_, dia = int(m2.group(1)), int(m2.group(2))
        if not (60 <= sys_ <= 250): return False, f"Systolic out of range ({sys_})"
        if not (40 <= dia <= 150):  return False, f"Diastolic out of range ({dia})"
        return True, ""
    return check

@pattern(r"must be (a )?(valid )?heart rate", "must be a valid heart rate")
def _heart_rate(m, **kw):
    return lambda v: (isinstance(v, int) and not isinstance(v, bool) and 20 <= v <= 300,
                      f"Expected heart rate (20-300 bpm), got {v!r}")

@pattern(r"must be (a )?(valid )?temperature( celsius)?", "must be a valid temperature celsius")
def _temperature_c(m, **kw):
    return lambda v: (isinstance(v, (int, float)) and not isinstance(v, bool) and -273.15 <= v <= 100,
                      f"Expected Celsius temperature (-273.15 to 100), got {v!r}")

@pattern(r"must be (a )?(valid )?body temperature", "must be a valid body temperature")
def _body_temp(m, **kw):
    return lambda v: (isinstance(v, (int, float)) and not isinstance(v, bool) and 35.0 <= v <= 42.0,
                      f"Expected body temperature (35-42°C), got {v!r}")

@pattern(r"must be (a )?(valid )?blood type", "must be a valid blood type")
def _blood_type(m, **kw):
    TYPES = {"A+","A-","B+","B-","AB+","AB-","O+","O-"}
    return lambda v: (isinstance(v, str) and v.upper() in TYPES,
                      f"Expected blood type (A+, B-, AB+, O-, etc.), got {v!r}")

@pattern(r"must be (a )?(valid )?icd(-?10)? code", "must be a valid icd-10 code")
def _icd10(m, **kw):
    rx = re.compile(r"^[A-Z]\d{2}(\.\d{1,4})?$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v.upper())),
                      f"Expected ICD-10 code (e.g. A01.1), got {v!r}")

@pattern(r"must be (a )?(valid )?drug dosage", "must be a valid drug dosage")
def _dosage(m, **kw):
    rx = re.compile(r"^\d+(\.\d+)?\s*(mg|g|ml|mcg|µg|IU|units?)(/\w+)?$", re.IGNORECASE)
    return lambda v: (isinstance(v, str) and bool(rx.match(v.strip())),
                      f"Expected dosage (e.g. '500mg', '2.5ml'), got {v!r}")

# ── E-commerce ────────────────────────────────────────────────────────────────

@pattern(r"must be (a )?(valid )?sku", "must be a valid sku")
def _sku(m, **kw):
    rx = re.compile(r"^[A-Z0-9\-_]{3,30}$", re.IGNORECASE)
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected SKU (alphanumeric + -_), got {v!r}")

@pattern(r"must be (a )?(valid )?upc( code)?", "must be a valid upc code")
def _upc(m, **kw):
    def check(v):
        if not isinstance(v, str) or not v.isdigit() or len(v) != 12:
            return False, f"Expected 12-digit UPC, got {v!r}"
        total = sum(int(d) * (3 if i % 2 else 1) for i, d in enumerate(v[:11]))
        return (10 - total % 10) % 10 == int(v[11]), f"UPC checksum failed for {v!r}"
    return check

@pattern(r"must be (a )?(valid )?tracking number", "must be a valid tracking number")
def _tracking(m, **kw):
    rx = re.compile(r"^[A-Z0-9]{8,30}$", re.IGNORECASE)
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected tracking number (8-30 alphanumeric), got {v!r}")

@pattern(r"must be (a )?(valid )?coupon code", "must be a valid coupon code")
def _coupon(m, **kw):
    rx = re.compile(r"^[A-Z0-9\-_]{4,20}$", re.IGNORECASE)
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected coupon code (4-20 alphanumeric), got {v!r}")

@pattern(r"must be (a )?(valid )?price", "must be a valid price")
def _price(m, **kw):
    def check(v):
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return v >= 0, f"Expected non-negative price, got {v!r}"
        if isinstance(v, str):
            cleaned = re.sub(r"[,$€£¥\s]", "", v)
            try:
                n = float(cleaned)
                return n >= 0, f"Expected non-negative price, got {v!r}"
            except ValueError:
                pass
        return False, f"Expected price (number or '$X.XX'), got {v!r}"
    return check

@pattern(r"must be (a )?(valid )?quantity", "must be a valid quantity")
def _quantity(m, **kw):
    return lambda v: (isinstance(v, int) and not isinstance(v, bool) and v >= 0,
                      f"Expected non-negative integer quantity, got {v!r}")

@pattern(r"must be (a )?(valid )?weight", "must be a valid weight")
def _weight(m, **kw):
    rx = re.compile(r"^\d+(\.\d+)?\s*(kg|g|lb|lbs|oz|t|mg)?$", re.IGNORECASE)
    return lambda v: (isinstance(v, (int, float)) and v > 0
                      or (isinstance(v, str) and bool(rx.match(v.strip()))),
                      f"Expected weight (e.g. 1.5, '2.5kg', '5lbs'), got {v!r}")

# ── Numbers: advanced ─────────────────────────────────────────────────────────

@pattern(r"must be (a )?triangular( number)?", "must be a triangular number")
def _triangular(m, **kw):
    def is_tri(n):
        if not isinstance(n, int) or isinstance(n, bool) or n < 0: return False
        # n is triangular iff 8n+1 is a perfect square
        x = 8*n + 1
        return int(math.isqrt(x))**2 == x
    return lambda v: (is_tri(v), f"Expected triangular number (1,3,6,10,15…), got {v!r}")

@pattern(r"must be (a )?narcissistic( number)?", "must be a narcissistic number")
def _narcissistic(m, **kw):
    def is_narc(n):
        if not isinstance(n, int) or isinstance(n, bool) or n < 0: return False
        digits = [int(d) for d in str(n)]
        return sum(d**len(digits) for d in digits) == n
    return lambda v: (is_narc(v), f"Expected narcissistic number (153, 370, 371…), got {v!r}")

@pattern(r"must be (a )?palindrome number", "must be a palindrome number")
def _palindrome_num(m, **kw):
    return lambda v: (isinstance(v, int) and not isinstance(v, bool) and str(v) == str(v)[::-1],
                      f"Expected palindrome number (121, 1331…), got {v!r}")

@pattern(r"must be (a )?happy( number)?", "must be a happy number")
def _happy(m, **kw):
    def is_happy(n):
        if not isinstance(n, int) or isinstance(n, bool) or n <= 0: return False
        seen = set()
        while n != 1:
            n = sum(int(d)**2 for d in str(n))
            if n in seen: return False
            seen.add(n)
        return True
    return lambda v: (is_happy(v), f"Expected happy number (1,7,10,13,19…), got {v!r}")

@pattern(r"must be (an? )?abundant( number)?", "must be an abundant number")
def _abundant(m, **kw):
    def is_abundant(n):
        if not isinstance(n, int) or isinstance(n, bool) or n < 2: return False
        return sum(i for i in range(1, n) if n % i == 0) > n
    return lambda v: (is_abundant(v), f"Expected abundant number (12,18,20…), got {v!r}")

@pattern(r"must be (a )?perfect( number)?", "must be a perfect number")
def _perfect_num(m, **kw):
    def is_perfect(n):
        if not isinstance(n, int) or isinstance(n, bool) or n < 2: return False
        return sum(i for i in range(1, n) if n % i == 0) == n
    return lambda v: (is_perfect(v), f"Expected perfect number (6,28,496…), got {v!r}")

@pattern(r"must be (in )?scientific notation", "must be in scientific notation")
def _sci_notation(m, **kw):
    rx = re.compile(r"^-?\d+(\.\d+)?[eE][+-]?\d+$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected scientific notation (e.g. 1.5e10), got {v!r}")

@pattern(r"must be (a )?safe integer", "must be a safe integer")
def _safe_int(m, **kw):
    MAX_SAFE = 2**53 - 1
    return lambda v: (isinstance(v, int) and not isinstance(v, bool) and -MAX_SAFE <= v <= MAX_SAFE,
                      f"Expected safe integer (±{MAX_SAFE}), got {v!r}")

@pattern(r"must be (a )?byte( value)?", "must be a byte value")
def _byte(m, **kw):
    return lambda v: (isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= 255,
                      f"Expected byte (0-255), got {v!r}")

@pattern(r"must be (a )?(valid )?unix timestamp", "must be a valid unix timestamp")
def _unix_ts(m, **kw):
    # Reasonable range: 1970-01-01 to 2100-01-01
    return lambda v: (isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= 4102444800,
                      f"Expected Unix timestamp (0 to 4102444800), got {v!r}")

@pattern(r"must be (a )?round number", "must be a round number")
def _round_number(m, **kw):
    return lambda v: (isinstance(v, (int, float)) and not isinstance(v, bool) and v % 1 == 0,
                      f"Expected round number (no decimals), got {v!r}")

# ── Collections: advanced ─────────────────────────────────────────────────────

@pattern(r"must (be a )?matrix", "must be a matrix")
def _matrix(m, **kw):
    def check(v):
        if not isinstance(v, list): return False, f"Expected list of lists"
        if not v: return False, f"Matrix cannot be empty"
        if not all(isinstance(row, list) for row in v):
            return False, f"Expected list of lists (matrix)"
        row_len = len(v[0])
        if not all(len(row) == row_len for row in v):
            return False, f"Matrix rows must all have the same length"
        return True, ""
    return check

@pattern(r"must be (a )?square matrix", "must be a square matrix")
def _square_matrix(m, **kw):
    def check(v):
        if not isinstance(v, list) or not all(isinstance(r, list) for r in v):
            return False, f"Expected list of lists"
        n = len(v)
        return all(len(row) == n for row in v), f"Expected NxN matrix, rows have varying length"
    return check

@pattern(r"must (be )?contain (the )?value (\-?\d+(?:\.\d+)?)", "must contain the value N")
def _contains_value(m, **kw):
    val_str = m.group(3)
    try:
        val = int(val_str) if "." not in val_str else float(val_str)
    except ValueError:
        val = val_str
    return lambda v: (isinstance(v, (list, tuple, set)) and val in v,
                      f"Expected collection containing {val!r}, got {v!r}")

@pattern(r"must (be )?contain (the )?item [\"']([^\"']+)[\"']", "must contain the item 'x'")
def _contains_item(m, **kw):
    item = m.group(3)
    return lambda v: (isinstance(v, (list, tuple, set)) and item in v,
                      f"Expected collection containing {item!r}, got {v!r}")

@pattern(r"must (be )?all positive", "must all be positive")
def _all_positive(m, **kw):
    return lambda v: (isinstance(v, (list, tuple)) and all(
        isinstance(i, (int, float)) and not isinstance(i, bool) and i > 0 for i in v),
        f"Expected all positive values, got {v!r}")

@pattern(r"must (be )?all negative", "must all be negative")
def _all_negative(m, **kw):
    return lambda v: (isinstance(v, (list, tuple)) and all(
        isinstance(i, (int, float)) and not isinstance(i, bool) and i < 0 for i in v),
        f"Expected all negative values, got {v!r}")

@pattern(r"must (be )?strictly increasing", "must be strictly increasing")
def _strictly_increasing(m, **kw):
    def check(v):
        if not isinstance(v, (list, tuple)): return False, "Expected list"
        return all(v[i] < v[i+1] for i in range(len(v)-1)), f"Expected strictly increasing sequence, got {v!r}"
    return check

@pattern(r"must (be )?strictly decreasing", "must be strictly decreasing")
def _strictly_decreasing(m, **kw):
    def check(v):
        if not isinstance(v, (list, tuple)): return False, "Expected list"
        return all(v[i] > v[i+1] for i in range(len(v)-1)), f"Expected strictly decreasing, got {v!r}"
    return check

@pattern(r"must (be )?monotone( increasing)?", "must be monotone increasing")
def _monotone_inc(m, **kw):
    def check(v):
        if not isinstance(v, (list, tuple)): return False, "Expected list"
        return all(v[i] <= v[i+1] for i in range(len(v)-1)), f"Expected monotone increasing, got {v!r}"
    return check

@pattern(r"must (have )?no null(s| items?| values?)?", "must have no null values")
def _no_nulls(m, **kw):
    return lambda v: (isinstance(v, (list, tuple)) and all(i is not None for i in v),
                      f"Expected no null values in list, got {v!r}")

@pattern(r"must (have )?sum (of )?(\d+(?:\.\d+)?)", "must have sum of N")
def _sum_equals(m, **kw):
    n = float(m.group(3))
    return lambda v: (isinstance(v, (list, tuple)) and abs(sum(v) - n) < 1e-9,
                      f"Expected sum = {n}, got {sum(v) if isinstance(v,(list,tuple)) else '?'}")

@pattern(r"must (have )?sum (greater|more) than (\d+(?:\.\d+)?)", "must have sum greater than N")
def _sum_gt(m, **kw):
    n = float(m.group(3))
    return lambda v: (isinstance(v, (list, tuple)) and sum(v) > n,
                      f"Expected sum > {n}, got sum={sum(v) if isinstance(v,(list,tuple)) else '?'}")

@pattern(r"must (have )?sum (less|smaller) than (\d+(?:\.\d+)?)", "must have sum less than N")
def _sum_lt(m, **kw):
    n = float(m.group(3))
    return lambda v: (isinstance(v, (list, tuple)) and sum(v) < n,
                      f"Expected sum < {n}, got sum={sum(v) if isinstance(v,(list,tuple)) else '?'}")

@pattern(r"must (have )?average (of )?(\d+(?:\.\d+)?)", "must have average of N")
def _avg_equals(m, **kw):
    n = float(m.group(3))
    return lambda v: (isinstance(v, (list, tuple)) and len(v) > 0 and abs(sum(v)/len(v)-n) < 1e-9,
                      f"Expected average = {n}")

@pattern(r"must be (a )?superset of \[([^\]]+)\]", "must be a superset of [a, b, c]")
def _superset(m, **kw):
    raw = m.group(2)
    required = set(s.strip().strip("'\"") for s in raw.split(","))
    return lambda v: (isinstance(v, (list, set, tuple)) and required.issubset(set(v)),
                      f"Expected superset of {required}, got {v!r}")

@pattern(r"must (have )?max (of |value )?(\-?\d+(?:\.\d+)?)", "must have max of N")
def _max_val(m, **kw):
    n = float(m.group(3))
    return lambda v: (isinstance(v, (list, tuple)) and len(v) > 0 and max(v) == n,
                      f"Expected max = {n}, got {max(v) if isinstance(v,(list,tuple)) and v else '?'}")

@pattern(r"must (have )?min (of |value )?(\-?\d+(?:\.\d+)?)", "must have min of N")
def _min_val(m, **kw):
    n = float(m.group(3))
    return lambda v: (isinstance(v, (list, tuple)) and len(v) > 0 and min(v) == n,
                      f"Expected min = {n}, got {min(v) if isinstance(v,(list,tuple)) and v else '?'}")

# ── Dict: advanced ─────────────────────────────────────────────────────────────

@pattern(r"must have (all )?keys (in |matching )?[\"']?([^\"']+)[\"']?", "must have all keys in 'a, b, c'")
def _allowed_keys(m, **kw):
    raw = m.group(3)
    allowed = {s.strip().strip("'\"") for s in raw.split(",")}
    return lambda v: (isinstance(v, dict) and set(v.keys()).issubset(allowed),
                      f"Dict has unexpected keys: {set(v.keys()) - allowed if isinstance(v,dict) else '?'}")

@pattern(r"must (have )?no empty values?", "must have no empty values")
def _no_empty_values(m, **kw):
    return lambda v: (isinstance(v, dict) and all(val not in (None, "", [], {}) for val in v.values()),
                      f"Dict has empty values: {[k for k,vv in v.items() if vv in (None,'',[], {})] if isinstance(v,dict) else '?'}")

@pattern(r"must (have )?(\d+) (keys?|fields?|properties)", "must have N keys")
def _exact_keys(m, **kw):
    n = int(m.group(2))
    return lambda v: (isinstance(v, dict) and len(v) == n,
                      f"Expected {n} keys, got {len(v) if isinstance(v,dict) else '?'}")

# ── Datetime & Period ─────────────────────────────────────────────────────────

@pattern(r"must be (a )?weekend", "must be a weekend")
def _weekend(m, **kw):
    from datetime import date as _date
    def check(v):
        if isinstance(v, str):
            for fmt in ("%Y-%m-%d","%d/%m/%Y"):
                try: d = datetime.strptime(v, fmt).date(); break
                except: d = None
            if d is None: return False, f"Cannot parse date: {v!r}"
        elif isinstance(v, _date): d = v
        else: return False, f"Expected date"
        return d.weekday() >= 5, f"Expected weekend date, got {v!r} ({d.strftime('%A')})"
    return check

@pattern(r"must be (a )?weekday date( string)?", "must be a weekday date")
def _weekday_date(m, **kw):
    from datetime import date as _date
    def check(v):
        if isinstance(v, str):
            for fmt in ("%Y-%m-%d","%d/%m/%Y"):
                try: d = datetime.strptime(v, fmt).date(); break
                except: d = None
            if d is None: return False, f"Cannot parse date: {v!r}"
        elif isinstance(v, _date): d = v
        else: return False, f"Expected date"
        return d.weekday() < 5, f"Expected weekday, got {v!r} ({d.strftime('%A')})"
    return check

@pattern(r"must be (an? )?(iso|iso.?8601) (date|datetime)( string)?", "must be an iso 8601 date string")
def _iso8601(m, **kw):
    rx = re.compile(r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}(:\d{2})?(\.\d+)?(Z|[+-]\d{2}:?\d{2})?)?$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected ISO 8601 date, got {v!r}")

@pattern(r"must be (a )?(valid )?quarter", "must be a valid quarter")
def _quarter(m, **kw):
    QUARTERS = {"Q1","Q2","Q3","Q4","q1","q2","q3","q4","1","2","3","4",1,2,3,4}
    return lambda v: (v in QUARTERS, f"Expected Q1/Q2/Q3/Q4, got {v!r}")

# ── Environment & System ──────────────────────────────────────────────────────

@pattern(r"must be (a )?(valid )?log level", "must be a valid log level")
def _log_level(m, **kw):
    LEVELS = {"debug","info","warning","warn","error","critical","fatal",
              "DEBUG","INFO","WARNING","WARN","ERROR","CRITICAL","FATAL"}
    return lambda v: (isinstance(v, str) and v in LEVELS,
                      f"Expected log level (DEBUG/INFO/WARNING/ERROR/CRITICAL), got {v!r}")

@pattern(r"must be (a )?(valid )?http (status )?code", "must be a valid http status code")
def _http_status(m, **kw):
    return lambda v: (isinstance(v, int) and not isinstance(v, bool) and 100 <= v <= 599,
                      f"Expected HTTP status code (100-599), got {v!r}")

@pattern(r"must be (a )?(valid )?http method", "must be a valid http method")
def _http_method(m, **kw):
    METHODS = {"GET","POST","PUT","PATCH","DELETE","HEAD","OPTIONS","TRACE","CONNECT"}
    return lambda v: (isinstance(v, str) and v.upper() in METHODS,
                      f"Expected HTTP method, got {v!r}")

@pattern(r"must be (a )?(valid )?content type", "must be a valid content type")
def _content_type(m, **kw):
    rx = re.compile(r"^(application|audio|font|image|message|model|multipart|text|video)/[a-zA-Z0-9!#$&\-^_.+]+(;\s*.+)?$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected Content-Type, got {v!r}")

@pattern(r"must be (a )?(valid )?semantic (version|semver) range", "must be a valid semantic version range")
def _semver_range(m, **kw):
    rx = re.compile(r"^[\^~><=!*][\d.*]")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected semver range (e.g. ^1.0.0, >=2.0), got {v!r}")

@pattern(r"must be (a )?(valid )?package name", "must be a valid package name")
def _pkg_name(m, **kw):
    rx = re.compile(r"^[a-z][a-z0-9_\-]{0,213}$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected package name (lowercase), got {v!r}")

@pattern(r"must be (a )?(valid )?namespace", "must be a valid namespace")
def _namespace(m, **kw):
    rx = re.compile(r"^[a-zA-Z][a-zA-Z0-9_\.]*$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected namespace (e.g. com.example.app), got {v!r}")

@pattern(r"must be (a )?(valid )?color (in )?rgb", "must be a valid color in rgb")
def _color_rgb(m, **kw):
    rx = re.compile(r"^rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)$")
    def check(v):
        if not isinstance(v, str): return False, f"Expected string"
        mm = rx.match(v)
        if not mm: return False, f"Expected rgb(R,G,B), got {v!r}"
        return all(0 <= int(mm.group(i)) <= 255 for i in (1,2,3)), f"RGB values must be 0-255, got {v!r}"
    return check

@pattern(r"must (not )?be (a |an )?empty (string|value)?", "must not be an empty string")
def _nonempty_str_alt(m, **kw):
    is_not = "not" in (m.group(1) or "")
    if is_not:
        return lambda v: (v is not None and v != "" and v != [] and v != {},
                          f"Expected non-empty value, got {v!r}")
    return lambda v: (v == "" or v is None, f"Expected empty value, got {v!r}")

@pattern(r"must be (a )?(valid )?geohash", "must be a valid geohash")
def _geohash(m, **kw):
    rx = re.compile(r"^[0-9bcdefghjkmnpqrstuvwxyz]{1,12}$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected geohash string, got {v!r}")

@pattern(r"must be (a )?(valid )?what3words address", "must be a valid what3words address")
def _w3w(m, **kw):
    rx = re.compile(r"^[a-z]+\.[a-z]+\.[a-z]+$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected what3words address (word.word.word), got {v!r}")

@pattern(r"must be (a )?strong (api )?key", "must be a strong api key")
def _strong_api_key(m, **kw):
    return lambda v: (isinstance(v, str) and len(v) >= 32
                      and re.search(r"[A-Za-z]", v) and re.search(r"\d", v),
                      f"Expected strong API key (32+ chars, letters+digits), got {v!r}")

@pattern(r"must be (a )?(valid )?oauth scope", "must be a valid oauth scope")
def _oauth_scope(m, **kw):
    rx = re.compile(r"^[a-zA-Z0-9:._\-]+( [a-zA-Z0-9:._\-]+)*$")
    return lambda v: (isinstance(v, str) and bool(rx.match(v)),
                      f"Expected OAuth scope(s), got {v!r}")



# Load extended pattern sets
from .patterns_v4 import *  # noqa: F401,F403
