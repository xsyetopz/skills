"""Call-shape tests: TodoLens/plugin.py driven through the host stub.

These prove which sublime API names the plugin calls, with which
arguments, in which order, and what it decides from the values the stub
returns. They do not prove editor behavior; tests/host_commands.py in the
package does that inside Sublime Text with UnitTesting.

Run: python test_adapter.py   (VARIANT=<name> runs against a mutant)
"""

import contextlib
import io
import sys
import unittest

sys.dont_write_bytecode = True  # keep __pycache__ out of the skill tree

from harness import load, reload_plugin, sublime  # noqa: E402


def names(prefix):
    return [args for name, args in sublime.calls if name == prefix]


class AdapterCase(unittest.TestCase):
    def setUp(self):
        self.core, self.plugin = load()
        self.plugin.plugin_loaded()
        self.settings = sublime.load_settings(self.plugin.SETTINGS_FILE)
        self.window = sublime.active_window()
        self.view = self.window.new_file()
        self.listener = self.plugin.TodoLensListener(self.view)

    def tearDown(self):
        self.plugin.plugin_unloaded()

    def type_text(self, text):
        self.view.user_types(text)
        self.listener.on_modified_async()

    def settle(self):
        sublime.run_async()
        sublime.run_main()

    def select(self, *pairs):
        self.view.sel().clear()
        for a, b in pairs:
            self.view.sel().add(sublime.Region(a, b))


