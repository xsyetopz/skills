import unittest

from textkit import pairs, summarize


class TextkitTest(unittest.TestCase):
    def test_summarize(self):
        self.assertEqual(summarize(["b", "A", "a", " ", "c", "B "]), "a:2, b:2, c:1")

    def test_pairs(self):
        self.assertEqual(pairs([1, 2, 3]), [(1, 2), (2, 3)])
