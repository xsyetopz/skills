"""Run with UnitTesting inside Sublime Text, not a mock API or system Python."""

import unittest

try:
    import sublime
except ModuleNotFoundError as error:
    if error.name != "sublime":
        raise
    if __name__ == "__main__":

        @unittest.skip("requires the actual Sublime Text host")
        class UnavailableHost(unittest.TestCase):
            def test_host_commands(self):
                pass

        unittest.main()
    raise unittest.SkipTest("requires the actual Sublime Text host") from error


class JsonStringCommandTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.window = sublime.active_window()
        # Closing the last test view must not close the host window mid-suite.
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
        for start, end in regions:
            self.view.sel().add(sublime.Region(start, end))

    def text(self):
        return self.view.substr(sublime.Region(0, self.view.size()))

    def test_multiple_selections_preserve_offsets_and_undo_together(self):
        self.prepare('a"b | c\\d', [(0, 3), (6, 9)])
        self.view.run_command("example_json_string")
        self.assertEqual(self.text(), '"a\\"b" | "c\\\\d"')
        self.view.run_command("undo")
        self.assertEqual(self.text(), 'a"b | c\\d')
        self.view.run_command("redo")
        self.assertEqual(self.text(), '"a\\"b" | "c\\\\d"')

    def test_reversed_selection_preserves_unicode_and_escapes_newlines(self):
        self.prepare("before café\n雪 after", [(13, 7)])
        self.view.run_command("example_json_string")
        self.assertEqual(self.text(), 'before "café\\n雪" after')

    def test_carets_are_ignored_beside_nonempty_selections(self):
        self.prepare("one two", [(0, 3), (7, 7)])
        self.view.run_command("example_json_string")
        self.assertEqual(self.text(), '"one" two')
        self.assertEqual(self.view.sel()[-1], sublime.Region(9, 9))

    def test_only_carets_do_not_change_the_buffer(self):
        self.prepare("one two", [(0, 0), (7, 7)])
        before = self.view.change_count()
        self.view.run_command("example_json_string")
        self.assertEqual(self.text(), "one two")
        self.assertEqual(self.view.change_count(), before)

    def test_read_only_programmatic_invocation_does_not_edit(self):
        self.prepare("locked", [(0, 6)])
        self.view.set_read_only(True)
        self.view.run_command("example_json_string")
        self.assertEqual(self.text(), "locked")


if __name__ == "__main__":
    unittest.main()
