import os
import unittest

from downloads import read_upload

UPLOADS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")


class DownloadTest(unittest.TestCase):
    def test_top_level_file(self):
        self.assertEqual(read_upload(UPLOADS, "report.txt"), b"quarterly numbers\n")

    def test_subdirectory_file(self):
        self.assertEqual(read_upload(UPLOADS, "2026/jan.txt"), b"january\n")


if __name__ == "__main__":
    unittest.main()
