# Pattern reference

livecheck ships with **326 built-in patterns** compiled to pure Python at import time.

Run `livecheck patterns` or `python -c "from livecheck import list_patterns; print('\n'.join(list_patterns()))"` to see all patterns in your installed version.

## Numbers

| Pattern | Example passing value |
|---|---|
| `must be a positive number` | `42` |
| `must be a negative number` | `-5` |
| `must be between X and Y` | `must be between 1 and 100` → `50` |
| `must be greater than N` | `must be greater than 10` → `11` |
| `must be less than N` | `must be less than 10` → `9` |
| `must be greater than or equal to N` | `10` |
| `must be less than or equal to N` | `10` |
| `must be an integer` | `7` |
| `must be a float` | `3.14` |
| `must be even` | `4` |
| `must be odd` | `3` |
| `must be a multiple of N` | `must be a multiple of 7` → `21` |
| `must be divisible by N` | `must be divisible by 4` → `16` |
| `must be a prime number` | `17` |
| `must be a perfect square` | `16` |
| `must be a fibonacci number` | `13` |
| `must be a triangular number` | `15` |
| `must be a narcissistic number` | `153` |
| `must be a happy number` | `7` |
| `must be an abundant number` | `12` |
| `must be a perfect number` | `6` |
| `must be non-zero` | `1` |
| `must be finite` | `1.0` |
| `must be a number` | `42` |
| `must be a percentage` | `75.0` |
| `must be a valid probability` | `0.75` |
| `must equal N` | `must equal 42` → `42` |
| `must be a power of N` | `must be a power of 2` → `8` |
| `must be a power of two` | `64` |
| `must be in range(start, end)` | `must be in range(0, 10)` → `5` |
| `must be a whole number` | `3.0` |
| `must be non-negative` | `0` |
| `must be a natural number` | `1` |
| `must be a byte value` | `200` |
| `must be a 16-bit integer` | `32000` |
| `must be a 32-bit integer` | `2000000000` |
| `must be a 64-bit integer` | `9000000000` |
| `must be a safe integer` | `42` |
| `must be a valid unix timestamp` | `1700000000` |
| `must be a round number` | `42.0` |
| `must be in scientific notation` | `"1.5e10"` |
| `must be a valid latitude` | `48.8566` |
| `must be a valid longitude` | `2.3522` |
| `must be a valid bmi` | `22.5` |
| `must be a valid heart rate` | `72` |
| `must be a valid body temperature` | `36.6` |
| `must be a valid ph level` | `7.0` |
| `must be a valid altitude` | `100.0` |
| `must be a valid angle` | `180.0` |
| `must be a valid probability` | `0.5` |
| `must have at most N decimal places` | `must have at most 2 decimal places` → `3.14` |

## Strings — basic

| Pattern | Example |
|---|---|
| `must be a non-empty string` | `"hello"` |
| `must be a string` | `"hello"` |
| `must be lowercase` | `"hello"` |
| `must be uppercase` | `"HELLO"` |
| `must be title case` | `"Hello World"` |
| `must be trimmed` | `"hello"` |
| `must be capitalized` | `"Hello"` |
| `must be a palindrome` | `"racecar"` |
| `must be a single character` | `"x"` |
| `must be a single word` | `"hello"` |
| `must be a sentence` | `"Hello world!` |
| `must be an acronym` | `"NASA"` |
| `must have length at least N` | `"hello"` with N=3 |
| `must have length at most N` | `"hi"` with N=5 |
| `must have length exactly N` | `"abc"` with N=3 |
| `must have at least N words` | `"hello world"` with N=2 |
| `must have at most N words` | `"hello"` with N=3 |
| `must start with 'prefix'` | `"https://…"` |
| `must end with 'suffix'` | `"file.pdf"` |
| `must contain 'substring'` | `"hello world"` |
| `must not contain 'substring'` | `"clean text"` |
| `must match pattern 'regex'` | `"AB1234"` |
| `must be one of a, b, c` | `"admin"` |
| `must contain only letters` | `"hello"` |
| `must contain only digits` | `"12345"` |
| `must contain only alphanumeric characters` | `"abc123"` |
| `must contain only ascii characters` | `"hello"` |
| `must contain only printable characters` | `"hello"` |
| `must have no whitespace` | `"nospaces"` |
| `must not have consecutive spaces` | `"one space"` |
| `must not have a newline` | `"single line"` |
| `must not have special characters` | `"hello123"` |
| `must not start with a number` | `"hello"` |
| `must start with uppercase` | `"Hello"` |
| `must be wrapped in quotes` | `'"hello"'` |
| `must be a valid emoji` | `"🎉"` |
| `must not contain emoji` | `"clean text"` |

## Strings — format & identity

