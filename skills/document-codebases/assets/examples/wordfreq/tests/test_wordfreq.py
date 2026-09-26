import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from wordfreq import top_words


class TopWordsTests(unittest.TestCase):
    def test_counts_case_insensitively(self):
        self.assertEqual(top_words("The the cat", 1), [("the", 2)])


if __name__ == "__main__":
    unittest.main()
