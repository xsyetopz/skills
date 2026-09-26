# Plugin host and lifecycle

Cards for choosing the Python plugin host, keeping code compatible with
it, and owning everything a plugin load creates. The runnable package is
[`assets/examples/TodoLens/`](../assets/examples/TodoLens/); offline
suites are in [`assets/examples/offline/`](../assets/examples/offline/).

Verification tier: **Executed** for the pure core, the host-stub call
shapes, the mutants, and Python 3.8 compilation (`sh
assets/examples/verify.sh`, macOS 27.0 arm64, CPython 3.14.7 and uv
0.12.15 fetching CPython 3.8.20). **Not runnable here** for behavior
inside Sublime Text: no editor is installed on this machine.

## Contents

- Plugin host selection with .python-version
- Python 3.8 compatibility check
- plugin_loaded and plugin_unloaded
- API calls at import time
- Load state owned by one plugin load
- Pure core and host adapter split

## Plugin host selection with .python-version

**Definition.** A file named `.python-version` in the package root selects
the embedded Python that runs every plugin of that package in the
separate `plugin_host` process ([API environments][env]). Builds 4050 to
4204 accept `3.3` or `3.8`; any other value or no file means 3.3, except
in the `User` package. From build 4205 the newer host is Python 3.14, and
`3.8` still selects it for backwards compatibility. Build 4213 (stable, 21
Sep 2026) ships 3.14 and 3.3 with 3.3 disabled by default; the setting
`"disable_plugin_host_3.3": false` re-enables it ([release notes][notes]).

**Use when.**

- The package has any `.py` file at its root (every one is a plugin).
- The code uses syntax or stdlib newer than 3.3 (f-strings, `typing`,
  variable annotations, `NamedTuple` class syntax).

**Do not use when.**

- Writing `3.14` for a package that must also load on builds before 4205:
  those builds fall back to 3.3 for unknown values.
- Expecting `3.8` to pin an interpreter: on 4205+ it runs under 3.14, so
  code must also work on 3.14 (for example no removed stdlib modules).
- Relying on the file in older builds: a `3.8` marker loaded by a build
  before 4050 runs the plugins under 3.3 ([env]).

Source conflict: the API environments page says the 3.3 host "can be
fully disabled using the setting `"disable_plugin_host_3.3": false`",
while the 4213 notes say `false` re-enables it and build 4200 notes say
the setting "causes all plugins to run under 3.8". Treat `true` as
"disabled" (the release notes) and test both values.

**Example.**

```text
TodoLens/.python-version
3.8
```

**Cost removed.** Plugins silently running on the wrong interpreter.
Metric (host, Not runnable here): `import sys; sys.version` in the
plugin host prints the selected version. Offline,
`scripts/check_package.py` reports `.python-version: missing` or an
unknown value; TodoLens has 0 such lines.

**Verify.**

1. `python scripts/check_package.py assets/examples/TodoLens --external
   edit_settings` prints `0 issue(s) in TodoLens`.
1. Remove the file in a copy and rerun: the checker prints
   `.python-version: missing; the host then differs by build`.
1. Host (Not runnable here): add `print(sys.version)` to
   `plugin_loaded`, restart, and read the console line.

## Python 3.8 compatibility check

**Definition.** `python -m py_compile` under CPython 3.8 rejects syntax
that 3.8 cannot parse; running the test suites under 3.8 also catches
newer runtime APIs and runtime-evaluated annotations, which `py_compile`
accepts. `uv run --python 3.8 --no-project python` fetches
and runs CPython 3.8 without a project.

**Use when.**

- `.python-version` says `3.8` and builds 4050 to 4204 are supported.
- Any code change in the package, before claiming compatibility.

**Do not use when.**

- Treating a clean `py_compile` as proof: it passed for
  `str.removeprefix` (3.9+) and `list[int]` annotations, which then
  failed at runtime (recorded below).
- Checking only 3.8: builds 4205+ run the same package under 3.14.

**Example.** Recorded on this machine (uv 0.12.15, CPython 3.8.20):

```text
$ uv run --python 3.8 --no-project python -m py_compile p39.py
py_compile p39 exit=0
$ uv run --python 3.8 --no-project python p39.py
AttributeError: 'str' object has no attribute 'removeprefix'
$ uv run --python 3.8 --no-project python -c 'import p39b'
TypeError: 'type' object is not subscriptable
$ uv run --python 3.8 --no-project python -m py_compile m.py
SyntaxError: invalid syntax          (a match statement; exit 1)
```

The package passes both ways: `sh assets/examples/verify.sh py38` prints
`py_compile 3.8: package, host tests, stub, and snippets compile`, then
18 + 23 tests OK and `11/11 mutants killed` under 3.8.20.

**Cost removed.** Import errors in the plugin host on older builds. Metric:
failing 3.8 runs (py_compile errors plus test failures) go to 0.

**Verify.**

1. `sh assets/examples/verify.sh py38` exits 0.
1. `sh assets/examples/verify.sh offline` with `PYTHON` set to 3.14 exits
   0, covering the 4205+ host generation.

## plugin_loaded and plugin_unloaded

**Definition.** A module-level `plugin_loaded()` is called when the API is
ready; `plugin_unloaded()` is called just before the plugin is unloaded,
including on package reload ([Plugin Lifecycle][lifecycle]).

**Use when.**

- The plugin reads settings, registers `add_on_change`, or builds state
  that needs the API.
- The plugin creates anything that outlives one call: settings callbacks,
  regions, status keys, phantom sets, worker requests.

**Do not use when.**

- Adding empty hooks: they own nothing.
- Releasing user-owned things in `plugin_unloaded` (settings files, key
  bindings): release only what the load created.

**Example.**

```python
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
```

