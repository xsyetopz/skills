import os
import tempfile
import unittest
from pathlib import Path

from notes import cli, render


class NotesTests(unittest.TestCase):
    def test_add_then_export(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["NOTES_FILE"] = str(Path(tmp, "n.json"))
            cli.main(["add", "<b>hi</b>"])
            out = Path(tmp, "out.html")
            cli.main(["export", str(out)])
            self.assertIn("&lt;b&gt;hi&lt;/b&gt;", out.read_text())

    def test_render_is_pure(self) -> None:
        self.assertEqual(render.to_html([]), "<!doctype html><ul></ul>\n")


if __name__ == "__main__":
    unittest.main()