| Pattern | Example |
|---|---|
| `must be a valid email` | `"alice@example.com"` |
| `must be a valid url` | `"https://example.com"` |
| `must be a valid uuid` | `"6ba7b810-9dad-11d1-…"` |
| `must be a valid slug` | `"my-blog-post"` |
| `must be a valid hex color` | `"#FF5733"` |
| `must be a valid color value` | `"#FF5733"` or `"rgb(255,0,0)"` |
| `must be a valid color in rgb` | `"rgb(255, 0, 128)"` |
| `must be a valid color name` | `"red"` |
| `must be a valid password` | `"Secure@123"` |
| `must be a valid strong password` | `"MyStr0ng!Pass"` |
| `must be a valid phone number` | `"+33612345678"` |
| `must be a valid credit card number` | `"4532015112830366"` |
| `must be a valid username` | `"alice_42"` |
| `must be a valid hashtag` | `"#python"` |
| `must be a valid twitter handle` | `"@user"` |
| `must be camelCase string` | `"myVariable"` |
| `must be PascalCase string` | `"MyClass"` |
| `must be snake_case string` | `"my_var"` |
| `must be kebab-case string` | `"my-var"` |
| `must be SCREAMING_SNAKE_CASE string` | `"MY_CONST"` |

## Strings — network & security

| Pattern | Example |
|---|---|
| `must be a valid ip address` | `"192.168.1.1"` |
| `must be a valid ipv4 address` | `"10.0.0.1"` |
| `must be a valid ipv6 address` | `"::1"` |
| `must be a valid hostname` | `"api.example.com"` |
| `must be a valid domain name` | `"example.com"` |
| `must be a valid cidr` | `"192.168.0.0/24"` |
| `must be a valid mac address` | `"AA:BB:CC:DD:EE:FF"` |
| `must be a valid port number` | `8080` |
| `must be a valid jwt token` | `"header.payload.sig"` |
| `must be a valid md5 hash` | `"d41d8cd9…"` (32 hex) |
| `must be a valid sha1 hash` | (40 hex) |
| `must be a valid sha256 hash` | (64 hex) |
| `must be a valid bcrypt hash` | `"$2b$12$…"` |
| `must be a valid bearer token` | `"Bearer abc123"` |
| `must be a valid otp code` | `"123456"` |
| `must be a valid totp code` | `"987654"` |
| `must be a valid api key format` | `"abc123…"` (16-64 chars) |
| `must be a strong api key` | (32+ alphanumeric) |
| `must not contain sql injection` | `"hello world"` |
| `must not contain xss` | `"hello world"` |
| `must not contain path traversal` | `"safe/path"` |
| `must be a valid pii free string` | (no email/SSN/card) |

## Strings — dates & time

| Pattern | Example |
|---|---|
| `must be a valid date` | `"2024-01-15"` |
| `must be a valid time` | `"14:30"` |
| `must be a valid datetime` | `"2024-01-15 10:30:00"` |
| `must be an iso 8601 date string` | `"2024-01-15T10:30:00Z"` |
| `must be a valid semver` | `"1.2.3"` |
| `must be a valid semver range` | `"^1.0.0"` |
| `must be a valid timezone` | `"Europe/Paris"` |
| `must be a valid timezone offset` | `"+02:00"` |
| `must be a valid duration` | `"1h30m"` |
| `must be a valid cron expression` | `"0 9 * * 1-5"` |
| `must be a valid weekday` | `"Monday"` |
| `must be a weekday date` | `"2024-01-15"` |
| `must be a weekend` | `"2024-01-13"` |
| `must be in the past` | `"2020-01-01"` |
| `must be in the future` | `"2099-01-01"` |
| `must be a recent date` | (within last year) |
| `must be a valid year` | `2024` |
| `must be a valid month` | `6` |
| `must be a valid day` | `15` |
| `must be a valid quarter` | `"Q2"` |
| `must be a valid fiscal year` | `"FY2024"` |
| `must be a leap year` | `2024` |

## Strings — developer tooling

| Pattern | Example |
|---|---|
| `must be a valid python identifier` | `"my_var"` |
| `must be a valid env var name` | `"MY_VAR"` |
| `must be a valid sql table name` | `"users"` |
| `must be a valid pypi package name` | `"livecheck"` |
| `must be a valid npm package name` | `"my-package"` |
| `must be a valid git commit hash` | `"abc1234"` |
| `must be a valid git branch name` | `"feature/my-feature"` |
| `must be a valid semantic commit message` | `"feat: add login"` |
| `must be a valid github repo url` | `"https://github.com/user/repo"` |
| `must be a valid docker image name` | `"nginx:latest"` |
| `must be a valid kubernetes name` | `"my-service"` |
| `must be a valid s3 bucket name` | `"my-bucket"` |
| `must be a valid terraform resource name` | `"my_resource"` |
| `must be a valid namespace` | `"com.example.app"` |
| `must be valid json` | `'{"key": 1}'` |
| `must be valid yaml` | `"key: value"` |
| `must be valid base64` | `"aGVsbG8="` |
| `must be a valid mime type` | `"image/jpeg"` |
| `must be a valid html tag` | `"div"` |
| `must be a valid aria role` | `"button"` |
| `must be a valid wcag level` | `"AA"` |
| `must be a valid css class name` | `"my-class"` |

