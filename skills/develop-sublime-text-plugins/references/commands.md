# Commands and edits

Cards for the three command kinds, the `Edit` token, multi-selection
edits, command availability, command names, and Command Palette input
handlers. Runnable code: `assets/examples/TodoLens/plugin.py`; stub
tests: `assets/examples/offline/test_adapter.py`.

Verification tier: **Executed** for the pure logic and for call shapes
against the documented stub of `sublime`/`sublime_plugin`, which proves
the API names and arguments the plugin uses, not what the editor does.
**Not runnable here**: undo grouping, palette visibility, and key
dispatch in Sublime Text; `TodoLens/tests/host_commands.py` covers them
with UnitTesting.

## Contents

- TextCommand and the Edit token
- Last-to-first multi-selection edits
- WindowCommand
- ApplicationCommand
- is_enabled, is_visible, and is_checked
- Command names from class names
- ListInputHandler
- TextInputHandler with next_input

## TextCommand and the Edit token

**Definition.** `sublime_plugin.TextCommand` is instantiated once per
view (`self.view`); the host calls `run(edit, **args)` with a
`sublime.Edit`, "a grouping of buffer modifications" that user code
cannot create. "Using an invalid Edit object, or an Edit object from a
different View, will cause the functions that require them to fail"
([Edit][edit]). `View.insert`, `erase`, and `replace` require it. Since
Sublime Text 3 the only way to get a valid Edit is to put the edits in a
TextCommand and invoke it with `run_command()` ([porting]).

**Use when.**

- Any change to buffer text.
- Deferred work (timers, workers) ends with text to insert: call
  `view.run_command("name", {json args})` for a fresh Edit.

**Do not use when.**

- Storing `edit` on `self` or in a closure, or passing it to
  `set_timeout`: the token is invalid once `run` returns.
- Moving the selection or adding regions: `view.sel()` and `add_regions`
  do not need an Edit.

**Example.**

```python
class TodoLensMarkDoneCommand(sublime_plugin.TextCommand):
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
```

Runnable: `assets/examples/TodoLens/plugin.py`. The stub models the
documented failure: `test_edit_token_is_dead_after_run` keeps an Edit
from one `run`, uses it later, and gets `ValueError`.

**Cost removed.** Undo steps and repeat/macro breakage from edits outside
a command ([porting]). Metric (host, Not runnable here): one `undo` after
`todo_lens_mark_done` restores the whole multi-selection change
(`test_selections_change_length_and_undo_together`).

**Verify.**

1. Offline: `python test_adapter.py` passes
   `test_edit_token_is_dead_after_run`.
1. `grep -n "edit" plugin.py` shows `edit` used only inside `run`.
1. Host (Not runnable here): run `TodoLens/tests/host_commands.py` with
   UnitTesting; the undo test passes.

## Last-to-first multi-selection edits

**Definition.** `view.sel()` is a `Selection` that "maintains a set of
sorted non-overlapping Regions"; each Region has `a` and `b` where `b`
(the caret) may be before `a` ([Selection][selection], [Region][region]).
A replacement shifts the offsets of every later region, so apply
length-changing edits from the last region to the first.

**Use when.**

- A command edits several selections or carets and changes the text
  length.

**Do not use when.**

- Adding an overlap-merging pass for `view.sel()`: the host already keeps
  it non-overlapping. Regions from other sources (search results, your
  own lists) need their own overlap rule.
- Using `a`/`b` as start/end: reversed selections have `a > b`; use
  `begin()`/`end()` or `min`/`max`.

**Example.**

```python
from typing import Iterable, List, Tuple


def plan_edits(regions: Iterable[Tuple[int, int]]) -> List[Tuple[int, int]]:
    spans = {(min(a, b), max(a, b)) for a, b in regions if a != b}
    return sorted(spans, reverse=True)


assert plan_edits([(0, 3), (9, 6), (4, 4)]) == [(6, 9), (0, 3)]
```

Runnable: `core.plan_edits` in `assets/examples/TodoLens/core.py`;
`TodoLensInsertCommand` applies the same rule to caret points.

**Cost removed.** Corrupted text in the second and later selections.
Metric: the stub records edit offsets; for `"FIXME a | FIXME b"` with two
selections the order is `[10, 0]` and the result `"DONE a | DONE b"`.

**Verify.**

1. `test_mark_done_changes_length_in_every_selection` and
   `test_insert_at_every_caret` pass.
1. `VARIANT=forward-order` and `VARIANT=forward-insert` each fail their
   test (`python run_mutants.py` prints `killed forward-order ...`).

## WindowCommand

**Definition.** `sublime_plugin.WindowCommand` is "instantiated once per
window"; `self.window` is its `Window`, and `run(**kwargs)` receives no
Edit ([WindowCommand][windowcommand]). `Window.run_command` dispatches
"via input focus" and can run any kind of command ([Window][window]).

**Use when.**