class LifecycleTest(AdapterCase):
    def test_reload_keeps_one_settings_callback(self):
        self.assertEqual(self.settings.callback_count(), 1)
        self.plugin.plugin_unloaded()
        self.plugin = reload_plugin(self.core)
        self.plugin.plugin_loaded()
        self.assertEqual(self.settings.callback_count(), 1)

    def test_callback_from_unloaded_load_is_ignored(self):
        self.type_text("TODO a")
        self.plugin.plugin_unloaded()  # scan still queued
        self.plugin = reload_plugin(self.core)
        self.plugin.plugin_loaded()
        self.settle()
        self.assertEqual(names("View.add_regions"), [])

    def test_unload_erases_owned_decorations(self):
        self.type_text("TODO a")
        self.settle()
        self.plugin.plugin_unloaded()
        self.assertEqual(self.view.get_regions("todo_lens"), [])
        self.assertEqual(self.view.get_status("todo_lens"), "")

    def test_is_applicable_honors_view_setting(self):
        cls = self.plugin.TodoLensListener
        self.assertTrue(cls.is_applicable(self.view.settings()))
        self.view.settings().set("todo_lens.disable", True)
        self.assertFalse(cls.is_applicable(self.view.settings()))

    def test_invalid_setting_is_reported_and_defaulted(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.settings.set("display", "popup")
        self.assertIn("TodoLens: display must be one of", out.getvalue())
        self.assertEqual(self.plugin._state.options.display, "annotations")


class AsyncTest(AdapterCase):
    def test_modification_schedules_worker_then_main_thread(self):
        self.type_text("x TODO: y")
        async_calls = names("set_timeout_async")
        self.assertEqual(len(async_calls), 1)
        self.assertEqual(async_calls[0][1], 300)  # debounce_ms default
        sublime.run_async()
        self.assertEqual([a[1] for a in names("set_timeout")], [0])
        self.assertEqual(names("View.add_regions"), [])  # not from worker
        sublime.run_main()
        self.assertEqual(self.view.get_regions("todo_lens"), [sublime.Region(2, 6)])
        self.assertEqual(self.view.get_status("todo_lens"), "TODO:1")

    def test_three_modifications_scan_once(self):
        for text in ("T", "ODO", " a"):
            self.type_text(text)
        self.assertEqual(sublime.run_async(), 3)
        self.assertEqual(len(names("set_timeout")), 1)

    def test_edit_during_scan_discards_result(self):
        self.type_text("TODO a")
        sublime.run_async()  # computed from change_count 1
        self.view.user_types("\nFIXME")  # count 2; no new listener event
        sublime.run_main()
        self.assertEqual(self.view.get_regions("todo_lens"), [])

    def test_closed_view_is_not_published(self):
        self.type_text("TODO a")
        sublime.run_async()
        self.view.close()
        sublime.run_main()
        self.assertEqual(names("View.add_regions"), [])

    def test_phantom_display(self):
        self.settings.set("display", "phantoms")
        self.type_text("TODO a FIXME b")
        self.settle()
        self.assertIn(("todo_lens", 2), names("PhantomSet.update"))
        self.assertEqual(names("View.add_regions")[-1][3], sublime.HIDDEN)

    def test_annotation_escapes_markup(self):
        self.type_text('TODO <a href="subl:exit">x</a>')
        self.settle()
        self.assertNotIn("<a", self.view.annotations[0])


class CommandTest(AdapterCase):
    def test_mark_done_changes_length_in_every_selection(self):
        self.view.user_types("FIXME a | FIXME b")
        self.select((0, 7), (10, 17))
        self.view.run_command("todo_lens_mark_done")
        self.assertEqual(self.view.substr(sublime.Region(0, 99)), "DONE a | DONE b")
        begins = [args[0] for args in names("View.edit")]
        self.assertEqual(begins, [10, 0])  # last region edited first

    def test_carets_only_disable_and_do_not_edit(self):
        self.view.user_types("TODO a")
        self.select((0, 0), (6, 6))
        cmd = self.plugin.TodoLensMarkDoneCommand(self.view)
        self.assertFalse(cmd.is_enabled())
        self.view.run_command("todo_lens_mark_done")
        self.assertEqual(names("View.edit"), [])

    def test_read_only_view_is_not_edited(self):
        self.view.user_types("TODO locked")
        self.select((0, 11))
        self.view.set_read_only(True)
        cmd = self.plugin.TodoLensMarkDoneCommand(self.view)
        self.assertFalse(cmd.is_enabled())
        self.view.run_command("todo_lens_mark_done")
        self.assertEqual(self.view.substr(sublime.Region(0, 99)), "TODO locked")

    def test_edit_token_is_dead_after_run(self):
        kept = []

        class KeepEditCommand(self.plugin.sublime_plugin.TextCommand):
            def run(self, edit):
                kept.append(edit)

        self.view.run_command("keep_edit")
        with self.assertRaises(ValueError):
            self.view.insert(kept[0], 0, "late")

    def test_insert_at_every_caret(self):
        self.view.user_types("ab")
        self.select((0, 0), (1, 1))
        self.view.run_command("todo_lens_insert", {"word": "FIXME"})
        self.assertEqual(self.view.substr(sublime.Region(0, 99)), "FIXME: aFIXME: b")
        self.view.run_command("todo_lens_insert", {"word": "rm -rf"})
        self.view.run_command("todo_lens_insert", {"word": "TODO", "note": "a\nb"})
        self.assertEqual(len(names("View.edit")), 2)

    def test_insert_asks_for_word_only_when_missing(self):
        cmd = self.plugin.TodoLensInsertCommand(self.view)
        handler = cmd.input({})
        self.assertEqual(handler.name(), "word")
        self.assertEqual(handler.list_items(), ["TODO", "FIXME"])
        self.assertIsNone(cmd.input({"word": "TODO"}))
        note = handler.next_input({"word": "TODO"})
        self.assertEqual(note.name(), "note")
        self.assertTrue(note.validate("rename x"))
        self.assertFalse(note.validate("two\nlines"))
        self.assertIsNone(handler.next_input({"word": "TODO", "note": ""}))

    def test_list_command_quick_panel(self):
        self.type_text("TODO a\nFIXME b")
        self.settle()
        self.plugin.TodoLensListCommand(self.window).run()
        items, on_select = self.window.quick_panels[-1]
        self.assertEqual(items, ["TODO: a", "FIXME: b"])
        on_select(-1)
        self.assertEqual(names("View.show_at_center"), [])
        on_select(1)
        self.assertEqual(list(self.view.sel()), [sublime.Region(7, 12)])

    def test_toggle_persists_and_clears(self):
        self.type_text("TODO a")
        self.settle()
        toggle = self.plugin.TodoLensToggleCommand()
        self.assertTrue(toggle.is_checked())
        toggle.run()
        self.assertFalse(toggle.is_checked())
        self.assertEqual(names("save_settings"), [("TodoLens.sublime-settings",)])
        self.assertEqual(self.view.get_regions("todo_lens"), [])


class ContextAndHoverTest(AdapterCase):
    def published(self, text):
        self.type_text(text)
        self.settle()

    def test_has_markers_context(self):
        query = self.listener.on_query_context
        self.assertFalse(query("todo_lens.has_markers", sublime.OP_EQUAL, True, False))
        self.published("TODO")
        self.assertTrue(query("todo_lens.has_markers", sublime.OP_EQUAL, True, False))
        self.assertFalse(
            query("todo_lens.has_markers", sublime.OP_NOT_EQUAL, True, False)
        )

    def test_selection_context_match_all(self):
        self.published("TODO a b")
        self.select((1, 1), (7, 7))
        key = "todo_lens.selection_has_marker"
        query = self.listener.on_query_context
        self.assertTrue(query(key, sublime.OP_EQUAL, True, False))
        self.assertFalse(query(key, sublime.OP_EQUAL, True, True))

    def test_unknown_context_key_returns_none(self):
        self.assertIsNone(
            self.listener.on_query_context("other.key", sublime.OP_EQUAL, True, False)
        )

    def test_hover_shows_escaped_popup_on_text_only(self):
        self.published("TODO <b>x</b>")
        self.listener.on_hover(2, sublime.HOVER_GUTTER)
        self.assertEqual(self.view.popups, [])
        self.listener.on_hover(2, sublime.HOVER_TEXT)
        self.assertIn("&lt;b&gt;x&lt;/b&gt;", self.view.popups[0])
        flags, location, _width = names("View.show_popup")[0]
        self.assertEqual((flags, location), (sublime.HIDE_ON_MOUSE_MOVE_AWAY, 2))


if __name__ == "__main__":
    unittest.main()
