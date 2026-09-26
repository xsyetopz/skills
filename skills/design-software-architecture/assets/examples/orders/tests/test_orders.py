"""Contract tests run against every OrderStore adapter, plus HTTP tests."""

import json
import sys
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from orders.adapters.http import serve
from orders.adapters.memory import MemoryStore
from orders.adapters.sqlite import SqliteStore
from orders.domain import OrderError, new_order
from orders.service import place_order

ADAPTERS = {"memory": MemoryStore, "sqlite": SqliteStore}


class StoreContract(unittest.TestCase):
    """The same assertions for each adapter: the port's contract."""

    def test_add_then_get(self):
        for name, factory in ADAPTERS.items():
            with self.subTest(adapter=name):
                store = factory()
                self.addCleanup(getattr(store, "close", lambda: None))
                order = new_order("o1", "ada", {"pen": 2})
                store.add(order, "k1")
                self.assertEqual(store.get("o1"), order)
                self.assertEqual(store.get_by_key("k1"), order)

    def test_same_key_returns_first_order(self):
        for name, factory in ADAPTERS.items():
            with self.subTest(adapter=name):
                store = factory()
                self.addCleanup(getattr(store, "close", lambda: None))
                first = store.add(new_order("o1", "ada", {"pen": 2}), "k1")
                second = store.add(new_order("o2", "ada", {"pen": 2}), "k1")
                self.assertEqual(second, first)
                self.assertIsNone(store.get("o2"))

    def test_missing_order_is_none(self):
        for name, factory in ADAPTERS.items():
            with self.subTest(adapter=name):
                store = factory()
                self.addCleanup(getattr(store, "close", lambda: None))
                self.assertIsNone(store.get("nope"))


class ServiceTests(unittest.TestCase):
    def test_retry_with_same_key_creates_one_order(self):
        store = MemoryStore()
        first = place_order(store, "ada", {"pen": 1}, "retry-1")
        again = place_order(store, "ada", {"pen": 1}, "retry-1")
        self.assertEqual(first.order_id, again.order_id)

    def test_without_identity_a_retry_duplicates(self):
        # What the key prevents: a new key per attempt makes two orders.
        store = MemoryStore()
        a = place_order(store, "ada", {"pen": 1}, "attempt-1")
        b = place_order(store, "ada", {"pen": 1}, "attempt-2")
        self.assertNotEqual(a.order_id, b.order_id)

    def test_domain_rules(self):
        with self.assertRaises(OrderError):
            new_order("o", "", {"pen": 1})
        with self.assertRaises(OrderError):
            new_order("o", "ada", {"pen": 0})


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.store = SqliteStore()
        self.server = serve(self.store)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.store.close()

    def request(self, method, path, body=None, key=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method)
        if key:
            req.add_header("Idempotency-Key", key)
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status, resp.headers["Content-Type"], json.load(resp)
        except urllib.error.HTTPError as error:
            with error:
                return error.code, error.headers["Content-Type"], json.load(error)

    def test_create_retry_and_read(self):
        body = {"customer": "ada", "items": {"pen": 2}}
        status, _, created = self.request("POST", "/orders", body, key="k-9")
        self.assertEqual(status, 201)
        _, _, retried = self.request("POST", "/orders", body, key="k-9")
        self.assertEqual(retried["order_id"], created["order_id"])
        status, _, read = self.request("GET", f"/orders/{created['order_id']}")
        self.assertEqual((status, read["quantity"]), (200, 2))

    def test_errors_are_problem_details(self):
        status, kind, problem = self.request("POST", "/orders", {"customer": "a"})
        self.assertEqual((status, kind), (400, "application/problem+json"))
        self.assertEqual(problem["status"], 400)
        status, _, problem = self.request(
            "POST", "/orders", {"customer": "", "items": {"pen": 1}}, key="k"
        )
        self.assertEqual((status, problem["detail"]), (422, "customer is required"))
        status, _, _ = self.request("GET", "/orders/missing")
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
