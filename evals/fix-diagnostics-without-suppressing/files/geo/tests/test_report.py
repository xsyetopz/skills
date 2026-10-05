import unittest

from report import line


class ReportTest(unittest.TestCase):
    def test_line(self):
        self.assertEqual(line("North farm", [(100, 200), (50, 40)]), "North farm: 2.20 ha")