- The action concerns the window: panels, quick panels, opening files,
  layouts, or choosing among views.

**Do not use when.**

- The command edits text: a WindowCommand has no Edit; run a
  TextCommand on the target view instead.
- Assuming `active_view()` is non-`None`: it returns `View | None`.

**Example.**

```python
class TodoLensListCommand(sublime_plugin.WindowCommand):
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
            m = markers[index]
            view.sel().clear()
            view.sel().add(sublime.Region(m.begin, m.end))
            view.show_at_center(sublime.Region(m.begin, m.end))

        self.window.show_quick_panel(
            core.quick_panel_items(markers), on_select
        )
```

Runnable: `assets/examples/TodoLens/plugin.py` (same logic, one local
`region` variable).

**Cost removed.** `AttributeError` on `None` when no view is focused, and
edits attempted without a token. Metric: `test_list_command_quick_panel`
checks items, the `-1` cancel path, and the selection set on choice.

**Verify.**

1. `python test_adapter.py` passes `test_list_command_quick_panel`.
1. Host (Not runnable here): run "TodoLens: List Markers" from the
   palette with an empty window; the status bar shows the message.

## ApplicationCommand

**Definition.** `sublime_plugin.ApplicationCommand` is "a Command
instantiated just once" and is run with `sublime.run_command(cmd, args)`
([ApplicationCommand][appcommand], [run_command][runcommand]).

**Use when.**

- The action is not tied to a window or view: toggling a package
  setting, opening a global resource.

**Do not use when.**

- The action needs the current view or window: a TextCommand or
  WindowCommand receives it.

**Example.**

```python
class TodoLensToggleCommand(sublime_plugin.ApplicationCommand):
    def is_checked(self):
        settings = sublime.load_settings(SETTINGS_FILE)
        return settings.get("enabled", True) is True

    def run(self):
        settings = sublime.load_settings(SETTINGS_FILE)
        settings.set("enabled", settings.get("enabled", True) is not True)
        sublime.save_settings(SETTINGS_FILE)
```

**Cost removed.** Per-window copies of global state. Metric:
`test_toggle_persists_and_clears` sees one `save_settings` call with
`"TodoLens.sublime-settings"` and the regions cleared by the change
callback.

**Verify.**

1. `python test_adapter.py` passes `test_toggle_persists_and_clears`.
1. Host (Not runnable here): run `sublime.run_command("todo_lens_toggle")`
   in the console; the context-menu checkbox "TodoLens: Enabled" flips
   and annotations disappear.

## is_enabled, is_visible, and is_checked

**Definition.** `Command.is_enabled()` returns "whether the command is
able to be run at this time"; `is_visible()` whether it "should be shown
in the menu"; `is_checked()` whether a checkbox is shown, which requires
`"checkbox": true` in the `.sublime-menu` entry. Each receives the
command arguments as keyword arguments ([Command][command]).

**Use when.**

- The command cannot act in some states (read-only view, only carets, no
  markers): return `False` from `is_enabled`.
- A menu entry shows a toggle state: `is_checked` plus `"checkbox"`.

**Do not use when.**

- Relying on `is_enabled` alone: the documentation describes
  availability and does not promise that `run_command` skips a disabled
  command. Keep the guard in `run` too.
- Doing slow work in these methods: menus and the palette call them
  while rendering entries.

**Example.**

```python
def is_enabled(self):
    return not self.view.is_read_only() and any(
        not region.empty() for region in self.view.sel()
    )
```

**Cost removed.** Programmatic runs that edit read-only views, and menu
entries that do nothing. Metric: with a read-only view, `is_enabled()` is
`False` and the text is unchanged after `run_command`.

**Verify.**

1. `test_read_only_view_is_not_edited` and
   `test_carets_only_disable_and_do_not_edit` pass.
1. `VARIANT=no-read-only-guard` fails `test_read_only_view_is_not_edited`.

## Command names from class names

**Definition.** Sublime Text derives the command name from the class
name "by stripping the Command suffix, splitting subwords of
PhrasesLikeThis with underscores, and lower-casing it"
([community docs][naming]); `Command.name()` returns it
([Command][command]). Build 4213 notes: "Fixed command names not being
snake_cased correctly" ([notes]), so names with consecutive capitals
(`ShowHTMLCommand`) can differ between builds.

**Use when.**

- Writing any `"command"` value in `.sublime-commands`, `.sublime-keymap`,
  `.sublime-menu`, `run_command`, or a `subl:` link.

**Do not use when.**

- Naming classes with acronyms in capitals: use `ShowHtmlCommand`
  (`show_html`) so every build agrees.
- Guessing a built-in command name: look it up in the Default package
  or with `sublime.log_commands(True)` in the console.

**Example.**

