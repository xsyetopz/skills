import unittest

from app.settings import load


class LoadTest(unittest.TestCase):
    def test_sections_and_keys(self) -> None:
        text = "[db]\nhost = localhost\nport = 5432\n"
        self.assertEqual(load(text), {"db": {"host": "localhost", "port": "5432"}})


if __name__ == "__main__":
    unittest.main()