Runnable: `assets/examples/TodoLens/plugin.py`.

**Cost removed.** Duplicate callbacks and orphaned decorations after each
reload. Metric: `Settings.callback_count()` in the stub stays 1 across
unload + reload + load; regions and status are empty after unload.

**Verify.**

1. `python test_adapter.py` in `offline/`:
   `test_reload_keeps_one_settings_callback` and
   `test_unload_erases_owned_decorations` pass.
1. `VARIANT=no-clear-on-change python test_adapter.py` fails
   `test_reload_keeps_one_settings_callback` (callback count 2).
1. Host (Not runnable here): save `plugin.py` twice, change the setting
   once, and count `TodoLens:` console lines from one bad value.

## API calls at import time

**Definition.** Before build 4171 a plugin may call only
`sublime.version()`, `platform()`, `arch()`, `channel()`, and (4081+)
`executable_path()`, `packages_path()`, `installed_packages_path()`,
`cache_path()` at import; during startup other calls are "silently
ignored" ([porting guide][porting]). The API reference marks this list as
removed in 4171 ([lifecycle]); the 4180 release notes say "All functions
are now available at import time" ([notes]). The sources disagree;
treat 4180 as the safe boundary.

**Use when.**

- Placing a module-level statement: API calls belong in
  `plugin_loaded()` unless the minimum build is 4180.

**Do not use when.**

- Calling `sublime.load_settings(...)` at module level in a package that
  supports builds before 4180: the settings object is not loaded and the
  plugin runs with defaults.

**Example.**

```python
import sublime

VERSION = sublime.version()  # allowed at import on every build


def plugin_loaded():
    global SETTINGS
    SETTINGS = sublime.load_settings("X.sublime-settings")
```

**Cost removed.** Settings or windows missing only at startup, not on a
manual reload, which makes the bug hard to reproduce. Metric: module-level
`sublime.*()` calls outside the safe list, counted by the checker.

**Verify.**

1. `python scripts/test_check_package.py`: the fixture's module-level
   `sublime.load_settings` is reported as
   `plugin.py:4: sublime.load_settings() at import time`, while
   `sublime.version()` is not.
1. `python scripts/check_package.py <pkg>` reports 0 such lines.

## Load state owned by one plugin load

**Definition.** One object created in `plugin_loaded()` holds everything
the load owns (settings handle, request generations, per-view results,
phantom sets). Deferred callbacks capture that object, not the module
global. `plugin_unloaded()` closes it so every callback it scheduled
becomes a no-op.

**Use when.**

- The plugin schedules `set_timeout`/`set_timeout_async` work or keeps
  per-view data.
- The package can reload while work is queued (saving a plugin file
  reloads it).

**Do not use when.**

- Using a module-level `unloaded = False` flag instead: reload
  re-executes the module and resets it, so an old callback reads `False`
  and runs.
- The plugin has no deferred work: plain functions are enough.

**Example.**

```python
class Generations:
    def __init__(self) -> None:
        self._latest: Dict[int, int] = {}
        self._closed = False

    def next(self, key: int) -> int:
        token = self._latest.get(key, 0) + 1
        self._latest[key] = token
        return token

    def is_current(self, key: int, token: int) -> bool:
        return not self._closed and self._latest.get(key) == token

    def close(self) -> None:
        self._closed = True
```

Runnable: `assets/examples/TodoLens/core.py` (`Generations`) and
`plugin.py` (`LoadState`, `schedule_scan` captures `state`).

**Cost removed.** Callbacks from an unloaded plugin drawing into views
after reload. Metric: `View.add_regions` calls recorded by the stub after
unload → reload → load with a scan still queued: 0.

**Verify.**

1. `test_callback_from_unloaded_load_is_ignored` passes.
1. `VARIANT=close-is-noop python test_adapter.py` fails that test.
1. Host (Not runnable here): set `"debounce_ms": 3000`, type a marker,
   save `plugin.py` within 3 s, and check that no annotation appears
   until the next edit.

## Pure core and host adapter split

**Definition.** `core.py` holds every decision (parsing, validation, edit
order, freshness, context answers, HTML) with no `sublime` import;
`plugin.py` only reads host state, calls `core`, and applies results.
Sublime loads both as plugins (`TodoLens.core`, `TodoLens.plugin`); the
package-relative `from . import core` works because each plugin is a
sub-module of the package module ([env]).

**Use when.**

- Logic that maps input → output without the editor.
- Edge cases that are slow to set up in a real view (reversed
  selections, operators, invalid settings).

**Do not use when.**

- Moving host calls into `core.py`: testing it then needs the host.
- Splitting a three-line command into modules: the split pays off only
  when there is logic to test.

**Example.**

```python
def plan_edits(regions):
    """Normalize (a, b), drop empty ones, order last to first."""
    spans = {(min(a, b), max(a, b)) for a, b in regions if a != b}
    return sorted(spans, reverse=True)
```

`TodoLensMarkDoneCommand.run` only turns `view.sel()` into pairs, calls
`core.plan_edits`, and replaces text.

**Cost removed.** Editor-only test cycles for logic. Metric: 18 pure
tests run with no editor (`Ran 18 tests in 0.001s` on this machine,
machine-specific), and 11 mutants of that logic are detected offline.

**Verify.**

1. `grep -n "import sublime" assets/examples/TodoLens/core.py` prints
   nothing.
1. `python test_core.py` in `offline/` prints `Ran 18 tests` and `OK`.

[env]: https://www.sublimetext.com/docs/api_environments.html
[notes]: https://www.sublimetext.com/download
[porting]: https://www.sublimetext.com/docs/porting_guide.html
[lifecycle]: https://www.sublimetext.com/docs/api_reference.html#plugin-lifecycle
