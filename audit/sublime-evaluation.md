# Sublime capability and starter evaluation

Evaluated 2026-09-11. Scope: `sublime-plugin-development`, not the other editor
starters or the full suite.

## Accepted changes

- Replaced the greeting demo, unused settings callback, unused configuration,
  placeholder install message, and missing-import suppression with one real
  selection command. It uses `json.dumps`, not a custom escaping implementation.
- Replaced the greeting unit test with five real-host command tests. No fake
  Sublime module, skipped host test, or mocked Edit token is shipped.
- Consolidated six inherited reference fragments into two substantive files:
  runtime/edit ownership and packaging/validation. They distinguish current
  stable APIs from development docs, synchronous work from async lifecycle,
  packed resources from loose overrides, and archive creation from publication.
- Removed the inherited uncommitted explicit-only metadata restriction. It was
  absent from the original committed skill and unsupported by a user request.
  The skill remains implicitly discoverable for Sublime work.

## Primary evidence

The [stable download](https://www.sublimetext.com/download) lists build 4200.
The downloaded macOS application passed `codesign --verify --deep --strict`
before execution. Its actual plugin runtime reported Python 3.8.12. The
[environment documentation](https://www.sublimetext.com/docs/api_environments.html)
also describes development 4205/Python 3.14; that environment was not executed.

Verified
[command/edit/selection APIs](https://www.sublimetext.com/docs/api_reference.html),
[package precedence](https://www.sublimetext.com/docs/packages.html),
[minihtml](https://www.sublimetext.com/docs/minihtml.html),
[syntax format](https://www.sublimetext.com/docs/syntax.html),
[CLI](https://www.sublimetext.com/docs/command_line.html),
[safe mode](https://www.sublimetext.com/docs/safe_mode.html), and
[Package Control submission](https://packagecontrol.io/docs/submitting_a_package).
The installed `Lib/python38/sublime_plugin.py` additionally confirms that
`reload_plugin` calls unload then `importlib.reload` on the existing module.

Tests used the maintained
[UnitTesting runner](https://github.com/SublimeText/UnitTesting) at commit
`1e968c58ef7a5c7f47dfb48a85a92e60041321b2`, with its required `sublime_aio`
0.2.7 dependency. Coverage was not requested. Initial manual installation
omitted this dependency and failed to register UnitTesting; installing the
dependency corrected the setup failure. No replacement runner was invented or
shipped. Temporary bootstrap code only invoked UnitTesting and recorded runtime
identity.

## Host and artifact results

Workspace: `/tmp/skill-sublime-validation`. The final application used the new
disposable `Data` directory there. No pre-existing Sublime process or app
installation was found. An early raw-binary client attempt started a second
instance and created an empty normal profile; it was stopped. Its newly created
profile contained only generated session state. Subsequent commands used the
bundled `subl` client. Task-owned processes, profile links, normal/safe-mode
profiles, and Library caches were removed after validation.

Executed cases:

- Multiple selections whose replacements increase length preserve both target
  regions and untouched intervening text; undo and redo affect the whole
  command.
- Reversed selection preserves Unicode and encodes its embedded newline.
- Carets beside a nonempty selection remain carets at the host-adjusted offset.
- Caret-only invocation leaves text and change count unchanged.
- A read-only programmatic invocation leaves the text unchanged.

An initial test-fixture failure closed the host's last view/window after the
first test, causing later `new_file()` calls to return invalid views. The
fixture now owns a scratch anchor for the suite and closes only its own views.
Adding arbitrary delays was tried in the disposable copy, did not fix the cause,
and was not retained.

All five tests passed in the loose package with reload. A temporary
forward-order replacement fault produced one intended assertion failure in the
multi-selection test. The fault was not applied to repository code. A separate
instrumented run showed that 4200 checks `is_enabled` for direct `run_command`
calls; a redundant read-only guard inside `run` was therefore removed rather
than retained as speculative defense.

A clean restart with only the release ZIP implementation and loose tests passed
all five cases plus one temporary artifact-provenance test. The host reported:

```text
build: 4200
Python: 3.8.12
module: Data/Installed Packages/ExampleJson.sublime-package/ExamplePlugin.py
selector: 3.8
palette command: example_json_string
```

The provenance check also loaded the palette and Python selector through Sublime
resource APIs. The documented `python3 -m zipfile -c` command reproduced every
host-tested runtime file byte-for-byte. Tests/build scaffolding were not packed.
The interactive command palette was not visually operated; this is resource and
command execution evidence, not a claim about rendered UI appearance.

## Independent forward evaluation

A reviewer received the skill and a raw asynchronous selection formatter using
an existing formatter dependency. It repaired Edit-token retention, applied
results through a fresh TextCommand, checked buffer freshness, and reported
formatter failures. It explicitly limited the incomplete selection policy to one
nonempty selection instead of silently processing arbitrary selections.

The first repair used a resettable module-global unload flag. Coordinator review
identified the in-place reload hazard from the actual host loader source. The
reviewer corrected the temporary artifact to capture and invalidate per-load
state, including failure callbacks. The skill now explains this specific hazard.
The reviewer's miniature re-execution test demonstrates the guard distinction;
it was not shipped or counted as a host test of the formatter. That formatter
artifact was syntax-checked, not executed in Sublime.

The final metadata-only routing pass activated direct, paraphrased, incomplete,
and composed Sublime+CI requests. It did not select Sublime implementation for a
VS Code port, a web-app repair, or an unspecified editor target. Explicit
Sublime+CI invocation also retained the separate CI responsibility.

## Other gates and limits

Ruff check/format, Python 3.8 syntax parsing, palette JSON parsing, local
Markdown links, existing Markdown rules, official skills-ref, and bundled quick
validation passed. No syntax grammar, native dependency, Package Control
submission, other platform, or Python 3.14 host was validated or claimed by this
starter change.
