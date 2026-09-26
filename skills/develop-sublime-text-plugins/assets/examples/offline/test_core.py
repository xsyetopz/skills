"""Pure-logic tests for TodoLens/core.py: stdlib unittest, no editor.

Run: python test_core.py   (VARIANT=<name> runs against a mutant)
"""

import sys
import unittest

sys.dont_write_bytecode = True  # keep __pycache__ out of the skill tree

from harness import load  # noqa: E402

core, _plugin = load()


class FindMarkersTest(unittest.TestCase):
    def test_marker_and_note(self):
        markers = core.find_markers("x = 1  # TODO: rename x\n", ["TODO"])
        self.assertEqual(markers, [core.Marker(9, 13, "TODO", "rename x")])

    def test_word_boundaries(self):
        text = "TODOS XTODO TODO_x TODO"
        found = [m.begin for m in core.find_markers(text, ["TODO"])]
        self.assertEqual(found, [19])

    def test_longest_word_wins_and_empty_words(self):
        text = "FIXMEX FIXME"
        self.assertEqual(
            [m.word for m in core.find_markers(text, ["FIX", "FIXME"])],
            ["FIXME"],
        )
        self.assertEqual(core.find_markers(text, []), [])

    def test_two_markers_on_one_line(self):
        markers = core.find_markers("TODO: a FIXME b\r\nTODO", ["TODO", "FIXME"])
        self.assertEqual(
            [(m.word, m.note) for m in markers],
            [("TODO", "a"), ("FIXME", "b"), ("TODO", "")],
        )

    def test_marker_at_includes_both_ends(self):
        markers = core.find_markers("TODO", ["TODO"])
        self.assertIsNotNone(core.marker_at(markers, 4))
        self.assertIsNone(core.marker_at(markers, 5))


class EditPlanningTest(unittest.TestCase):
    def test_plan_is_last_to_first_normalized_and_non_empty(self):
        plan = core.plan_edits([(0, 3), (9, 6), (4, 4), (6, 9)])
        self.assertEqual(plan, [(6, 9), (0, 3)])

    def test_mark_done_changes_length(self):
        self.assertEqual(
            core.mark_done("FIXME: a TODO b", ["TODO", "FIXME"]),
            "DONE: a DONE b",
        )

    def test_valid_note(self):
        self.assertTrue(core.valid_note(""))
        self.assertTrue(core.valid_note("x" * core.MAX_NOTE))
        self.assertFalse(core.valid_note("x" * (core.MAX_NOTE + 1)))
        self.assertFalse(core.valid_note("a\rb"))

    def test_touches(self):
        spans = [(4, 8)]
        self.assertTrue(core.touches((6, 6), spans))
        self.assertTrue(core.touches((0, 5), spans))
        self.assertFalse(core.touches((0, 4), spans))
        self.assertFalse(core.touches((9, 9), spans))


class FreshnessTest(unittest.TestCase):
    def test_is_fresh_needs_valid_current_and_same_count(self):
        snap = core.Snapshot(view_id=1, change_count=7, generation=2)
        ok = {"valid": True, "change_count": 7, "current": True}
        self.assertTrue(core.is_fresh(snap, **ok))
        for key, bad in (("valid", False), ("change_count", 8), ("current", False)):
            with self.subTest(key=key):
                self.assertFalse(core.is_fresh(snap, **dict(ok, **{key: bad})))

    def test_generations(self):
        gens = core.Generations()
        first = gens.next(1)
        second = gens.next(1)
        self.assertFalse(gens.is_current(1, first))
        self.assertTrue(gens.is_current(1, second))
        gens.forget(1)
        self.assertFalse(gens.is_current(1, second))
        third = gens.next(1)
        gens.close()
        self.assertFalse(gens.is_current(1, third))
        self.assertFalse(gens.is_current(1, gens.next(1)))


class ContextTest(unittest.TestCase):
    def test_operators(self):
        cases = [
            (core.EQUAL, True, [True], True),
            (core.NOT_EQUAL, True, [True], False),
            (core.NOT_EQUAL, False, [True], True),
            (core.REGEX_MATCH, "TO.O", ["TODO"], True),
            (core.NOT_REGEX_MATCH, "TO", ["TODO"], True),
            (core.REGEX_CONTAINS, "DO", ["TODO"], True),
            (core.NOT_REGEX_CONTAINS, "DO", ["TODO"], False),
        ]
        for operator, operand, values, expected in cases:
            with self.subTest(operator=operator, operand=operand):
                self.assertIs(
                    core.evaluate_context(values, operator, operand, False),
                    expected,
                )

    def test_match_all(self):
        values = [True, False]
        self.assertTrue(core.evaluate_context(values, core.EQUAL, True, False))
        self.assertFalse(core.evaluate_context(values, core.EQUAL, True, True))

    def test_unhandled_operator_or_operand_is_none(self):
        self.assertIsNone(core.evaluate_context([True], 99, True, False))
        self.assertIsNone(core.evaluate_context(["x"], core.REGEX_MATCH, 1, False))
        self.assertIsNone(core.evaluate_context([], core.EQUAL, True, False))


class HtmlAndOptionsTest(unittest.TestCase):
    def test_annotation_escapes_markup(self):
        marker = core.Marker(0, 4, "TODO", '<a href="subl:exit">x</a> & y')
        html = core.annotation_html(marker)
        self.assertNotIn("<a", html)
        self.assertIn("&lt;a href=&quot;subl:exit&quot;&gt;", html)
        self.assertIn("&amp; y", html)

    def test_popup_escapes_and_fills_empty_note(self):
        self.assertIn("&lt;b&gt;", core.popup_html(core.Marker(0, 1, "T", "<b>")))
        self.assertIn("(no note)", core.popup_html(core.Marker(0, 1, "T", "")))

    def test_read_options_defaults_and_problems(self):
        good = {"enabled": False, "words": ["NOTE"], "display": "phantoms"}
        options, problems = core.read_options(good.get)
        self.assertEqual(options, core.Options(False, ("NOTE",), "phantoms", 300))
        self.assertEqual(problems, [])
        bad = {
            "enabled": "yes",
            "words": ["TO DO"],
            "display": "popup",
            "debounce_ms": True,
        }
        options, problems = core.read_options(bad.get)
        self.assertEqual(
            options, core.Options(True, core.DEFAULT_WORDS, "annotations", 300)
        )
        self.assertEqual(len(problems), 4)

    def test_status_and_quick_panel_text(self):
        markers = core.find_markers("TODO a\nFIXME\nTODO", ["TODO", "FIXME"])
        self.assertEqual(core.status_text(markers), "FIXME:1 TODO:2")
        self.assertEqual(core.status_text([]), "")
        self.assertEqual(core.quick_panel_items(markers)[1], "FIXME: (no note)")


if __name__ == "__main__":
    unittest.main()
