# Events, threads, and stale results

Cards for listeners, the `_async` handlers, the two timeout queues, and
the checks that keep late results from overwriting newer text. Runnable
code: `assets/examples/TodoLens/plugin.py`, `core.py`; compiled-only
snippets: `assets/examples/snippets/`.

Verification tier: **Executed** for decision logic and call order through
the stub (`offline/test_adapter.py`, `run_mutants.py`), which queues
`set_timeout` and `set_timeout_async` callbacks and runs them only when a
test drains the queue. **Compiled** (3.8.20 and 3.14.7) for the snippets.
**Not runnable here**: real threading, event delivery, and timing; the
stub proves order and arguments, not host scheduling.

## Contents

- ViewEventListener with is_applicable
- EventListener
- Async event handlers
- set_timeout and set_timeout_async
- Debounce with generation tokens
- Change-count freshness guard
- change_id and transform_region_from
- on_query_context

## ViewEventListener with is_applicable

**Definition.** `sublime_plugin.ViewEventListener` is instantiated per
view (`self.view`) and receives view events without a view argument; the
class method `is_applicable(settings)` decides, from the view's
`Settings`, whether an instance is created for a view
([ViewEventListener][vel]). `applies_to_primary_view_only()` limits it to
the primary view of a buffer.

**Use when.**

- Behavior belongs to individual views (decorations, per-view state,
  context keys, hover).
- A per-view setting or syntax decides whether the feature runs.

**Do not use when.**

- The handler needs window or project events (`on_new_window`,
  `on_load_project`): only `EventListener` has them.
- The decision needs the buffer text: `is_applicable` receives only the
  view's `Settings`.

**Example.**

```python
class TodoLensListener(sublime_plugin.ViewEventListener):
    @classmethod
    def is_applicable(cls, settings):
        return settings.get("todo_lens.disable", False) is not True

    def on_modified_async(self):
        schedule_scan(self.view)
```

**Cost removed.** Per-event `if view.settings().get(...)` checks and work
for views that opted out. Metric: `is_applicable` returns `False` after
`view.settings().set("todo_lens.disable", True)`.

**Verify.**

1. `test_is_applicable_honors_view_setting` passes.
1. Host (Not runnable here): in a view, run
   `view.settings().set("todo_lens.disable", True)`, then edit; no new
   annotations appear in that view.

## EventListener

**Definition.** `sublime_plugin.EventListener` is instantiated once and
receives events for every view and window with the object as an argument,
including window and project events such as `on_new_window`,
`on_load_project`, and `on_pre_close_window` (4050+)
([EventListener][el]).

**Use when.**

- One handler must observe all views (save hooks, global counters).
- Window or project lifecycle events are needed.

**Do not use when.**

- Keeping per-view state in dicts keyed by view: a `ViewEventListener`
  has one instance per view that ends with the view.

**Example.**

```python
import time

import sublime_plugin


class SaveStampListener(sublime_plugin.EventListener):
    def on_post_save_async(self, view):
        if not view.is_valid() or view.file_name() is None:
            return
        view.set_status("save_stamp", "saved " + time.strftime("%H:%M:%S"))

    def on_pre_close(self, view):
        view.erase_status("save_stamp")
```

Runnable (compiled only): `assets/examples/snippets/save_stamp.py`.

**Cost removed.** Missed events for views created before or outside a
per-view listener. Metric (host, Not runnable here): every saved file
shows a `saved HH:MM:SS` status.

**Verify.**

1. `sh assets/examples/verify.sh py38` compiles the snippet under 3.8.
1. Host (Not runnable here): copy the snippet into a package, save two
   files in two windows, and read both status bars.

## Async event handlers

**Definition.** Every `on_<event>_async` handler "runs in a separate
thread, and does not block the application"; the non-async form runs on
the main thread and blocks it ([EventListener][el]). All API functions are
thread-safe, but "application state will be changing while the code is
running" ([threading]).

**Use when.**

- The handler does more than constant work (reading the buffer, regex
  scans, file or network I/O).

**Do not use when.**

- The handler must return a value the host uses: `on_text_command`
  (rewrite a command) and `on_query_context` exist only in the
  synchronous form.
- The handler must act "just before a view is saved": use `on_pre_save`;
  whether the save waits for `on_pre_save_async` is not documented.
- Assuming values read in sequence belong together: the buffer can
  change between two calls (see the change-count card).

**Example.**

```python
def on_load_async(self):
    schedule_scan(self.view)

def on_activated_async(self):
    schedule_scan(self.view)

def on_modified_async(self):
    schedule_scan(self.view)
```