```python
import re


def command_name(class_name: str) -> str:
    if class_name.endswith("Command"):
        class_name = class_name[: -len("Command")]
    return re.sub(r"(?<!^)(?=[A-Z])", "_", class_name).lower()


assert command_name("TodoLensMarkDoneCommand") == "todo_lens_mark_done"
assert command_name("ShowHTMLCommand") == "show_h_t_m_l"
```

Runnable: `scripts/check_package.py` (`command_name`).

**Cost removed.** Menu, palette, and key entries whose command name does
not resolve. Metric: checker lines `command '<name>' is not
defined` and `has consecutive capitals`; 0 for TodoLens.

**Verify.**

1. `python scripts/test_check_package.py`: the fixture reports both
   `ShowHTMLCommand has consecutive capitals` and `command 'show_html'
   is not defined`.
1. Host (Not runnable here): `sublime.log_commands(True)`, run the
   entry, and read the logged name.

## ListInputHandler

**Definition.** `Command.input(args)` may return a
`sublime_plugin.ListInputHandler`; the Command Palette then asks the user
to pick from `list_items()` before `run` receives the choice under the
argument name `name()`. The command "MUST be made available in the
Command Palette by adding the command to a Default.sublime-commands
file" ([ListInputHandler][listinput], [input][commandinput]).

**Use when.**

- A command run from the palette takes an argument from a small closed
  set.

**Do not use when.**

- The command is only bound to keys or menus, where the handler is not
  shown: pass `args` in the binding.
- The argument is already present: `input` receives the known `args`;
  return `None`.

**Example.**

```python
class WordInputHandler(sublime_plugin.ListInputHandler):
    def __init__(self, words):
        self.words = words

    def name(self):
        return "word"

    def list_items(self):
        return list(self.words)


class TodoLensInsertCommand(sublime_plugin.TextCommand):
    def input(self, args):
        if "word" not in args:
            return WordInputHandler(current_words())
        return None
```

**Cost removed.** Commands that never prompt because the palette file
does not list them. Metric: checker line `input() needs a
.sublime-commands entry`; 0 for TodoLens.

**Verify.**

1. `test_insert_asks_for_word_only_when_missing` passes.
1. `python scripts/test_check_package.py` reports `PickCommand: input()
   needs a .sublime-commands entry` for the fixture.

## TextInputHandler with next_input

**Definition.** `sublime_plugin.TextInputHandler` accepts free text in
the palette; `placeholder()` shows hint text, `validate(text)` returning
`False` disallows the value on Enter, and a handler's
`next_input(args)` returns the next handler or `None`
([CommandInputHandler][inputhandler]).

**Use when.**

- A palette command needs a free-text argument after another choice.

**Do not use when.**

- Validating the value only in the UI: key bindings and `run_command`
  call `run` with arguments directly, so validate there too.

**Example.**

```python
class NoteInputHandler(sublime_plugin.TextInputHandler):
    def name(self):
        return "note"

    def placeholder(self):
        return "note text (optional)"

    def validate(self, text):
        return core.valid_note(text)  # one line, <= 200 characters
```

`WordInputHandler.next_input` returns `NoteInputHandler()` while `"note"`
is missing; `run(edit, word="TODO", note="")` checks `valid_note` again.

**Cost removed.** Multi-line or oversized notes reaching the buffer
through any entry point. Metric: `run_command("todo_lens_insert", {"word":
"TODO", "note": "a\nb"})` produces no edit in the stub.

**Verify.**

1. `test_insert_asks_for_word_only_when_missing` checks `name()`,
   `validate`, and `next_input`; `test_insert_at_every_caret` checks the
   rejected note.
1. Host (Not runnable here): run "TodoLens: Insert Marker", pick a word,
   type a note, press Enter.

[edit]: https://www.sublimetext.com/docs/api_reference.html#sublime.Edit
[porting]: https://www.sublimetext.com/docs/porting_guide.html
[selection]: https://www.sublimetext.com/docs/api_reference.html#sublime.Selection
[region]: https://www.sublimetext.com/docs/api_reference.html#sublime.Region
[window]: https://www.sublimetext.com/docs/api_reference.html#sublime.Window
[windowcommand]: https://www.sublimetext.com/docs/api_reference.html#sublime_plugin.WindowCommand
[appcommand]: https://www.sublimetext.com/docs/api_reference.html#sublime_plugin.ApplicationCommand
[runcommand]: https://www.sublimetext.com/docs/api_reference.html#sublime.run_command
[command]: https://www.sublimetext.com/docs/api_reference.html#sublime_plugin.Command
[naming]: https://docs.sublimetext.io/guide/extensibility/plugins/
[notes]: https://www.sublimetext.com/download
[listinput]: https://www.sublimetext.com/docs/api_reference.html#sublime_plugin.ListInputHandler
[commandinput]: https://www.sublimetext.com/docs/api_reference.html#sublime_plugin.Command.input
[inputhandler]: https://www.sublimetext.com/docs/api_reference.html#sublime_plugin.CommandInputHandler
