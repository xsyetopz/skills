# Regions, annotations, phantoms, popups, and panels

Cards for drawing plugin results in a view and showing choices, all from
the main thread after a freshness check. Runnable code:
`assets/examples/TodoLens/plugin.py` (`publish`, `on_hover`,
`TodoLensListCommand`) and `core.py` (HTML builders).

Verification tier: **Executed** for arguments and escaping through the
stub and pure tests. **Not runnable here**: how the editor renders
regions, annotations, phantoms, and popups (colors, layout, minihtml
support), which needs Sublime Text.

## Contents

- add_regions with annotations
- PhantomSet
- show_popup from on_hover
- set_status
- show_quick_panel
- Escaping text for minihtml

## add_regions with annotations

**Definition.** `View.add_regions(key, regions, scope='', icon='',
flags=RegionFlags.NONE, annotations=[], annotation_color='',
on_navigate=None, on_close=None)` draws regions for `key`, replacing any
earlier set with that key; regions "should not overlap"; an empty scope
means "the regions won't be drawn"; `annotations` (4050+) are HTML shown
at the right edge, one per region; `get_regions(key)` and
`erase_regions(key)` read and remove them ([add_regions][addregions]).
Pseudo-scopes such as `"region.yellowish"` pick the nearest color from
the user's scheme (3148+). Flag enums exist since 4132; the module
constants (`sublime.DRAW_NO_FILL`, `sublime.HIDDEN`) also work on
earlier builds ([RegionFlags][regionflags]).

**Use when.**

- Marking ranges (findings, markers, diagnostics) that follow edits.
- Keeping ranges for later lookup without drawing: `flags=HIDDEN`.

**Do not use when.**

- Using a shared key (`"errors"`): another plugin's `erase_regions`
  removes yours. Prefix the key with the package name.
- Passing a different number of annotations than regions.
- Calling it from a worker with possibly stale results: publish on the
  main thread after the freshness check.

**Example.**

```python
view.add_regions(
    KEY,
    regions,
    scope="region.yellowish",
    icon="bookmark",
    flags=sublime.DRAW_NO_FILL,
    annotations=[core.annotation_html(m) for m in markers],
    annotation_color="#d7ba7d",
)
```

**Cost removed.** Recomputing marker positions after edits, and
decorations that collide with other packages. Metric:
`view.get_regions("todo_lens")` returns `[Region(2, 6)]` after one
publish for `"x TODO: y"` (stub); `plugin_unloaded` leaves it empty.

**Verify.**

1. `test_modification_schedules_worker_then_main_thread` and
   `test_unload_erases_owned_decorations` pass.
1. Host (Not runnable here): `test_annotations_appear_after_debounce` in
   `tests/host_commands.py`.

## PhantomSet

**Definition.** A `Phantom` is minihtml content "interspersed in a View",
positioned by `PhantomLayout` `INLINE`, `BELOW`, or `BLOCK` (module
constants `LAYOUT_*`); a `PhantomSet(view, key)` owns a group and
`update(phantoms)` moves changed ones, adds new ones, and removes the
rest ([Phantom][phantom], [PhantomSet][phantomset]). The reference lists
the attributes `region`, `content`, `layout`, `on_navigate` and
`to_tuple()` in that order but prints no constructor signature; TodoLens
passes the first three positionally, inferring the order from that list.

**Use when.**

- Content needs its own lines between text (inline results, build
  errors; `Packages/Default/exec.py` shows build errors as phantoms).

**Do not use when.**

- A one-line note at the right edge is enough: annotations take no
  vertical space.
- Creating a new `PhantomSet` on every publish: keep one per view, call
  `update`, and clear it with `update([])`.

**Example.**

```python
phantom_set = state.phantoms.get(view.id())
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
```

**Cost removed.** Phantoms left behind after a display change or unload.
Metric: the stub records `PhantomSet.update("todo_lens", 2)` for two markers
and `update([])` via `clear_view`.

**Verify.**

1. `test_phantom_display` passes.
1. Host (Not runnable here): set `"display": "phantoms"`; each marker
   shows a block under its line; set it back and they disappear.

## show_popup from on_hover

**Definition.** `ViewEventListener.on_hover(point, hover_zone)` reports
the closest text point and a `HoverZone` (`TEXT`, `GUTTER`, `MARGIN`;
module constants `HOVER_*`) ([on_hover][onhover]).
`View.show_popup(content, flags=PopupFlags.NONE, location=-1,
max_width=320, max_height=240, on_navigate=None, on_hide=None)` shows
minihtml at `location` (`-1` is the caret); `HIDE_ON_MOUSE_MOVE_AWAY`
hides it when the mouse moves away unless towards the popup
([show_popup][showpopup]).

**Use when.**

- Showing details for a marked range on demand (hover or a command).

**Do not use when.**

- Showing text details for `GUTTER` or `MARGIN` hovers: `point` is only
  the closest text point; check `hover_zone == HOVER_TEXT`.
- Scanning the buffer inside `on_hover`, which is synchronous: look up
  results already computed.

**Example.**

```python
def on_hover(self, point, hover_zone):
    state = _state
    if state is None or hover_zone != sublime.HOVER_TEXT:
        return
    markers = state.markers.get(self.view.id(), [])
    marker = core.marker_at(markers, point)
    if marker is None:
        return
    self.view.show_popup(
        core.popup_html(marker),
        sublime.HIDE_ON_MOUSE_MOVE_AWAY,
        location=point,
        max_width=480,
    )
```

