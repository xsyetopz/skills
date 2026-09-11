# Sublime Text selection-command starter

A working TextCommand encodes each non-empty selection as a JSON string literal
using Python's stdlib encoder. It preserves Unicode, escapes embedded quotes,
backslashes and control characters, leaves carets alone, respects read-only
views, and groups multi-selection changes into one undo step.

This is an adaptation example, not a recommendation to publish another JSON
utility package. Check Sublime's built-in commands and maintained packages
before creating a new feature. Replace `Example` and the `example_json_string`
command ID consistently. Keep the tests aligned with the feature you build. Do
not carry unused settings, workers, or lifecycle callbacks into the project.

## Supported runtime

The starter targets Sublime Text 4 build 4200 with its embedded Python 3.8. The
root `.python-version` selects that host. Test newer host generations separately
before extending the supported range; a system-Python syntax check is not an
editor integration test.

## Host tests

Copy the package to `Packages/ExampleJson` in a disposable Sublime profile.
Install [UnitTesting](https://github.com/SublimeText/UnitTesting) there. In the
Sublime console, run:

```python
window.run_command("unit_testing", {"package": "ExampleJson"})
```

The five tests create and close their own scratch views. They cover changed
selection offsets, one-step undo/redo, reversed selections, Unicode/newlines,
carets, and read-only programmatic invocation. Run again with package reload
enabled. Do not replace the host with mock `sublime` modules or skip tests when
the API is unavailable.

Invoke **Example: Encode Selections as JSON Strings** from the palette in a
writable scratch buffer. Check that it is unavailable with only carets or a
read-only view. This verifies UI registration separately from direct commands.

## Packed artifact

From the copied package root, create an archive outside the source tree:

```sh
python3 -m zipfile -c ../ExampleJson.sublime-package \
  .python-version ExamplePlugin.py Default.sublime-commands
python3 -m zipfile -l ../ExampleJson.sublime-package
```

Include the project's actual license and other required resources before
publishing. This command packages only the starter's three runtime files; it is
not a complete Package Control release workflow.

Install the archive in the disposable profile's `Installed Packages`. Remove its
loose implementation; loose files override packed files. Keep only the `tests`
directory in `Packages/ExampleJson`, then run UnitTesting with package reload
disabled against the packed implementation. Verify packed imports and palette
resources; archive listing alone cannot establish host behavior.
