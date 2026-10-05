import unittest

from csvline import parse_csv_line


class ParseCsvLineTest(unittest.TestCase):
    def test_plain_fields(self):
        self.assertEqual(parse_csv_line("a,b,c"), ["a", "b", "c"])

    def test_quoted_comma(self):
        self.assertEqual(parse_csv_line('"x,y",z'), ["x,y", "z"])


if __name__ == "__main__":
    unittest.main()
