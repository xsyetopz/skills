# Settings, resources, and UI files

Cards for package settings, change callbacks, per-view switches, reading
packaged resources, and the JSON files that expose commands: key maps,
palette entries, and menus. Files: `assets/examples/TodoLens/`.

Verification tier: **Executed** for settings validation, callback
ownership (stub), and the static checks on resource files
(`scripts/check_package.py`: parse with comments and trailing commas,
command references, palette coverage). **Compiled** for
`snippets/show_defaults.py`. **Not runnable here**: settings merging
across files, key dispatch, palette and menu display in the editor.

## Contents

- load_settings with a package settings file
- add_on_change and clear_on_change
- View settings as per-view switches
- load_resource instead of file paths
- Key bindings with a plugin context
- Command Palette entries
- Menu entries with a checkbox

## load_settings with a package settings file

**Definition.** `sublime.load_settings(base_name)` takes a file name with
extension and no path, collates every package's file of that name into
one `Settings` object, and returns the same object on later calls;
`save_settings(base_name)` flushes in-memory changes to disk
([load_settings][loadsettings]). Package order is Default first, User
last, others alphabetical ([packages]), so `Packages/User/<name>`
overrides the package defaults.

**Use when.**

- The package has user-tunable options: ship
  `<Package>.sublime-settings` with every key and its default.

**Do not use when.**

- Calling it at import time on builds before 4171/4180 (see the host
  reference): the object may not be loaded yet.
- Trusting values: users edit the JSON by hand; validate every key and
  fall back to the default with a console message.
- Writing user preferences into `Preferences.sublime-settings` from a
  package.

**Example.**

```json
{
  // Marker words: ASCII letters only, matched as whole words.
  "words": ["TODO", "FIXME"],
  // "annotations", "phantoms", or "none" (status bar only).
  "display": "annotations",
  // Delay in milliseconds before a modified view is rescanned.
  "debounce_ms": 300,
  "enabled": true
}
```

```python
options, problems = core.read_options(settings.get)
for problem in problems:
    print("TodoLens: " + problem)
```

Sublime's JSON decoder allows comments and trailing commas
([decode_value][decode]); `scripts/check_package.py` parses settings and
other resource files the same way.

**Cost removed.** Crashes and silent misbehavior from bad user values.
Metric: `read_options` returns 4 problems and all defaults for the four
invalid values in `test_read_options_defaults_and_problems`.

**Verify.**

1. `test_read_options_defaults_and_problems` and
   `test_invalid_setting_is_reported_and_defaulted` pass.
1. Host (Not runnable here): set `"display": "popup"` in
   `Packages/User/TodoLens.sublime-settings`; the console prints
   `TodoLens: display must be one of annotations, phantoms, none`.

## add_on_change and clear_on_change

**Definition.** `Settings.add_on_change(tag, callback)` registers a
callback "run whenever a setting is changed"; `clear_on_change(tag)`
removes "all callbacks associated with the provided tag"
([add_on_change][onchange]).

**Use when.**

- The plugin caches options that must refresh when the user edits the
  settings file.

**Do not use when.**

- Registering without clearing in `plugin_unloaded`: each reload adds a
  callback, so one change runs N times.
- Using a generic tag such as `"settings"`: another package's
  `clear_on_change("settings")` removes yours. Use the package key.

**Example.**

```python
def plugin_loaded():
    global _state
    settings = sublime.load_settings(SETTINGS_FILE)
    state = LoadState(settings)
    settings.add_on_change(KEY, state.reload_options)
    _state = state
```

`plugin_unloaded` calls `state.settings.clear_on_change(KEY)` first.

**Cost removed.** N-fold callbacks after N reloads. Metric: the stub's
`callback_count()` is 1 after unload, reload, and load.

**Verify.**

1. `test_reload_keeps_one_settings_callback` passes; the
   `no-clear-on-change` mutant is killed (`python run_mutants.py`).
1. Host (Not runnable here): save `plugin.py` three times, then set an
   invalid `display` value once; the console prints one `TodoLens:`
   line, not four.

## View settings as per-view switches

**Definition.** `View.settings()` returns the view's `Settings`; "any
changes to it will be private to this view" ([View.settings][viewsettings]).
Settings are layered: defaults, platform, User preferences, project,
syntax-specific, then buffer-specific ([settings]).

**Use when.**

- A feature needs a per-view or per-syntax switch: read a namespaced key
  (`todo_lens.disable`) that users can also set in syntax-specific or
  project settings.

