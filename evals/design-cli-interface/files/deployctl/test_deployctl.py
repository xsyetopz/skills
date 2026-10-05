"""Existing tests: CI calls the old command names, so they must keep working."""

import subprocess
import sys
import unittest
from pathlib import Path

CLI = [sys.executable, str(Path(__file__).with_name("deployctl.py"))]


class DeployctlTests(unittest.TestCase):
    def test_ls_lists_apps(self):
        out = subprocess.run([*CLI, "ls"], capture_output=True, text=True, check=True)
        self.assertIn("web\teu-west-1", out.stdout)


if __name__ == "__main__":
    unittest.main()
