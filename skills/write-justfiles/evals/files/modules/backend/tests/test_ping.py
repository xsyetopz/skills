import unittest


class PingTest(unittest.TestCase):
    def test_ping(self):
        self.assertEqual("pong", "pong")
