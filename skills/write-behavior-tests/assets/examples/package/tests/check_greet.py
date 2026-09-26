# pyright: reportMissingImports=false
# (`greet` comes from PYTHONPATH=src or the installed wheel)
import unittest

from greet import greet


class GreetTests(unittest.TestCase):
    def test_polish_greeting(self):
        self.assertEqual(greet("Ada", "pl"), "Cześć, Ada!")


if __name__ == "__main__":
    unittest.main()
