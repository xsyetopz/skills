"""Exploit-condition and fix tests for crypto.py (stdlib only).

Run: python3 test_crypto.py
"""

from __future__ import annotations

import io
import logging
import os
import secrets
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import crypto


class PredictableTokens(unittest.TestCase):
    def test_clock_seeded_token_is_recomputed_from_a_time_window(self) -> None:
        issued_at = 1_790_000_000.25  # synthetic request time
        token = crypto.vulnerable_reset_token(issued_at)
        guesses = {
            crypto.vulnerable_reset_token(issued_at + delta) for delta in range(-60, 61)
        }
        self.assertIn(token, guesses)

    def test_secrets_token_is_not_in_the_window(self) -> None:
        issued_at = 1_790_000_000.25
        guesses = {
            crypto.vulnerable_reset_token(issued_at + delta) for delta in range(-60, 61)
        }
        token = crypto.fixed_reset_token()
        self.assertNotIn(token, guesses)
        self.assertGreaterEqual(len(token), 43)  # 32 bytes, base64url


class PasswordStorage(unittest.TestCase):
    def test_unsalted_hash_reveals_shared_passwords(self) -> None:
        password = secrets.token_hex(8)
        first = crypto.vulnerable_hash_password(password)
        self.assertEqual(first, crypto.vulnerable_hash_password(password))

    def test_scrypt_is_salted_and_verifies(self) -> None:
        password = secrets.token_hex(8)
        first = crypto.fixed_hash_password(password)
        second = crypto.fixed_hash_password(password)
        self.assertNotEqual(first, second)
        self.assertTrue(crypto.fixed_verify_password(password, first))
        self.assertFalse(crypto.fixed_verify_password(password + "x", first))
        self.assertTrue(first.startswith("scrypt$131072$8$1$"))


class DigestComparison(unittest.TestCase):
    def test_same_decisions(self) -> None:
        key, body = secrets.token_bytes(32), b"payload"
        good = crypto.hmac.new(key, body, "sha256").hexdigest()
        for tag in (good, "0" * 64, good[:-1] + "0", ""):
            with self.subTest(tag=tag[:8]):
                self.assertEqual(
                    crypto.vulnerable_check_signature(key, body, tag),
                    crypto.fixed_check_signature(key, body, tag),
                )


class SecretsInLogs(unittest.TestCase):
    def capture(self, with_filter: bool) -> tuple[logging.Logger, io.StringIO]:
        stream = io.StringIO()
        log = logging.getLogger(f"test.{self.id()}.{with_filter}")
        log.propagate = False
        log.setLevel(logging.INFO)
        handler = logging.StreamHandler(stream)
        if with_filter:
            handler.addFilter(crypto.RedactingFilter())
        log.addHandler(handler)
        self.addCleanup(log.removeHandler, handler)
        return log, stream

    def test_raw_headers_leak_the_credential(self) -> None:
        token = secrets.token_urlsafe(24)
        log, stream = self.capture(with_filter=False)
        crypto.vulnerable_log_request(log, {"Authorization": f"Bearer {token}"})
        self.assertIn(token, stream.getvalue())

    def test_redaction_removes_the_credential(self) -> None:
        token = secrets.token_urlsafe(24)
        log, stream = self.capture(with_filter=True)
        headers = {"Authorization": f"Bearer {token}", "Accept": "text/html"}
        crypto.fixed_log_request(log, headers)
        log.info("retrying with Bearer %s", token)  # free-text slip
        output = stream.getvalue()
        self.assertNotIn(token, output)
        self.assertIn("text/html", output)
        self.assertEqual(output.count("[REDACTED]"), 2)


if __name__ == "__main__":
    unittest.main()
