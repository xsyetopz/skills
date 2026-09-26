# Crypto and secrets

Cards for randomness, password storage, digest comparison, and secrets in
code and logs. Runnable pairs:
[`crypto.py`](../assets/examples/python/crypto.py) (tests in
`test_crypto.py`), [`argon2_hash.py`][argon2-example], and the scanner
helper [`scan_secrets.py`](../scripts/scan_secrets.py).

Tier: **Executed** on Apple M1 Max, macOS, Python 3.14.7 with OpenSSL
3.6.4 (`test_crypto.py`: 7 tests, OK), argon2-cffi 25.1.0 through uv,
gitleaks 8.30.1, trufflehog 3.97.4. Timings are machine-specific and were
taken while other agents shared the machine.

## Contents

- secrets module for tokens
- scrypt password hashing
- Argon2id password hashing
- Constant-time digest comparison
- gitleaks secret scan
- Regex fallback secret scan
- trufflehog without verification
- Log redaction

## secrets module for tokens

**Definition.** `secrets.token_urlsafe(n)`, `token_hex`, and
`token_bytes` draw from the operating system's CSPRNG. The `random`
module's Mersenne Twister is deterministic and "completely unsuitable for
cryptographic purposes" ([random][random]); the `secrets` docs say 32
bytes was believed sufficient as of 2015 ([secrets][secrets]). Fixes
CWE-338.

**Use when.**

- Password-reset tokens, session IDs, API keys, CSRF tokens, invite
  codes, or salts use `random`, `uuid1`, time, or a counter.

**Do not use when.**

- Simulations, sampling, and tests that need reproducible sequences:
  keep `random` with an explicit seed there.

**Example.**

```python
def vulnerable_reset_token(now):
    rng = random.Random(int(now))
    return f"{rng.getrandbits(128):032x}"

def fixed_reset_token():
    return secrets.token_urlsafe(32)
```

**Cost removed.** Candidates an attacker must try for a token issued
within a minute either side of a known time: 121 seeds (vulnerable), and
the test finds the real token among them; the fixed token is not in that
set.

**Verify.**

1. `python3 assets/examples/python/test_crypto.py PredictableTokens`
1. `rg -n 'import random|random\.(random|randint|choice|getrandbits)'
   .` in the target; trace each use to whether the value is a secret.

## scrypt password hashing

**Definition.** `hashlib.scrypt(password, salt=..., n=..., r=..., p=...,
maxmem=..., dklen=64)` (Python 3.6+, needs OpenSSL) is a memory-hard key
derivation function ([hashlib.scrypt][scrypt]). Store the algorithm,
parameters, salt, and key together, and compare keys with
`hmac.compare_digest`. OWASP lists scrypt N=2^17, r=8, p=1 as one
minimum configuration ([OWASP password storage][owasp-pw]). Fixes
CWE-916 and CWE-759.

**Use when.**

- Passwords are stored with MD5, SHA-1, SHA-256, or any single fast hash,
  with or without salt, and argon2 is not available.

**Do not use when.**

- The stored value must be recoverable (API keys you send onward): that
  needs encryption and key management, not hashing.
- Argon2id is available: OWASP lists it first; see the next card.

**Example.**

```python
SCRYPT = {"n": 2**17, "r": 8, "p": 1, "maxmem": 132 * 1024 * 1024}

def fixed_hash_password(password):
    salt = os.urandom(16)
    key = hashlib.scrypt(password.encode(), salt=salt, **SCRYPT)
    params = f"{SCRYPT['n']}${SCRYPT['r']}${SCRYPT['p']}"
    return f"scrypt${params}${salt.hex()}${key.hex()}"
```

These parameters need `128 * r * N` = 128 MiB. With the OpenSSL default
`maxmem` (the docs cite 32 MiB for OpenSSL 1.1.0), the call raised
`ValueError: [digital envelope routines] memory limit exceeded` locally;
132 MiB worked.

**Cost removed.** Cheap guesses for an attacker who has the stored hash.
Measured locally: one scrypt hash took 0.307 s; 100,000 SHA-256 hashes
took 0.044 s. Two users with the same password get equal SHA-256 hashes
and different scrypt records.

**Verify.**