**Cost removed.** Typing latency from work on the main thread. Metric
(host, Not runnable here): with a large file, `sublime.log_fps(True)`
shows frame times; compare `on_modified` with `on_modified_async`.
Offline, the stub shows that the worker makes no drawing call: the
`View.add_regions` count is 0 after `run_async()` and 1 after
`run_main()`.

**Verify.**

1. `test_modification_schedules_worker_then_main_thread` passes.
1. `grep -n "def on_.*(self" plugin.py`: only `on_close`, `on_hover`, and
   `on_query_context` are synchronous, and they do constant work.

## set_timeout and set_timeout_async

**Definition.** `sublime.set_timeout(callback, delay=0)` runs the callback
on the main thread after `delay` ms, and "callbacks with an equal delay
will be run in the order they were added";
`sublime.set_timeout_async(callback, delay=0)` runs it on an alternate
thread ([set_timeout][settimeout], [set_timeout_async][settimeoutasync]).

**Use when.**

- `set_timeout_async`: move computation off the main thread or delay it
  (debounce).
- `set_timeout`: return a worker result to the main thread before
  drawing or running a TextCommand.

**Do not use when.**

- Expecting cancellation: neither returns a handle; stale callbacks must
  return early (generation tokens).
- Passing an `Edit` to either: it is dead when the callback runs.

**Example.**

```python
def scan(state, view, token):
    """Worker thread: read a snapshot and compute markers, never edit."""
    if not state.generations.is_current(view.id(), token):
        return
    if not view.is_valid():
        return
    change_count = view.change_count()
    text = view.substr(sublime.Region(0, view.size()))
    markers = core.find_markers(text, state.options.words)
    snapshot = core.Snapshot(view.id(), change_count, token)
    sublime.set_timeout(
        lambda: publish(state, view, snapshot, markers), 0
    )
```

**Cost removed.** Main-thread stalls and drawing from a worker. Metric:
the stub records `set_timeout_async(..., 300)` for the edit, then one
`set_timeout(..., 0)`; `add_regions` runs only in the main queue.

**Verify.**

1. `test_modification_schedules_worker_then_main_thread` asserts delays
   `300` and `0` and the order of calls.
1. Host (Not runnable here): UnitTesting
   `test_annotations_appear_after_debounce` waits on the condition.

## Debounce with generation tokens

**Definition.** Each event takes a new per-view token from
`Generations.next(view_id)` and schedules delayed work that first checks
`is_current(view_id, token)`; only the newest request per view survives,
so a burst of edits costs one scan.

**Use when.**

- Work is triggered by `on_modified*` or `on_selection_modified*`, which
  fire per keystroke.

**Do not use when.**

- The user invokes the action once (a command): there is no burst.
- Waiting with `time.sleep` in a handler: it blocks the handler's
  thread, and the reference does not say how many async threads exist,
  so assume other async work waits too.

**Example.**

```python
def schedule_scan(view):
    state = _state
    if state is None or not state.options.enabled:
        return
    token = state.generations.next(view.id())
    sublime.set_timeout_async(
        lambda: scan(state, view, token), state.options.debounce_ms
    )
```

**Cost removed.** One full-buffer scan per keystroke. Metric: three edits
in a row run 3 async callbacks but schedule 1 publish (`set_timeout`
count 1).

**Verify.**

1. `test_three_modifications_scan_once` passes.
1. `VARIANT=no-debounce` (scan ignores the token) fails it.

## Change-count freshness guard

**Definition.** `View.change_count()` increments on each buffer
modification ([change_count][changecount]). A worker captures it before
reading the text; the main-thread publisher compares it with the current
value, plus `is_valid()` and the generation, and discards the result on
any mismatch (`core.is_fresh`).

**Use when.**

- A result computed from buffer text is drawn or applied later.

**Do not use when.**

- Reading the text before the count: an edit between the two reads
  pairs old text with the new count, so the stale result passes the
  check. Read the count first; then a race can only cause a discard.
- The result can be mapped instead of discarded (insertions at a point):
  see change_id and transform_region_from.

**Example.**

```python
def is_fresh(snapshot, *, valid, change_count, current):
    return valid and current and change_count == snapshot.change_count
```

**Cost removed.** Decorations or edits placed at offsets of older text.
Metric: after `run_async()`, a user edit, and `run_main()`, the stub
view has 0 regions.

**Verify.**

1. `test_edit_during_scan_discards_result` and
   `test_closed_view_is_not_published` pass.
1. `VARIANT=no-change-count` fails `test_edit_during_scan_discards_result`.

## change_id and transform_region_from

