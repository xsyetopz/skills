import json
import sys
import tempfile
import unittest
from pathlib import Path

# Runs as a module from the repo root or directly as a file.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config_store import StaleWriteError, naive_update, versioned_update


class Base(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "settings.json"
        self.path.write_text(json.dumps({"theme": "dark"}))

    def other_writer(self) -> None:
        data = json.loads(self.path.read_text())
        data["font"] = "mono"  # edit made by another tool
        self.path.write_text(json.dumps(data))


class NaivePlanCounterexamples(Base):
    def test_lost_update(self) -> None:
        naive_update(self.path, {"theme": "light"}, between=self.other_writer)
        self.assertNotIn("font", json.loads(self.path.read_text()))

    def test_unserializable_edit_destroys_file(self) -> None:
        with self.assertRaises(TypeError):
            naive_update(self.path, {"bad": object()})
        self.assertEqual(self.path.read_text(), "")


class CorrectedBehavior(Base):
    def test_stale_write_detected(self) -> None:
        with self.assertRaises(StaleWriteError):
            versioned_update(self.path, {"theme": "light"}, self.other_writer)
        self.assertEqual(json.loads(self.path.read_text())["font"], "mono")

    def test_unserializable_edit_leaves_file(self) -> None:
        original = self.path.read_text()
        with self.assertRaises(TypeError):
            versioned_update(self.path, {"bad": object()})
        self.assertEqual(self.path.read_text(), original)


if __name__ == "__main__":
    unittest.main()
