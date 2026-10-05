import unittest

from fixture_db import make_db
from search import search


class SearchTest(unittest.TestCase):
    def test_finds_public_titles(self):
        self.assertEqual(search(make_db(), "report"), [(1, "Quarterly report")])

    def test_sort_by_id(self):
        self.assertEqual([r[0] for r in search(make_db(), "o", sort="id")], [1, 2, 5])


if __name__ == "__main__":
    unittest.main()
