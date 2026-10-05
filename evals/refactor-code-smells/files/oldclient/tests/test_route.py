import unittest

from api import route


class RouteTest(unittest.TestCase):
    def test_v2(self):
        self.assertEqual(route({"Accept": "application/vnd.acme.v2+json; region=eu"}), {"version": 2, "region": "eu"})
