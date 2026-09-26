# pyright: reportAttributeAccessIssue=false
"""Host tests: run inside Sublime Text with UnitTesting, never system Python.

unittesting.json sets "pattern": "host_*.py", so UnitTesting discovers this
file while plain test_*.py collectors do not. Run from the console:

    window.run_command("unit_testing", {"package": "TodoLens"})
"""

import sublime
from unittesting import DeferrableTestCase  # pyright: ignore[reportMissingImports]


class MarkDoneHostTest(DeferrableTestCase):
    @classmethod
    def setUpClass(cls):
        cls.window = sublime.active_window()
        # Closing the last test view must not close the window mid-suite.
        cls.anchor = cls.window.new_file()
        cls.anchor.set_scratch(True)

    @classmethod
    def tearDownClass(cls):
        cls.anchor.close()

    def setUp(self):
        self.view = self.window.new_file()
        self.view.set_scratch(True)

    def tearDown(self):
        self.view.set_read_only(False)
        self.view.close()

    def prepare(self, text, regions):
        self.view.run_command("append", {"characters": text})
        self.view.sel().clear()
        for a, b in regions:
            self.view.sel().add(sublime.Region(a, b))

    def text(self):
        return self.view.substr(sublime.Region(0, self.view.size()))

    def test_selections_change_length_and_undo_together(self):
        self.prepare("FIXME a | FIXME b", [(0, 7), (10, 17)])
        self.view.run_command("todo_lens_mark_done")
        self.assertEqual(self.text(), "DONE a | DONE b")
        self.view.run_command("undo")
        self.assertEqual(self.text(), "FIXME a | FIXME b")
        self.view.run_command("redo")
        self.assertEqual(self.text(), "DONE a | DONE b")

    def test_reversed_selection(self):
        self.prepare("x TODO y", [(8, 0)])
        self.view.run_command("todo_lens_mark_done")
        self.assertEqual(self.text(), "x DONE y")

    def test_carets_only_do_not_change_the_buffer(self):
        self.prepare("TODO one", [(0, 0), (8, 8)])
        before = self.view.change_count()
        self.view.run_command("todo_lens_mark_done")
        self.assertEqual(self.view.change_count(), before)

    def test_read_only_view_is_not_edited(self):
        self.prepare("TODO locked", [(0, 11)])
        self.view.set_read_only(True)
        self.view.run_command("todo_lens_mark_done")
        self.assertEqual(self.text(), "TODO locked")

    def test_annotations_appear_after_debounce(self):
        self.prepare("a TODO: b", [(0, 0)])
        view = self.view
        # True-or-None: the README says the runner resumes on "not None"
        # but its own example waits on a bool; this form satisfies both.
        yield lambda: bool(view.get_regions("todo_lens")) or None
        self.assertEqual(view.get_regions("todo_lens"), [sublime.Region(2, 6)])
        self.assertEqual(view.get_status("todo_lens"), "TODO:1")

    def test_rescan_after_edit_replaces_regions(self):
        self.prepare("TODO", [(0, 0)])
        view = self.view
        yield lambda: bool(view.get_regions("todo_lens")) or None
        view.run_command("append", {"characters": "\nFIXME"})
        yield lambda: len(view.get_regions("todo_lens")) == 2 or None
        self.assertEqual(
            view.get_regions("todo_lens"),
            [sublime.Region(0, 4), sublime.Region(5, 10)],
        )