**Do not use when.**

- Storing package-wide options there: they would differ per view.
- Using a bare key such as `"disable"` that other packages may read.

**Example.**

```python
VIEW_DISABLE = "todo_lens.disable"


class TodoLensListener(sublime_plugin.ViewEventListener):
    @classmethod
    def is_applicable(cls, settings):
        return settings.get(VIEW_DISABLE, False) is not True
```

**Cost removed.** A second settings mechanism for per-view control.
Metric: `is_applicable` flips with one `view.settings().set(...)`.

**Verify.**

1. `test_is_applicable_honors_view_setting` passes.
1. Host (Not runnable here): add `"todo_lens.disable": true` to
   `Packages/User/Markdown.sublime-settings`; Markdown views get no
   annotations.

## load_resource instead of file paths

**Definition.** `sublime.load_resource(name, max_size=16777216)` loads a
resource named like `"Packages/Default/Main.sublime-menu"` from packed or
loose packages; it raises `FileNotFoundError`, `IsADirectoryError`, and
(4213+) `FileTooLargeError`; `load_binary_resource` returns bytes;
`find_resources(pattern)` globs by file name ([load_resource][loadres]).
Packages can run from `.sublime-package` zip files, so files may not
exist on disk ([porting]).

**Use when.**

- Reading any file shipped in the package (templates, HTML, defaults).

**Do not use when.**

- Building paths from `__file__` or `sublime.packages_path()` and calling
  `open()`: it fails for a packed install.
- An external program needs a real path: add `.no-sublime-package` to
  keep the package unpacked ([submitting][submit]) or extract to
  `sublime.cache_path()` and own that copy.
- Loading large resources on the main thread: "loading large resources
  can cause the application to stutter".

**Example.**

```python
RESOURCE = "Packages/TodoLens/TodoLens.sublime-settings"


class TodoLensShowDefaultsCommand(sublime_plugin.WindowCommand):
    def run(self):
        try:
            text = sublime.load_resource(RESOURCE)
        except FileNotFoundError:
            found = sublime.find_resources("TodoLens.sublime-settings")
            sublime.error_message("TodoLens: not found; %s" % found)
            return
        view = self.window.new_file()
        view.set_scratch(True)
        view.run_command("append", {"characters": text})
        view.set_read_only(True)
```

Runnable (compiled only): `assets/examples/snippets/show_defaults.py`.
The `append` command takes `characters` ([commands]).

**Cost removed.** A package that works loose but fails when installed
packed.
Metric (host, Not runnable here): install the built
`TodoLens.sublime-package` with no loose copy and run the command; the
view shows the defaults.

**Verify.**

1. `sh assets/examples/verify.sh py38` compiles the snippet.
1. `sh assets/examples/verify.sh package` builds the archive; the host
   check above uses it.

## Key bindings with a plugin context

**Definition.** A `.sublime-keymap` is a JSON array of objects with
`"keys"`, `"command"`, optional `"args"`, and optional `"context"`; each
context entry has `"key"`, `"operator"` (default `"equal"`), `"operand"`
(default `true`), and for selection keys `"match_all"` (default `false`)
([key bindings][keys]). Unknown keys are answered by plugins through
`on_query_context`.

**Use when.**

- A default binding makes sense only in a state the plugin can detect:
  combine a built-in context key (`selection_empty`) with the plugin key.

**Do not use when.**

- Binding common chords without a context: they compete with other
  bindings in every view. Users add their own in
  `Packages/User/Default.sublime-keymap` ([key bindings][keys]).
- Naming a context key without the package prefix.

**Example.**

```json
[
  {
    "keys": ["ctrl+alt+shift+d"],
    "command": "todo_lens_mark_done",
    "context": [
      { "key": "selection_empty", "operator": "equal", "operand": false },
      {
        "key": "todo_lens.selection_has_marker",
        "operator": "equal",
        "operand": true,
        "match_all": false
      }
    ]
  }
]
```

**Cost removed.** A chord stolen from other packages in unrelated
states. Metric: the binding is active only where the context is true;
offline, `on_query_context` answers `True`/`False` for the key and `None`
for others (tests in the events reference).

**Verify.**

1. `python scripts/check_package.py <pkg>`: the keymap parses and
   `todo_lens_mark_done` resolves.
1. Host (Not runnable here): `sublime.log_input(True)` and
   `sublime.log_commands(True)`; press the chord on and off a marker.