## Strings — geographic & business

| Pattern | Example |
|---|---|
| `must be a valid country code` | `"FR"` |
| `must be a valid language code` | `"fr"` |
| `must be a valid currency code` | `"EUR"` |
| `must be a valid us state code` | `"CA"` |
| `must be a valid zip code` | `"90210"` |
| `must be a valid uk postcode` | `"SW1A 1AA"` |
| `must be a valid french postcode` | `"75008"` |
| `must be a valid postal code` | `"12345"` |
| `must be a valid iban` | `"FR76…"` |
| `must be a valid swift code` | `"DEUTDEDB"` |
| `must be a valid isbn` | `"978-3-16-148410-0"` |
| `must be a valid ean-13 barcode` | `"4006381333931"` |
| `must be a valid isin` | `"US0378331005"` |
| `must be a valid doi` | `"10.1000/xyz123"` |
| `must be a valid orcid` | `"0000-0002-1825-0097"` |
| `must be a valid ssn` | `"123-45-6789"` |
| `must be a valid vin number` | `"1HGBH41JXMN109186"` |
| `must be a valid sku` | `"SKU-001-A"` |
| `must be a valid upc code` | `"012345678905"` |
| `must be a valid tracking number` | `"1Z9999999999999999"` |
| `must be a valid price` | `"$9.99"` or `9.99` |
| `must be a valid geohash` | `"u4pruydqqvj"` |
| `must be a valid what3words address` | `"filled.count.soap"` |

## Strings — medical

| Pattern | Example |
|---|---|
| `must be a valid blood type` | `"AB+"` |
| `must be a valid blood pressure` | `"120/80"` |
| `must be a valid icd-10 code` | `"A01.1"` |
| `must be a valid drug dosage` | `"500mg"` |
| `must be a valid npi number` | `"1234567890"` |

## Collections

| Pattern | Example |
|---|---|
| `must be a list` | `[1, 2, 3]` |
| `must be a non-empty list` | `[1]` |
| `must be a sorted list` | `[1, 2, 3]` |
| `must be in ascending order` | `[1, 2, 3]` |
| `must be in descending order` | `[3, 2, 1]` |
| `must be strictly increasing` | `[1, 2, 3]` |
| `must be strictly decreasing` | `[3, 2, 1]` |
| `must be monotone increasing` | `[1, 1, 2]` |
| `must be a contiguous range` | `[3, 4, 5]` |
| `must be a matrix` | `[[1,2],[3,4]]` |
| `must be a square matrix` | `[[1,2],[3,4]]` |
| `must be a flat list` | `[1, "a", True]` |
| `must be a subset of [a, b, c]` | `["a"]` |
| `must be a superset of [a, b, c]` | `["a","b","c","d"]` |
| `must have unique items` | `[1, 2, 3]` |
| `must not have duplicates` | `[1, 2, 3]` |
| `must have at least N items` | `[1,2,3]` with N=2 |
| `must have at most N items` | `[1,2]` with N=3 |
| `must have exactly N items` | `[1,2]` with N=2 |
| `must have no null values` | `[1, 2, 3]` |
| `must have no empty items` | `["a","b"]` |
| `must all be positive` | `[1, 2, 3]` |
| `must all be negative` | `[-1, -2]` |
| `must have all items truthy` | `[1, "x", True]` |
| `must have sum of N` | `[1,2,3]` → N=6 |
| `must have sum greater than N` | `[5,5]` → N=8 |
| `must have average of N` | `[2,4]` → N=3 |
| `must contain the value N` | `[1,2,3]` → N=2 |
| `must contain the item 'x'` | `["a","x","b"]` |
| `must have max of N` | `[1,2,3]` → N=3 |
| `must have min of N` | `[1,2,3]` → N=1 |
| `must be a list of integers` | `[1, 2, 3]` |
| `must be a list of strings` | `["a","b"]` |
| `must be a list of floats` | `[1.0, 2.0]` |
| `must be a list of booleans` | `[True, False]` |
| `must be a list of dicts` | `[{"a":1}]` |

## Types

| Pattern | Example |
|---|---|
| `must be a boolean` | `True` |
| `must be a dict` | `{"a": 1}` |
| `must be a non-empty dict` | `{"a": 1}` |
| `must be a set` | `{1, 2}` |
| `must be a non-empty set` | `{1}` |
| `must be a tuple` | `(1, 2)` |
| `must be none` | `None` |
| `must not be none` | `42` |
| `must be truthy` | `1` |
| `must be falsy` | `0` |
| `must be required` | `"value"` |
| `must be callable` | `len` |
| `must be a flat dict` | `{"a": 1}` |
| `must be json-serializable` | `{"a": [1, 2]}` |
| `must contain the key 'name'` | `{"name": "Alice"}` |
| `must have N keys` | `{"a":1,"b":2}` → N=2 |
| `must have all keys be strings` | `{"a":1}` |
| `must have all values be strings` | `{"a":"x"}` |
| `must have no empty values` | `{"a":"x","b":1}` |
