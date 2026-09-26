import contextlib
import io
import unittest

from csvsum import main


class MainTest(unittest.TestCase):
    def test_sums_column_and_skips_blanks(self) -> None:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            main(["data/sales.csv", "--column", "revenue"])
        self.assertEqual(out.getvalue(), "852.75\n")


if __name__ == "__main__":
    unittest.main()