**Definition.** `View.change_id()` returns a 3-tuple identifying the
buffer state; `View.transform_region_from(region, change_id)` maps a
region from that state to "an equivalent region in the current state",
meant for "text modification that must operate in an asynchronous
fashion" ([change_id][changeid], [transform_region_from][transform]).

**Use when.**

- A slow result should still apply after unrelated edits elsewhere in
  the buffer (formatters, language-server edits).

**Do not use when.**

- Skipping the text check: the edited span itself may have changed;
  compare its current text with the original and discard on mismatch,
  or the result overwrites typing.
- Discarding and rescanning is acceptable (TodoLens): the change-count
  guard is simpler.

**Example.**

```python
class UpperAsyncApplyCommand(sublime_plugin.TextCommand):
    def run(self, edit, change_id, a, b, original, text):
        region = self.view.transform_region_from(
            sublime.Region(a, b), tuple(change_id)
        )
        if self.view.substr(region) != original:
            return  # the selected text itself changed: stale result
        self.view.replace(edit, region, text)
```

Runnable (compiled only): `assets/examples/snippets/async_replace.py`
(`UpperAsyncCommand` captures `change_id()` and runs this command via
`set_timeout`). The change id travels as a JSON list because command
arguments are JSON values ([CommandArgs][types]).

**Cost removed.** Discarded work when the user edits another part of the
file. Metric (host, Not runnable here): select a word, run
`upper_async`, type elsewhere before it finishes; the word is still
uppercased at its moved position.

**Verify.**

1. `sh assets/examples/verify.sh py38` compiles the snippet.
1. Host (Not runnable here): the manual check above, then `undo`
   restores the word in one step.

## on_query_context

**Definition.** `on_query_context(key, operator, operand, match_all)`
answers key-binding `"context"` entries: return `True` or `False` when
the plugin handles `key`, and `None` when "the context is unknown"
([on_query_context][querycontext]). `operator` is a `QueryOperator`
(`EQUAL`, `NOT_EQUAL`, `REGEX_MATCH`, `NOT_REGEX_MATCH`,
`REGEX_CONTAINS`, `NOT_REGEX_CONTAINS`; module constants `OP_*`), and
`match_all` asks whether every selection must match
([key bindings][keys]).

**Use when.**

- A key binding should apply only in a plugin-defined state (markers
  present, caret on a marker).

**Do not use when.**

- Returning `False` for keys the plugin does not own: the API requires
  `None`.
- Ignoring `operator`: bindings with `"operator": "not_equal"` then fire
  in the opposite state.

**Example.**

```python
def on_query_context(self, key, operator, operand, match_all):
    if key == "todo_lens.has_markers":
        values = [bool(self.view.get_regions(KEY))]
    elif key == "todo_lens.selection_has_marker":
        spans = [(r.a, r.b) for r in self.view.get_regions(KEY)]
        values = [core.touches((s.a, s.b), spans) for s in self.view.sel()]
    else:
        return None
    return core.evaluate_context(values, operator, operand, match_all)
```

`core.evaluate_context` applies the six operators to one value per
selection and combines them with `all` (`match_all`) or `any`.

**Cost removed.** Key bindings that fire in the wrong state or shadow
other packages' contexts. Metric: `NOT_EQUAL` and `match_all` cases in
`test_operators`, `test_match_all`, and
`test_selection_context_match_all`.

**Verify.**

1. `test_unknown_context_key_returns_none` passes;
   `VARIANT=unknown-context-false` and `VARIANT=operator-ignored` are
   killed.
1. Host (Not runnable here): with `sublime.log_commands(True)`, press the
   binding with the caret on and off a marker; the command logs only on.

[vel]: https://www.sublimetext.com/docs/api_reference.html#sublime_plugin.ViewEventListener
[el]: https://www.sublimetext.com/docs/api_reference.html#sublime_plugin.EventListener
[threading]: https://www.sublimetext.com/docs/api_reference.html#threading
[settimeout]: https://www.sublimetext.com/docs/api_reference.html#sublime.set_timeout
[settimeoutasync]: https://www.sublimetext.com/docs/api_reference.html#sublime.set_timeout_async
[changecount]: https://www.sublimetext.com/docs/api_reference.html#sublime.View.change_count
[changeid]: https://www.sublimetext.com/docs/api_reference.html#sublime.View.change_id
[transform]: https://www.sublimetext.com/docs/api_reference.html#sublime.View.transform_region_from
[types]: https://www.sublimetext.com/docs/api_reference.html#types
[querycontext]: https://www.sublimetext.com/docs/api_reference.html#sublime_plugin.ViewEventListener.on_query_context
[keys]: https://www.sublimetext.com/docs/key_bindings.html
