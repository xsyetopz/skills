# Sublime Text Plugins

Gotchas for the plugin host, commands, events, async work, settings, resource files, decorations,
and packaging. Run `python3 scripts/check_sublime_package.py PACKAGE_DIR [--external CMD ...]` on
the package before release; it reports one line per issue and lists the built-in or other-package
commands it cannot resolve unless they are passed with `--external`.

## Contents

- [Host and Lifecycle](#host-and-lifecycle)
- [Commands](#commands)
- [Events and Async Work](#events-and-async-work)
- [Settings and Resource Files](#settings-and-resource-files)
- [Decorations and HTML](#decorations-and-html)
- [Tests and Packaging](#tests-and-packaging)
- [Sources](#sources)

## Host and Lifecycle

- Mistake: no `.python-version`, or a value the target builds do not know. Fix: write `3.8` for
  builds 4050 to 4204; any other value or no file selects Python 3.3, except in the `User` package.
  From build 4205 the newer host is Python 3.14 and `3.8` still selects it, so test both. [API
  environments][env]
- Mistake: passing a `py_compile` check as proof of Python 3.8 compatibility. Fix: run the tests
  under 3.8; `py_compile` accepts `str.removeprefix` and `list[int]` annotations that then fail at
  runtime.
- Mistake: `sublime.load_settings()` or other `sublime.*` calls at module level. Fix: only
  `version`, `platform`, `arch`, `channel`, and the path functions are safe at import. Move the rest
  into `plugin_loaded()` unless the minimum build is 4180. Reason: before build 4171 the API ignores
  other calls during import, and the 4180 release notes say all functions are available at import.
  [plugin lifecycle][lifecycle], [release notes][notes]
- Mistake: listeners, timers, region keys, or phantom sets created at import and never released.
  Fix: create them in `plugin_loaded()` and release them in `plugin_unloaded()`; callbacks capture
  the load object, not a module global. Reason: a reload runs the new module while the old callbacks
  still fire.
- Mistake: decisions mixed into `sublime` calls. Fix: keep the logic in a module with no `sublime`
  imports so it can run under plain `unittest`; the plugin module only adapts.

## Commands

- Mistake: changing buffer text outside `TextCommand.run`, or storing the `edit` object for later.
  Fix: edit only inside `run` with its `edit`; deferred results go through
  `view.run_command("name", {json args})` for a fresh `Edit`. [Edit][edit], [porting guide][porting]
- Mistake: replacing several selections first-to-last. Fix: iterate from the last region to the
  first, and normalize reversed regions with `begin()` and `end()`; earlier edits shift later
  offsets. [Selection][selection], [Region][region]
- Mistake: a palette or key entry that does nothing. Fix: the command name is the class name in
  snake case without the `Command` suffix. Avoid consecutive capitals; build 4213 changed how they
  are split, so the name depends on the build. The checker flags this and any `"command"` in a
  resource file that resolves to nothing. [naming][naming], [release notes][notes]
- Mistake: relying on `is_enabled` alone to guard a command. Fix: repeat the guard in `run`; the
  reference does not promise that `run_command` skips a disabled command. [Command][command]
- Mistake: an `input()` method with no palette entry. Fix: list the command in a `.sublime-commands`
  file; input handlers are shown only from the Command Palette. [Command.input][commandinput]

## Events and Async Work

- Mistake: slow work in `on_modified` or `on_selection_modified`. Fix: use the `_async` variants or
  `set_timeout_async` for computation only, and debounce with a generation counter.
  [EventListener][el]
- Mistake: touching the view or running commands from an async callback. Fix: hand the result back
  with `sublime.set_timeout`, then apply it only when `view.is_valid()`, `view.change_count()` (read
  before the text), and the request generation still match. Use `change_id` and
  `transform_region_from` to map old regions onto newer text. [set_timeout][settimeout],
  [change_count][changecount], [change_id][changeid], [transform_region_from][transform]
- Mistake: `EventListener` for per-view work. Fix: `ViewEventListener` with `is_applicable` so it
  only attaches to matching views. [ViewEventListener][vel]
- Mistake: `on_query_context` returning `False` for keys it does not own. Fix: return `None` so
  other handlers decide, and honor `operator` and `match_all`. [on_query_context][querycontext],
  [keys][keys]

## Settings and Resource Files

- Mistake: reading settings once and caching them. Fix:
  `sublime.load_settings("Pkg.sublime-settings")` in `plugin_loaded`, `add_on_change(tag, cb)` with
  a package-prefixed tag, and `clear_on_change(tag)` in `plugin_unloaded`.
  [load_settings][loadsettings], [add_on_change][onchange]
- Mistake: unprefixed settings, region, status, or context keys. Fix: prefix every key with the
  package name; they share one namespace with every other package.
- Mistake: `open()` on a path built from `__file__` to read a shipped file. Fix:
  `sublime.load_resource("Packages/Pkg/file")`, which works when the package is a `.sublime-package`
  archive. [load_resource][loadres], [packages][packages]
- Mistake: a resource file the editor silently ignores. Fix: the checker parses `.sublime-commands`,
  `-keymap`, `-menu`, `-settings`, and `-mousemap` with the comments and trailing commas Sublime
  accepts. [key bindings][keys], [menus][menus]

## Decorations and HTML

- Mistake: text from a buffer, file, setting, or tool put into popup, phantom, or annotation HTML.
  Fix: `html.escape` it first; `subl:` links run commands, so unescaped text is an injection path.
  [minihtml][minihtml], [html.escape][escape]
- Mistake: `add_regions` with flags `HIDDEN` expecting annotations to show. Fix: annotations are
  HTML shown at line end (build 4050+); check the region flags. [add_regions][addregions],
  [RegionFlags][regionflags]
- Mistake: a `Phantom` set that is not kept. Fix: hold one `PhantomSet` per view and update it
  instead of creating new ones. [PhantomSet][phantomset]

## Tests and Packaging

- Mistake: treating a stub or pure test as proof of editor behavior. Fix: use it for call shapes and
  logic; run undo, drawing, key dispatch, and palette checks under UnitTesting in a disposable or
  safe-mode profile. [UnitTesting][ut], [safe mode][safe]
- Mistake: a package directory with `.pyc`, `__pycache__`, `package-metadata.json`, or a root
  `__init__.py`, or a package name containing `.`. Fix: remove them; Package Control will not load a
  package whose name has a dot. [packages][packages], [submitting][submit]
- Mistake: a wrong `"sublime_text"` range in the channel entry. Fix: set it to the lowest build
  whose APIs the package uses, such as `>=4050` for annotations and the 3.8 host. [example
  repository][repo]
- Mistake: opening a channel pull request or publishing without being asked. Fix: stop after the
  checker and archive listing.

## Sources

[addregions]: https://www.sublimetext.com/docs/api_reference.html#sublime.View.add_regions
[changecount]: https://www.sublimetext.com/docs/api_reference.html#sublime.View.change_count
[changeid]: https://www.sublimetext.com/docs/api_reference.html#sublime.View.change_id
[command]: https://www.sublimetext.com/docs/api_reference.html#sublime_plugin.Command
[commandinput]: https://www.sublimetext.com/docs/api_reference.html#sublime_plugin.Command.input
[edit]: https://www.sublimetext.com/docs/api_reference.html#sublime.Edit
[el]: https://www.sublimetext.com/docs/api_reference.html#sublime_plugin.EventListener
[env]: https://www.sublimetext.com/docs/api_environments.html
[escape]: https://docs.python.org/3/library/html.html#html.escape
[keys]: https://www.sublimetext.com/docs/key_bindings.html
[lifecycle]: https://www.sublimetext.com/docs/api_reference.html#plugin-lifecycle
[loadres]: https://www.sublimetext.com/docs/api_reference.html#sublime.load_resource
[loadsettings]: https://www.sublimetext.com/docs/api_reference.html#sublime.load_settings
[menus]: https://www.sublimetext.com/docs/menus.html
[minihtml]: https://www.sublimetext.com/docs/minihtml.html
[naming]: https://docs.sublimetext.io/guide/extensibility/plugins/
[notes]: https://www.sublimetext.com/download
[onchange]: https://www.sublimetext.com/docs/api_reference.html#sublime.Settings.add_on_change
[packages]: https://www.sublimetext.com/docs/packages.html
[phantomset]: https://www.sublimetext.com/docs/api_reference.html#sublime.PhantomSet
[porting]: https://www.sublimetext.com/docs/porting_guide.html
[querycontext]: https://www.sublimetext.com/docs/api_reference.html#sublime_plugin.ViewEventListener.on_query_context
[region]: https://www.sublimetext.com/docs/api_reference.html#sublime.Region
[regionflags]: https://www.sublimetext.com/docs/api_reference.html#sublime.RegionFlags
[repo]: https://raw.githubusercontent.com/wbond/package_control/master/example-repository.json
[safe]: https://www.sublimetext.com/docs/safe_mode.html
[selection]: https://www.sublimetext.com/docs/api_reference.html#sublime.Selection
[settimeout]: https://www.sublimetext.com/docs/api_reference.html#sublime.set_timeout
[submit]: https://packagecontrol.io/docs/submitting_a_package
[transform]: https://www.sublimetext.com/docs/api_reference.html#sublime.View.transform_region_from
[ut]: https://github.com/SublimeText/UnitTesting
[vel]: https://www.sublimetext.com/docs/api_reference.html#sublime_plugin.ViewEventListener
