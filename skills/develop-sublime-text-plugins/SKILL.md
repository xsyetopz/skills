---
name: develop-sublime-text-plugins
description: >-
  Builds and tests Sublime Text plugins: commands, event listeners, async
  work, settings, key bindings and menus, regions, popups, and packaging. Use
  when writing or fixing a Sublime Text plugin. Not for generic Python apps or
  user settings.
---

# Develop Sublime Text Plugins

Build or change a Sublime Text package so that it runs on the plugin host
its `.python-version` selects, edits text only inside a `TextCommand`,
does slow work off the main thread and discards stale results, owns and
releases everything a plugin load creates, exposes commands through
resource files that resolve, and ships as a clean archive. Each card in
the references gives the definition, **Use when** and **Do not use when**
conditions, the cost it removes, verification, and a runnable example.
Cards cite the Sublime Text API reference, API environments, porting
guide, release notes up to build 4215, UnitTesting, and Package Control
documentation; follow them instead of recalling API behavior.

## Workflow

1. Record the target: minimum and maximum Sublime Text build (README,
   channel entry `"sublime_text"`, CI), and `.python-version`. Builds
   4050-4204 run `3.8` on Python 3.8; 4205+ run it on 3.14; no file or
   another value means 3.3 on older builds. Keep the declared range.
1. Map the package before adding files: root `.py` plugins, resource
   files (`*.sublime-commands`, `-keymap`, `-menu`, `-settings`), tests,
   `unittesting.json`. Extend what exists; add no second scaffold.
1. Pick the card from the routing table and read all of it, including
   **Do not use when**.
1. Put decisions in a module without `sublime` imports (like
   `core.py`) and host calls in the plugin module. Write the pure test
   and, for adapter paths, a stub test first.
1. Implement the smallest change that satisfies the card.
1. Run the offline checks (commands below). Under Python 3.8 run the
   suites, not only `py_compile`: it accepts `str.removeprefix` and
   `list[int]` annotations, which then fail at runtime
   ([3.8 check][py38]).
1. Prove each new test discriminates: add a mutant to
   `offline/variants.py` that reintroduces the defect and confirm
   `run_mutants.py` reports it killed by the named test.
1. Run `scripts/check_package.py` on the package with every built-in or
   other-package command passed as `--external`.
1. Host behavior (undo, drawing, key dispatch, palette) needs Sublime
   Text: run UnitTesting host tests in a disposable or safe-mode profile.
   If no editor is available, say so and list the exact commands.

## Route the task to a card

