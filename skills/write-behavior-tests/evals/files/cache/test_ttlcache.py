import time
import unittest

from ttlcache import TTLCache


class TTLCacheTest(unittest.TestCase):
    def test_cache_expiry(self):
        cache = TTLCache(ttl=2)
        cache.set("k", "v")
        self.assertEqual(cache.get("k"), "v")
        time.sleep(2)
        self.assertIsNone(cache.get("k"))


if __name__ == "__main__":
    unittest.main()
