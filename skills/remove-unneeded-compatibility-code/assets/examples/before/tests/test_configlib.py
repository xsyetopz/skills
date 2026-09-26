import sys
import unittest
from pathlib import Path

# Runnable from the project root (python -m unittest) or directly as a file.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from configlib import load

ROOT = Path(__file__).resolve().parents[1]


class LoadTests(unittest.TestCase):
    def test_current_keys(self) -> None:
        self.assertEqual(load(str(ROOT / "data/current.toml"))["timeout_s"], 10)

    def test_saved_files_with_legacy_key_still_load(self) -> None:
        self.assertEqual(load(str(ROOT / "data/saved-1.2.toml"))["timeout_s"], 30)


if __name__ == "__main__":
    unittest.main()
