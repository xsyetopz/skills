import unittest

from text_stats import line_count


class LineCountTest(unittest.TestCase):
    def test_counts_lines(self) -> None:
        self.assertEqual(line_count("a\nb\n"), 2)


if __name__ == "__main__":
    unittest.main()