**Cost removed.** Popups for gutter hovers and main-thread scans on
mouse moves. Metric: no popup for `HOVER_GUTTER`; one popup with escaped
text for `HOVER_TEXT`; the stub records `(8, 2, 480)` as flags,
location, width.

**Verify.**

1. `test_hover_shows_escaped_popup_on_text_only` passes.
1. Host (Not runnable here): hover a marker; the popup shows its note.

## set_status

**Definition.** `View.set_status(key, value)` adds a status-bar entry
shown "in a comma separated list of all status values, ordered by key";
`""` clears it, as does `erase_status(key)` ([set_status][setstatus]).
`sublime.status_message(msg)` shows a transient message instead.

**Use when.**

- A short per-view summary (counts, mode) should stay visible.

**Do not use when.**

- Reporting an event once: use `status_message`.
- Leaving the key after unload: erase it in `plugin_unloaded`.

**Example.**

```python
view.set_status(KEY, core.status_text(markers))  # "FIXME:1 TODO:2"
```

**Cost removed.** Stale status text after unload or disabling. Metric:
`get_status("todo_lens")` is `"TODO:1"` after publish and `""` after
unload (stub).

**Verify.**

1. `test_modification_schedules_worker_then_main_thread` and
   `test_unload_erases_owned_decorations` pass.
1. `test_status_and_quick_panel_text` checks the text format.

## show_quick_panel

**Definition.** `Window.show_quick_panel(items, on_select,
flags=QuickPanelFlags.NONE, selected_index=-1, on_highlight=None,
placeholder=None)` shows a filterable list; `on_select` is called once
with the chosen index or `-1` when cancelled; items may be strings,
lists of strings, or (4083+) `QuickPanelItem`; `placeholder` is 4081+
([show_quick_panel][quickpanel]).

**Use when.**

- Choosing one of several computed items (markers, symbols, files).

**Do not use when.**

- Ignoring `-1`: `markers[-1]` silently picks the last item.
- Using the captured view in the callback without checking
  `is_valid()`: the user can close it while the panel is open.

**Example.** The `run` method of the list command in
`assets/examples/TodoLens/plugin.py` (a `WindowCommand`), dedented:

```python
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
```

**Cost removed.** Jumps to the wrong marker on cancel. Metric: after
`on_select(-1)` the stub records no `show_at_center`; after
`on_select(1)` the selection is `[Region(7, 12)]`.

**Verify.**

1. `test_list_command_quick_panel` passes.
1. Host (Not runnable here): press Escape in the panel; the selection is
   unchanged.

## Escaping text for minihtml

**Definition.** Popups, phantoms, annotations, and HTML sheets render
minihtml; in them `<a href>` supports `http:`, `https:`, and `subl:`
(4073+), where `subl:command_name {"arg": value}` runs a command, and
`on_navigate` callbacks receive every other URL ([minihtml][minihtml]).
[`html.escape(s, quote=True)`][escape] turns `&`, `<`, `>`, `"`, and `'`
into entities, so file text cannot add tags or links.

**Use when.**

- Text from the buffer, file names, settings, or tool output goes into
  popup, phantom, or annotation HTML.

**Do not use when.**

- Escaping twice (`&amp;lt;` shows literally).
- Building `subl:` links from untrusted text: create the URL with
  `sublime.command_url(cmd, args)` (4075+) and escape only the label.

**Example.**

```python
import html


def annotation_html(word, note):
    return '<body id="todo-lens"><b>%s</b> %s</body>' % (
        html.escape(word),
        html.escape(note),
    )


out = annotation_html("TODO", '<a href="subl:exit">x</a>')
assert "<a" not in out and "&lt;a href=&quot;subl:exit&quot;&gt;" in out
```

The `<body id>` follows the minihtml best practice and lets color
schemes style the plugin's HTML.

**Cost removed.** Clickable command links injected by file contents.
Metric: `<a` count in the generated HTML for hostile notes: 0.

**Verify.**

1. `test_annotation_escapes_markup` (core and adapter) and
   `test_popup_escapes_and_fills_empty_note` pass.
1. `VARIANT=no-escape` fails both `test_annotation_escapes_markup` tests.

[addregions]: https://www.sublimetext.com/docs/api_reference.html#sublime.View.add_regions
[regionflags]: https://www.sublimetext.com/docs/api_reference.html#sublime.RegionFlags
[phantom]: https://www.sublimetext.com/docs/api_reference.html#sublime.Phantom
[phantomset]: https://www.sublimetext.com/docs/api_reference.html#sublime.PhantomSet
[onhover]: https://www.sublimetext.com/docs/api_reference.html#sublime_plugin.ViewEventListener.on_hover
[showpopup]: https://www.sublimetext.com/docs/api_reference.html#sublime.View.show_popup
[setstatus]: https://www.sublimetext.com/docs/api_reference.html#sublime.View.set_status
[quickpanel]: https://www.sublimetext.com/docs/api_reference.html#sublime.Window.show_quick_panel
[minihtml]: https://www.sublimetext.com/docs/minihtml.html
[escape]: https://docs.python.org/3/library/html.html#html.escape
