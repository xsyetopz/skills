"""TodoLens: annotate TODO/FIXME markers, list them, and mark them done.

Every sublime/sublime_plugin call lives in this module; decisions live in
core.py so they can be unit-tested without the editor.
"""

import sublime
import sublime_plugin

from . import core

SETTINGS_FILE = "TodoLens.sublime-settings"
KEY = "todo_lens"  # region key, status key, and on_change tag
VIEW_DISABLE = "todo_lens.disable"  # per-view opt-out, read by is_applicable


class LoadState:
    """Everything one plugin load owns; plugin_unloaded releases it."""

    def __init__(self, settings):
        self.settings = settings
        self.generations = core.Generations()
        self.markers = {}  # view id -> List[core.Marker]
        self.phantoms = {}  # view id -> sublime.PhantomSet
        self.options = core.read_options(settings.get)[0]

    def reload_options(self):
        self.options, problems = core.read_options(self.settings.get)
        for problem in problems:
            print("TodoLens: " + problem)
        for window in sublime.windows():
            for view in window.views():
                if self.options.enabled:
                    schedule_scan(view)
                else:
                    clear_view(self, view)


_state = None


def plugin_loaded():
    global _state
    settings = sublime.load_settings(SETTINGS_FILE)
    state = LoadState(settings)
    settings.add_on_change(KEY, state.reload_options)
    _state = state


def plugin_unloaded():
    global _state
    state = _state
    if state is None:
        return
    state.settings.clear_on_change(KEY)
    state.generations.close()
    for window in sublime.windows():
        for view in window.views():
            clear_view(state, view)
    _state = None


def clear_view(state, view):
    view.erase_regions(KEY)
    view.erase_status(KEY)
    state.markers.pop(view.id(), None)
    phantom_set = state.phantoms.pop(view.id(), None)
    if phantom_set is not None:
        phantom_set.update([])


def schedule_scan(view):
    """Debounce: only the newest request per view survives to scan."""
    state = _state
    if state is None or not state.options.enabled:
        return
    token = state.generations.next(view.id())
    sublime.set_timeout_async(
        lambda: scan(state, view, token), state.options.debounce_ms
    )


def scan(state, view, token):
    """Worker thread: read a snapshot and compute markers, never edit."""
    if not state.generations.is_current(view.id(), token):
        return
    if not view.is_valid():
        return
    # Read the change count before the text: if the buffer changes in
    # between, the snapshot is older than the text and publish discards it.
    change_count = view.change_count()
    text = view.substr(sublime.Region(0, view.size()))
    markers = core.find_markers(text, state.options.words)
    snapshot = core.Snapshot(view.id(), change_count, token)
    sublime.set_timeout(lambda: publish(state, view, snapshot, markers), 0)


def publish(state, view, snapshot, markers):
    """Main thread: draw only if the view is unchanged since the snapshot."""
    fresh = core.is_fresh(
        snapshot,
        valid=view.is_valid(),
        change_count=view.change_count(),
        current=state.generations.is_current(view.id(), snapshot.generation),
    )
    if not fresh:
        return
    state.markers[view.id()] = markers
    regions = [sublime.Region(m.begin, m.end) for m in markers]
    display = state.options.display
    if display == "annotations":
        view.add_regions(
            KEY,
            regions,
            scope="region.yellowish",
            icon="bookmark",
            flags=sublime.DRAW_NO_FILL,
            annotations=[core.annotation_html(m) for m in markers],
            annotation_color="#d7ba7d",
        )
    else:
        view.add_regions(KEY, regions, flags=sublime.HIDDEN)
    phantom_set = state.phantoms.get(view.id())
    if display == "phantoms":
        if phantom_set is None:
            phantom_set = sublime.PhantomSet(view, KEY)
            state.phantoms[view.id()] = phantom_set
        phantom_set.update(
            [
                sublime.Phantom(
                    sublime.Region(m.begin, m.end),
                    core.annotation_html(m),
                    sublime.LAYOUT_BELOW,
                )
                for m in markers
            ]
        )
    elif phantom_set is not None:
        phantom_set.update([])
    view.set_status(KEY, core.status_text(markers))