## Command Palette entries

**Definition.** `.sublime-commands` files are JSON arrays of objects with
`"caption"`, `"command"`, and optional `"args"`; the palette filters
entries "by current context" ([palette]). Commands whose `input()`
returns a handler must be listed here ([ListInputHandler][listinput]).

**Use when.**

- Every user-facing command, captioned `Package: Action`.

**Do not use when.**

- Listing internal commands (helpers run from code, like
  `upper_async_apply`): users would run them without their arguments.

**Example.**

```json
[
  { "caption": "TodoLens: Mark Done in Selection",
    "command": "todo_lens_mark_done" },
  { "caption": "TodoLens: Insert Marker", "command": "todo_lens_insert" },
  { "caption": "TodoLens: List Markers", "command": "todo_lens_list" },
  { "caption": "TodoLens: Toggle", "command": "todo_lens_toggle" },
  {
    "caption": "Preferences: TodoLens Settings",
    "command": "edit_settings",
    "args": {
      "base_file": "${packages}/TodoLens/TodoLens.sublime-settings",
      "default": "{\n\t$0\n}\n"
    }
  }
]
```

`edit_settings` with `base_file` and `default` is the built-in used by
the Default package's own "Preferences: Settings" entry ([palette]);
pass it to the checker with `--external edit_settings`.

**Cost removed.** Commands users cannot find, and input handlers that
never show. Metric: checker lines `is not defined` and `input() needs a
.sublime-commands entry`: 0.

**Verify.**

1. `python scripts/check_package.py assets/examples/TodoLens --external
   edit_settings` prints `0 issue(s) in TodoLens`.
1. Host (Not runnable here): open the palette and type `TodoLens:`;
   four entries appear.

## Menu entries with a checkbox

**Definition.** `.sublime-menu` files are JSON arrays of entries with
`"caption"`, `"command"`, `"args"`, `"children"`, `"id"`, `"mnemonic"`,
and `"platform"`; files with the same name from all packages are merged
in package order; seven menus are customizable, including
`Main.sublime-menu` and `Context.sublime-menu` ([menus]). A
`"checkbox": true` entry shows the command's `is_checked()`
([Command][command]).

**Use when.**

- An action belongs in the text context menu or under a main-menu `id`
  defined in `Default/Main.sublime-menu`.

**Do not use when.**

- Guessing a submenu `id`: appending to a submenu needs the parent's
  exact `id`; read it with "View Package File" on
  `Default/Main.sublime-menu`.
- Adding `"checkbox"` for a command without `is_checked`.

**Example.**

```json
[
  { "caption": "TodoLens: Mark Done", "command": "todo_lens_mark_done" },
  {
    "caption": "TodoLens: Enabled",
    "command": "todo_lens_toggle",
    "checkbox": true
  }
]
```

**Cost removed.** Dead or unlabelled menu toggles. Metric: checker
resolves both commands; `test_toggle_persists_and_clears` checks
`is_checked` before and after.

**Verify.**

1. `python scripts/check_package.py <pkg>` reports 0 issues.
1. Host (Not runnable here): right-click in a view; the checkbox mirrors
   the `enabled` setting.

[loadsettings]: https://www.sublimetext.com/docs/api_reference.html#sublime.load_settings
[packages]: https://www.sublimetext.com/docs/packages.html
[decode]: https://www.sublimetext.com/docs/api_reference.html#sublime.decode_value
[onchange]: https://www.sublimetext.com/docs/api_reference.html#sublime.Settings.add_on_change
[viewsettings]: https://www.sublimetext.com/docs/api_reference.html#sublime.View.settings
[settings]: https://www.sublimetext.com/docs/settings.html
[loadres]: https://www.sublimetext.com/docs/api_reference.html#sublime.load_resource
[porting]: https://www.sublimetext.com/docs/porting_guide.html
[submit]: https://packagecontrol.io/docs/submitting_a_package
[commands]: https://docs.sublimetext.io/reference/commands.html
[keys]: https://www.sublimetext.com/docs/key_bindings.html
[palette]: https://docs.sublimetext.io/reference/command_palette.html
[listinput]: https://www.sublimetext.com/docs/api_reference.html#sublime_plugin.ListInputHandler
[menus]: https://www.sublimetext.com/docs/menus.html
[command]: https://www.sublimetext.com/docs/api_reference.html#sublime_plugin.Command
