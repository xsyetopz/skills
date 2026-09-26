"""Mutants: each reintroduces one known Sublime plugin defect.

run_mutants.py runs the offline suites once per entry with VARIANT=<name>
and requires the named test to fail. A mutant that survives means the
suite cannot detect that defect.
"""

import re
import types
from typing import Callable, Dict, NamedTuple

Mutate = Callable[[types.ModuleType, types.ModuleType], None]


class Variant(NamedTuple):
    why: str
    expect: str  # a test that must fail
    mutate: Mutate


def forward_order(core, plugin):
    def plan_edits(regions):
        return sorted({(min(a, b), max(a, b)) for a, b in regions if a != b})

    core.plan_edits = plan_edits


def no_change_count(core, plugin):
    def is_fresh(snapshot, *, valid, change_count, current):
        return valid and current

    core.is_fresh = is_fresh


def no_escape(core, plugin):
    def annotation_html(marker):
        return '<body id="todo-lens"><b>%s</b> %s</body>' % (
            marker.word,
            marker.note,
        )

    core.annotation_html = annotation_html


def close_is_noop(core, plugin):
    core.Generations.close = lambda self: None


def no_clear_on_change(core, plugin):
    def plugin_unloaded():
        state = plugin._state
        if state is not None:
            state.generations.close()
        plugin._state = None

    plugin.plugin_unloaded = plugin_unloaded


def operator_ignored(core, plugin):
    original = core._one

    def one(value, operator, operand):
        if operator == core.NOT_EQUAL:
            operator = core.EQUAL
        return original(value, operator, operand)

    core._one = one


def no_word_boundary(core, plugin):
    def pattern(words):
        alternatives = "|".join(re.escape(w) for w in words)
        return re.compile(r"(%s)" % alternatives)

    core._pattern = pattern


def no_read_only_guard(core, plugin):
    cls = plugin.TodoLensMarkDoneCommand
    cls.is_enabled = lambda self: any(not r.empty() for r in self.view.sel())

    def run(self, edit):
        words = plugin.current_words()
        pairs = [(r.a, r.b) for r in self.view.sel()]
        for begin, end in core.plan_edits(pairs):
            region = plugin.sublime.Region(begin, end)
            old = self.view.substr(region)
            self.view.replace(edit, region, core.mark_done(old, words))

    cls.run = run


def no_debounce(core, plugin):
    def scan(state, view, token):
        if not view.is_valid():
            return
        change_count = view.change_count()
        text = view.substr(plugin.sublime.Region(0, view.size()))
        markers = core.find_markers(text, state.options.words)
        snapshot = core.Snapshot(view.id(), change_count, token)
        plugin.sublime.set_timeout(
            lambda: plugin.publish(state, view, snapshot, markers), 0
        )

    plugin.scan = scan


def unknown_context_false(core, plugin):
    cls = plugin.TodoLensListener
    original = cls.on_query_context

    def on_query_context(self, key, operator, operand, match_all):
        result = original(self, key, operator, operand, match_all)
        return False if result is None else result

    cls.on_query_context = on_query_context


def edit_forward_insert(core, plugin):
    def run(self, edit, word="TODO"):
        if self.view.is_read_only() or word not in plugin.current_words():
            return
        for point in sorted({r.b for r in self.view.sel()}):
            self.view.insert(edit, point, word + ": ")

    plugin.TodoLensInsertCommand.run = run


VARIANTS: Dict[str, Variant] = {
    "forward-order": Variant(
        "Editing the first selection first shifts the later offsets.",
        "test_mark_done_changes_length_in_every_selection",
        forward_order,
    ),
    "no-change-count": Variant(
        "A result computed from old text is drawn over newer text.",
        "test_edit_during_scan_discards_result",
        no_change_count,
    ),
    "no-escape": Variant(
        "Note text becomes live minihtml, including subl: links.",
        "test_annotation_escapes_markup",
        no_escape,
    ),
    "close-is-noop": Variant(
        "A callback queued by the unloaded plugin still publishes.",
        "test_callback_from_unloaded_load_is_ignored",
        close_is_noop,
    ),
    "no-clear-on-change": Variant(
        "Each reload adds another settings callback.",
        "test_reload_keeps_one_settings_callback",
        no_clear_on_change,
    ),
    "operator-ignored": Variant(
        "not_equal behaves as equal, so key bindings fire inverted.",
        "test_operators",
        operator_ignored,
    ),
    "no-word-boundary": Variant(
        "TODOS and XTODO are reported as markers.",
        "test_word_boundaries",
        no_word_boundary,
    ),
    "no-read-only-guard": Variant(
        "A programmatic run_command edits a read-only view.",
        "test_read_only_view_is_not_edited",
        no_read_only_guard,
    ),
    "no-debounce": Variant(
        "Every keystroke schedules its own full-buffer scan.",
        "test_three_modifications_scan_once",
        no_debounce,
    ),
    "unknown-context-false": Variant(
        "Unknown keys must return None per the API; this returns False.",
        "test_unknown_context_key_returns_none",
        unknown_context_false,
    ),
    "forward-insert": Variant(
        "Inserting at the first caret first moves the later carets.",
        "test_insert_at_every_caret",
        edit_forward_insert,
    ),
}
