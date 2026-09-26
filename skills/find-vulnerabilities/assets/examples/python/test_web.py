"""Tests for the pure-function parts of web.py (stdlib only, no sockets).

Run: python3 test_web.py
"""

from __future__ import annotations

import ipaddress
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import web


class PublicIp(unittest.TestCase):
    def test_classification(self) -> None:
        blocked = [
            "127.0.0.1",
            "10.1.2.3",
            "172.16.0.1",
            "192.168.1.1",
            "169.254.169.254",
            "100.64.0.1",
            "::1",
            "fd00::1",
            "fe80::1",
            "::ffff:127.0.0.1",
            "::ffff:169.254.169.254",
        ]
        for text in blocked:
            with self.subTest(text=text):
                self.assertFalse(web.public_ip(ipaddress.ip_address(text)))
        for text in ("8.8.8.8", "2001:4860:4860::8888"):
            with self.subTest(text=text):
                self.assertTrue(web.public_ip(ipaddress.ip_address(text)))


class PolicyCheck(unittest.TestCase):
    """FetchPolicy.check with an injected resolver; nothing is dialed."""

    def policy(self, answers: list[str]) -> web.FetchPolicy:
        return web.FetchPolicy(
            frozenset({"api.example.test"}), resolve=lambda host, port: answers
        )

    def test_rejects_scheme_host_and_any_private_answer(self) -> None:
        good = self.policy(["8.8.8.8"])
        for url in (
            "http://api.example.test/x",
            "file:///etc/hosts",
            "https://evil.example.test/x",
            "https://api.example.test.evil.test/x",
        ):
            with self.subTest(url=url), self.assertRaises(web.BlockedRequest):
                good.check(url)
        mixed = self.policy(["8.8.8.8", "10.0.0.5"])
        with self.assertRaises(web.BlockedRequest):
            mixed.check("https://api.example.test/x")

    def test_returns_checked_address_for_pinning(self) -> None:
        result = self.policy(["8.8.8.8"]).check("https://api.example.test/a?b=1")
        self.assertEqual(
            result, ("https", "api.example.test", "8.8.8.8", 443, "/a?b=1")
        )


class Authorization(unittest.TestCase):
    def setUp(self) -> None:
        self.alice = web.User("alice", tenant="a")
        self.mallory = web.User("mallory", tenant="b")
        self.admin_b = web.User("root", tenant="b", role="admin")
        self.store = {1: web.Invoice("a", 120), 2: web.Invoice("b", 75)}

    def test_other_tenant_reads_invoice_by_id(self) -> None:
        stolen = web.vulnerable_get_invoice(self.store, self.mallory, 1)
        self.assertEqual(stolen.tenant, "a")

    def test_ownership_check_hides_other_tenant(self) -> None:
        with self.assertRaises(web.NotFound):
            web.fixed_get_invoice(self.store, self.mallory, 1)
        with self.assertRaises(web.NotFound):
            web.fixed_get_invoice(self.store, self.mallory, 99)
        self.assertEqual(web.fixed_get_invoice(self.store, self.alice, 1).total, 120)

    def test_member_calls_admin_action(self) -> None:
        users = {"alice": self.alice, "mallory": self.mallory}
        web.vulnerable_delete_user(users, self.mallory, "alice")
        self.assertNotIn("alice", users)

    def test_role_and_tenant_checked_on_admin_action(self) -> None:
        users = {"alice": self.alice, "mallory": self.mallory}
        with self.assertRaises(web.Forbidden):
            web.fixed_delete_user(users, self.mallory, "alice")
        with self.assertRaises(web.Forbidden):
            web.fixed_delete_user(users, self.admin_b, "alice")
        web.fixed_delete_user(users, self.admin_b, "mallory")
        self.assertEqual(set(users), {"alice"})


if __name__ == "__main__":
    unittest.main()