class TodoLensListener(sublime_plugin.ViewEventListener):
    @classmethod
    def is_applicable(cls, settings):
        return settings.get(VIEW_DISABLE, False) is not True

    def on_load_async(self):
        schedule_scan(self.view)

    def on_activated_async(self):
        schedule_scan(self.view)

    def on_modified_async(self):
        schedule_scan(self.view)

    def on_close(self):
        state = _state
        if state is not None:
            view_id = self.view.id()
            state.generations.forget(view_id)
            state.markers.pop(view_id, None)
            state.phantoms.pop(view_id, None)

    def on_hover(self, point, hover_zone):
        state = _state
        if state is None or hover_zone != sublime.HOVER_TEXT:
            return
        marker = core.marker_at(state.markers.get(self.view.id(), []), point)
        if marker is None:
            return
        self.view.show_popup(
            core.popup_html(marker),
            sublime.HIDE_ON_MOUSE_MOVE_AWAY,
            location=point,
            max_width=480,
        )

    def on_query_context(self, key, operator, operand, match_all):
        if key == "todo_lens.has_markers":
            values = [bool(self.view.get_regions(KEY))]
        elif key == "todo_lens.selection_has_marker":
            spans = [(r.a, r.b) for r in self.view.get_regions(KEY)]
            values = [core.touches((s.a, s.b), spans) for s in self.view.sel()]
        else:
            return None
        return core.evaluate_context(values, operator, operand, match_all)


def current_words():
    state = _state
    return state.options.words if state is not None else core.DEFAULT_WORDS


class TodoLensMarkDoneCommand(sublime_plugin.TextCommand):
    """Replace marker words in every non-empty selection with DONE."""

    def is_enabled(self):
        return not self.view.is_read_only() and any(
            not region.empty() for region in self.view.sel()
        )

    def run(self, edit):
        if self.view.is_read_only():
            return
        words = current_words()
        pairs = [(r.a, r.b) for r in self.view.sel()]
        for begin, end in core.plan_edits(pairs):  # last region first
            region = sublime.Region(begin, end)
            old = self.view.substr(region)
            new = core.mark_done(old, words)
            if new != old:
                self.view.replace(edit, region, new)


class WordInputHandler(sublime_plugin.ListInputHandler):
    def __init__(self, words):
        self.words = words

    def name(self):
        return "word"

    def list_items(self):
        return list(self.words)

    def next_input(self, args):
        if "note" not in args:
            return NoteInputHandler()
        return None


class NoteInputHandler(sublime_plugin.TextInputHandler):
    def name(self):
        return "note"

    def placeholder(self):
        return "note text (optional)"

    def validate(self, text):
        return core.valid_note(text)


class TodoLensInsertCommand(sublime_plugin.TextCommand):
    """Insert "WORD: NOTE" at every caret; the palette asks for both."""

    def input(self, args):
        if "word" not in args:
            return WordInputHandler(current_words())
        return None

    def is_enabled(self):
        return not self.view.is_read_only()

    def run(self, edit, word="TODO", note=""):
        if self.view.is_read_only() or word not in current_words():
            return
        if not core.valid_note(note):
            return
        text = word + ": " + note
        points = sorted({r.b for r in self.view.sel()}, reverse=True)
        for point in points:
            self.view.insert(edit, point, text)


class TodoLensListCommand(sublime_plugin.WindowCommand):
    """Quick panel over the markers of the active view."""

    def is_enabled(self):
        view = self.window.active_view()
        return _state is not None and view is not None

    def run(self):
        state = _state
        view = self.window.active_view()
        if state is None or view is None:
            return
        markers = list(state.markers.get(view.id(), []))
        if not markers:
            sublime.status_message("TodoLens: no markers in this view")
            return

        def on_select(index):
            if index < 0 or not view.is_valid():
                return
            region = sublime.Region(markers[index].begin, markers[index].end)
            view.sel().clear()
            view.sel().add(region)
            view.show_at_center(region)

        self.window.show_quick_panel(core.quick_panel_items(markers), on_select)


class TodoLensToggleCommand(sublime_plugin.ApplicationCommand):
    """Flip the global "enabled" setting; save_settings flushes it to disk."""

    def is_checked(self):
        return sublime.load_settings(SETTINGS_FILE).get("enabled", True) is True

    def run(self):
        settings = sublime.load_settings(SETTINGS_FILE)
        settings.set("enabled", settings.get("enabled", True) is not True)
        sublime.save_settings(SETTINGS_FILE)
