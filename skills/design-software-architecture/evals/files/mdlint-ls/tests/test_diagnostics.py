import unittest

from server.diagnostics import trailing_whitespace


class TrailingWhitespaceTest(unittest.TestCase):
    def test_ascii_line(self) -> None:
        [diag] = trailing_whitespace("ok\nbad  \n")
        self.assertEqual(diag["range"]["start"], {"line": 1, "character": 3})
        self.assertEqual(diag["range"]["end"], {"line": 1, "character": 5})


if __name__ == "__main__":
    unittest.main()
