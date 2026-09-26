"""Randomness, password storage, digest comparison, and log redaction pairs.

``vulnerable_*`` functions are INTENTIONALLY VULNERABLE; the tests use only
synthetic passwords and tokens generated at run time.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import random
import re
import secrets

# --- Predictable tokens (CWE-338) -------------------------------------------


def vulnerable_reset_token(now: float) -> str:
    # INTENTIONALLY VULNERABLE (CWE-338): Mersenne Twister seeded with the
    # clock; anyone who knows the request time can regenerate the token.
    rng = random.Random(int(now))
    return f"{rng.getrandbits(128):032x}"


def fixed_reset_token() -> str:
    return secrets.token_urlsafe(32)


# --- Password storage (CWE-916, CWE-759) ------------------------------------

# OWASP Password Storage Cheat Sheet, scrypt option: N=2**17, r=8, p=1.
# 128 * r * N bytes = 128 MiB exceeds OpenSSL's 32 MiB default maxmem.
SCRYPT = {"n": 2**17, "r": 8, "p": 1, "maxmem": 132 * 1024 * 1024}


def vulnerable_hash_password(password: str) -> str:
    # INTENTIONALLY VULNERABLE (CWE-916, CWE-759): one fast unsalted hash.
    return hashlib.sha256(password.encode()).hexdigest()


def fixed_hash_password(password: str) -> str:
    salt = os.urandom(16)
    key = hashlib.scrypt(password.encode(), salt=salt, **SCRYPT)
    params = f"{SCRYPT['n']}${SCRYPT['r']}${SCRYPT['p']}"
    return f"scrypt${params}${salt.hex()}${key.hex()}"


def fixed_verify_password(password: str, stored: str) -> bool:
    _, n, r, p, salt, key = stored.split("$")
    candidate = hashlib.scrypt(
        password.encode(),
        salt=bytes.fromhex(salt),
        n=int(n),
        r=int(r),
        p=int(p),
        maxmem=SCRYPT["maxmem"],
    )
    return hmac.compare_digest(candidate, bytes.fromhex(key))


# --- Digest comparison (CWE-208) --------------------------------------------


def vulnerable_check_signature(key: bytes, body: bytes, tag: str) -> bool:
    # INTENTIONALLY VULNERABLE (CWE-208): == may return at the first
    # differing character, so response time depends on the secret tag.
    expected = hmac.new(key, body, hashlib.sha256).hexdigest()
    return expected == tag


def fixed_check_signature(key: bytes, body: bytes, tag: str) -> bool:
    expected = hmac.new(key, body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, tag)


# --- Secrets in logs (CWE-532) ----------------------------------------------

SENSITIVE_KEYS = {"authorization", "cookie", "password", "token", "api_key"}
BEARER = re.compile(r"(?i)\bbearer\s+[a-z0-9._~+/-]+=*")


def vulnerable_log_request(log: logging.Logger, headers: dict[str, str]) -> None:
    # INTENTIONALLY VULNERABLE (CWE-532): credentials copied into the log.
    log.info("request headers=%s", headers)


def redact(headers: dict[str, str]) -> dict[str, str]:
    return {
        k: "[REDACTED]" if k.lower() in SENSITIVE_KEYS else v
        for k, v in headers.items()
    }


class RedactingFilter(logging.Filter):
    """Last line of defense for free text that slips past redact()."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = BEARER.sub("Bearer [REDACTED]", record.getMessage())
        record.args = None
        return True


def fixed_log_request(log: logging.Logger, headers: dict[str, str]) -> None:
    log.info("request headers=%s", redact(headers))