| Task or symptom | Card |
| --- | --- |
| Plugin runs on the wrong Python, `.python-version` | [Host selection](references/host-and-lifecycle.md#plugin-host-selection-with-python-version) |
| Prove 3.8 compatibility | [3.8 check](references/host-and-lifecycle.md#python-38-compatibility-check) |
| Setup, teardown, reload duplicates | [plugin_loaded](references/host-and-lifecycle.md#plugin_loaded-and-plugin_unloaded), [load state](references/host-and-lifecycle.md#load-state-owned-by-one-plugin-load) |
| Settings missing only at startup | [Import time](references/host-and-lifecycle.md#api-calls-at-import-time) |
| Logic hard to test in the editor | [Core/adapter split](references/host-and-lifecycle.md#pure-core-and-host-adapter-split) |
| Edit text, `Edit` object errors | [TextCommand](references/commands.md#textcommand-and-the-edit-token) |
| Later selections corrupted | [Last-to-first edits](references/commands.md#last-to-first-multi-selection-edits) |
| Window or global actions | [WindowCommand](references/commands.md#windowcommand), [ApplicationCommand](references/commands.md#applicationcommand) |
| Disable in read-only views, menu checkbox | [is_enabled](references/commands.md#is_enabled-is_visible-and-is_checked) |
| Palette/key entry does nothing | [Command names](references/commands.md#command-names-from-class-names) |
| Ask the user for arguments | [ListInputHandler](references/commands.md#listinputhandler), [TextInputHandler](references/commands.md#textinputhandler-with-next_input) |
| React to view or window events | [ViewEventListener](references/events-and-async.md#vieweventlistener-with-is_applicable), [EventListener](references/events-and-async.md#eventlistener) |
| Typing lags | [Async handlers](references/events-and-async.md#async-event-handlers), [debounce](references/events-and-async.md#debounce-with-generation-tokens) |
| Worker result must reach the UI | [set_timeout](references/events-and-async.md#set_timeout-and-set_timeout_async) |
| Late result overwrites newer text | [change_count](references/events-and-async.md#change-count-freshness-guard), [change_id](references/events-and-async.md#change_id-and-transform_region_from) |
| Key binding only in some states | [on_query_context](references/events-and-async.md#on_query_context), [keymap](references/settings-and-ui-files.md#key-bindings-with-a-plugin-context) |
| User options, change callbacks | [load_settings](references/settings-and-ui-files.md#load_settings-with-a-package-settings-file), [add_on_change](references/settings-and-ui-files.md#add_on_change-and-clear_on_change), [view settings](references/settings-and-ui-files.md#view-settings-as-per-view-switches) |
| Read a file shipped in the package | [load_resource](references/settings-and-ui-files.md#load_resource-instead-of-file-paths) |
| Palette or menu entries | [Palette](references/settings-and-ui-files.md#command-palette-entries), [menus](references/settings-and-ui-files.md#menu-entries-with-a-checkbox) |
| Highlight ranges, notes at line end | [add_regions](references/decorations.md#add_regions-with-annotations) |
| Blocks between lines | [PhantomSet](references/decorations.md#phantomset) |
| Hover details, status, pick from list | [Popup](references/decorations.md#show_popup-from-on_hover), [status](references/decorations.md#set_status), [quick panel](references/decorations.md#show_quick_panel) |
| File text shown as HTML | [Escaping](references/decorations.md#escaping-text-for-minihtml) |
| Tests: pure, stub, mutants, in editor | [Pure](references/testing-and-packaging.md#pure-core-unittest), [stub](references/testing-and-packaging.md#call-shape-stub-of-the-host-modules), [mutants](references/testing-and-packaging.md#mutant-matrix), [UnitTesting](references/testing-and-packaging.md#unittesting-host-tests) |
| Host tests without the user's editor | [Headless runner](references/testing-and-packaging.md#unittesting-headless-container-runner), [safe mode](references/testing-and-packaging.md#safe-mode-test-session) |
| CI, `.sublime-syntax` scopes | [Actions](references/testing-and-packaging.md#unittesting-in-github-actions), [syntax tests](references/testing-and-packaging.md#syntax-test-files) |
| Release checks, archive, publishing | [Checker](references/testing-and-packaging.md#package-checker), [archive](references/testing-and-packaging.md#sublime-package-archive-and-loose-overrides), [channel](references/testing-and-packaging.md#package-control-channel-entry), [channel test](references/testing-and-packaging.md#channelrepositorytools-before-a-pull-request) |

## Rules

- Buffer text changes only inside `TextCommand.run` with its `edit`.
  Never store `edit`; deferred results go through `view.run_command`
  with JSON arguments.
- Multi-selection edits that change length run from the last region to
  the first; normalize reversed regions with `begin()`/`end()`.
- `_async` handlers and `set_timeout_async` callbacks compute only. Drawing
  and commands happen after `set_timeout`, and only when `is_valid()`,
  `change_count()` (read before the text), and the request generation
  still match.
- Every callback, region key, status key, phantom set, and generation is
  created by one load and released in `plugin_unloaded`; callbacks
  capture the load object, not a module global.
- No `sublime.*()` calls at import time except `version`, `platform`,
  `arch`, `channel`, and the path functions, unless the minimum build is
  4180.
- Guards live in `run` as well as `is_enabled`: the reference does not
  say that `run_command` skips disabled commands.
- `on_query_context` returns `None` for keys the plugin does not own and
  honors `operator` and `match_all`.
- Text from buffers, files, settings, or tools is `html.escape`d before
  it enters popup, phantom, or annotation HTML (`subl:` links run
  commands).
- Resources are read with `sublime.load_resource`, never with `open()` on
  a path built from `__file__`.
- Command class names avoid consecutive capitals; every `"command"` in
  resource files resolves (`scripts/check_package.py`).
- Settings keys, region keys, status keys, `on_change` tags, and context
  keys carry the package prefix.
- No `.pyc`, `__pycache__`, `package-metadata.json`, or root
  `__init__.py` in the package; do not publish or open channel pull
  requests without explicit authorization.
- A stub or pure test proves call shapes and logic, never editor
  behavior; report host checks that did not run as not verified.

## Bundled tools

- `assets/examples/TodoLens/`: a complete package with `core.py` (pure),
  `plugin.py` (listener, commands, input handlers, settings, regions,
  phantoms, popup, status, quick panel), palette, keymap, context menu,
  settings, `unittesting.json`, and host tests in
  `tests/host_commands.py`. Copy files into the user's package and rename
  `TodoLens`, `todo_lens`, and `KEY` consistently; do not edit the
  installed skill.
- `assets/examples/offline/`: the documented `sublime`/`sublime_plugin`
  stub, pure and stub tests, and mutants.
- `assets/examples/snippets/`: compile-checked host-only examples.
- `sh assets/examples/verify.sh [all|offline|mutants|py38|check|
  package|host]` runs them. `PYTHON` selects the interpreter; `py38` uses
  `uv run --python 3.8`; `host` only prints the in-editor command.

## References

- [Host and lifecycle](references/host-and-lifecycle.md): Python host,
  3.8 checks, `plugin_loaded`, import time, load state, core split.
- [Commands](references/commands.md): TextCommand and Edit, edit order,
  Window/Application commands, availability, names, input handlers.
- [Events and async](references/events-and-async.md): listeners, async
  handlers, timeouts, debounce, `change_count`, `change_id`, contexts.
- [Settings and UI files](references/settings-and-ui-files.md): settings,
  callbacks, view settings, resources, keymap, palette, menus.
- [Decorations](references/decorations.md): regions and annotations,
  phantoms, popups, status, quick panel, minihtml escaping.
- [Testing and packaging](references/testing-and-packaging.md): pure,
  stub, mutants, UnitTesting, CI, safe mode, checker, archive, Package
  Control.

## Completion evidence

The final report contains:

- Target build range and `.python-version`, with builds and Python
  hosts not exercised listed as not verified.
- The cards applied and their **Do not use when** conditions checked.
- Offline results with interpreter versions: pure and stub test counts,
  `N/N mutants killed`, the 3.8 run, and the checker's issue count.
- For each new test, the mutant or reverted fix it kills.
- Host results (UnitTesting counts, build number from
  `sublime.version()`), or the statement that no editor was available
  plus the exact commands to run.
- Archive listing when packaging was requested; channel entry and
  ChannelRepositoryTools result only when publishing was authorized.

[py38]: references/host-and-lifecycle.md#python-38-compatibility-check