1. `python3 assets/examples/python/test_crypto.py PasswordStorage`
1. `rg -n 'md5|sha1|sha256|pbkdf2_hmac' .` near password handling in the
   target; each hit gets a verdict.

## Argon2id password hashing

**Definition.** Argon2id through `argon2-cffi`'s `PasswordHasher`, which
produces an encoded string that carries salt and parameters, and checks it
with `verify` and `check_needs_rehash`. OWASP lists m=47104 KiB (46 MiB), t=1,
p=1 as one minimum Argon2id configuration. The stdlib has no Argon2.

**Use when.**

- New password storage, or a migration from a fast hash, where a native
  dependency is acceptable.

**Do not use when.**

- The platform cannot ship native extensions: use scrypt from
  `hashlib`.

**Example.** Runnable: `assets/examples/thirdparty/argon2_hash.py`.

```python
HASHER = PasswordHasher(time_cost=1, memory_cost=47104, parallelism=1)
encoded = HASHER.hash(password)          # "$argon2id$v=19$m=47104,..."
HASHER.verify(encoded, password)         # True, or VerifyMismatchError
HASHER.check_needs_rehash(encoded)       # True after raising params
```

**Cost removed.** Same as scrypt: equal passwords get different records;
a wrong password raises `VerifyMismatchError`.

**Verify.**

1. `uv run --no-project --with argon2-cffi python
   assets/examples/thirdparty/argon2_hash.py` prints `PASS` (local:
   argon2-cffi 25.1.0, encoded prefix `argon2id`, `v=19`,
   `m=47104,t=1,p=1`).
1. On login, the target calls `check_needs_rehash` and re-stores.

## Constant-time digest comparison

**Definition.** `hmac.compare_digest(a, b)` returns `a == b` without
content-based short circuits, so time does not reveal how many leading
characters matched; it can still reveal lengths and types
([hmac.compare_digest][compare]). Fixes CWE-208.

**Use when.**

- Comparing a received MAC, signature, webhook digest, API key, or reset
  token with the expected value.

**Do not use when.**

- Comparing a password: verify it with the password hash's own verify
  function, which compares internally.

**Example.**

```python
def fixed_check_signature(key, body, tag):
    expected = hmac.new(key, body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, tag)
```

**Cost removed.** The timing side channel on the comparison. The bundled
test proves only that decisions are unchanged for 4 tags. It does not
measure timing: a local timing test is noisy and does not transfer to a
network attacker.

**Verify.**

1. `python3 assets/examples/python/test_crypto.py DigestComparison`
1. `rg -n '(digest|signature|token|mac)\w* *[!=]= ' .` in the target;
   each secret comparison uses `compare_digest`.

## gitleaks secret scan

**Definition.** `gitleaks dir PATH` scans files and `gitleaks git`
scans history (`git log -p`); `--redact` hides secrets in output,
`-f json -r FILE` writes a report, and the exit code is 1 when leaks are
found ([gitleaks][gitleaks]). Detects CWE-798 candidates.

**Use when.**

- Every review: scan the working tree and git history, because a secret
  removed from HEAD is still in history.

**Do not use when.**

- Output would go into a report unredacted: always pass `--redact`.

**Example.** Session from `verify.sh` (synthetic keys generated at run
time in a temp directory):

```console
$ gitleaks dir --no-banner --redact -f json -r gl.json leaky
INF scanned ~101 bytes (101 bytes) in 1.84ms
WRN leaks found: 2
$ echo $?
1
$ jq -c '.[] | {RuleID, File, StartLine, Secret}' gl.json
{"RuleID":"aws-access-token","File":"settings.py","StartLine":1,...}
{"RuleID":"github-pat","File":"settings.py","StartLine":2,...}
```

Locally, gitleaks' AWS rule matched only base32-style IDs (`A-Z2-7`); a
synthetic ID with digits 0, 1, 8, or 9 was not reported.

**Cost removed.** Committed credentials found: 2 of 2 synthetic keys,
redacted to `REDACTED` in the report.

**Verify.**

1. `sh assets/examples/verify.sh local` asserts both rule IDs and the
   redaction.
1. In the target: `gitleaks git --redact -f json -r history.json .` and
   `gitleaks dir --redact .`; triage each hit (rotate real ones, never
   test them).

## Regex fallback secret scan

**Definition.** `scripts/scan_secrets.py PATH... [--json]`: a stdlib
scanner with four rules (AWS `AKIA`/`ASIA` access key IDs per the [IAM
identifier prefixes][aws-ids], GitHub token prefixes per [GitHub's token
formats][gh-tokens], PEM private-key headers, and quoted literals
assigned to password/secret/token/api-key names). It prints redacted
previews and exits 1 on any match.

**Use when.**

- gitleaks is not installed and cannot be.
- A report or a single file must be checked before it leaves the team.

**Do not use when.**

- gitleaks is available: it has far more rules and scans git history.

**Example.**

```console
$ python3 scripts/scan_secrets.py leaky
aws-access-key-id  leaky/settings.py:1  AKIA...
github-token       leaky/settings.py:2  ghp_...
2 match(es)
```

**Cost removed.** The same two synthetic keys found; previews show only
four characters; `.git`, `node_modules`, and binaries are skipped.

**Verify.**

1. `python3 scripts/test_scan_secrets.py` (4 tests: each rule matches,
   ordinary code does not, previews are redacted, exit codes).
1. `python3 scripts/scan_secrets.py REPORT.md` exits 0 before sharing.

## trufflehog without verification

**Definition.** `trufflehog filesystem PATH` and `trufflehog git URL`
detect credentials and, by default, verify each one by calling the
provider's API ([trufflehog][trufflehog]). `--no-verification` turns that
off; `--no-update` skips the self-update check.

**Use when.**

- A second detector is wanted for the same tree.

**Do not use when.**

- `--no-verification` is missing: verification uses the found
  credential against a live third-party API, which is credential use
  outside a review's scope.
- The JSON output would be pasted anywhere: locally, its `Raw` field held
  the full unredacted token.

**Example.**

```console
$ trufflehog filesystem --no-verification --no-update --json leaky
{"DetectorName":"Github","Verified":false,"Raw":"ghp_...",...}
```

**Cost removed.** Live calls to credential providers: 0 with
`--no-verification`.

**Verify.**

1. `sh assets/examples/verify.sh local` asserts `"Verified":false`.
1. Review the transcript: every trufflehog command has
   `--no-verification`.

## Log redaction

**Definition.** Remove credentials before they reach a log: redact known
sensitive keys when building the log record, and add a `logging.Filter`
on the handler as a last defense for free text. OWASP's logging cheat sheet
lists tokens, passwords, and session IDs among data to exclude
([OWASP logging][owasp-log]). Fixes CWE-532.

**Use when.**

- Code logs request headers, bodies, full URLs with query strings,
  exceptions that include them, or configuration objects.

**Do not use when.**

- The filter would be the only control: its pattern cannot know every
  secret format; redact at the source first.

**Example.**

```python
SENSITIVE_KEYS = {"authorization", "cookie", "password", "token",
                  "api_key"}

def redact(headers):
    return {k: "[REDACTED]" if k.lower() in SENSITIVE_KEYS else v
            for k, v in headers.items()}

class RedactingFilter(logging.Filter):
    def filter(self, record):
        record.msg = BEARER.sub("Bearer [REDACTED]", record.getMessage())
        record.args = None
        return True
```

**Cost removed.** Occurrences of the synthetic token in the captured
log: 1 (vulnerable) to 0 (fixed), with non-secret headers kept and two
`[REDACTED]` markers.

**Verify.**

1. `python3 assets/examples/python/test_crypto.py SecretsInLogs`
1. `rg -n 'log(ger)?\.\w+\(.*(headers|request|token|password)' .` in the
   target; trace each hit.

[random]: https://docs.python.org/3/library/random.html
[secrets]: https://docs.python.org/3/library/secrets.html
[scrypt]: https://docs.python.org/3/library/hashlib.html#hashlib.scrypt
[owasp-pw]:
https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html
[compare]: https://docs.python.org/3/library/hmac.html#hmac.compare_digest
[gitleaks]: https://github.com/gitleaks/gitleaks
[aws-ids]:
https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_identifiers.html#identifiers-prefixes
[gh-tokens]:
https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/about-authentication-to-github#githubs-token-formats
[trufflehog]: https://github.com/trufflesecurity/trufflehog
[owasp-log]:
https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html
[argon2-example]: ../assets/examples/thirdparty/argon2_hash.py
