# Sublime runtime, commands and package lifecycle

Research: 2026-09-09. Latest stable listed: **Sublime Text 4 build 4200**
([download/release notes][ref-1]). Current API docs also describe development
build 4205; do not treat those features as stable-4200 APIs.

## Embedded Python and package layout

Plugins are Python files at the package root, loaded as submodules of the
package. The host uses its embedded Python, not system Python. Stable 4200
supports the Python 3.3 legacy environment and opt-in Python 3.8 via a root
`.python-version` containing `3.8`. Build 4205 docs describe Python 3.14
replacing the newer host and accepting `3.8` as a compatibility selector. A 3.8
marker therefore does not mean exactly Python 3.8 on every build. Preserve the
package's declared minimum and test its syntax/dependencies against that range.
[API environments][ref-2].

Keep API-dependent initialization in `plugin_loaded()` for lifecycle clarity and
older-build support. Stable build 4180 made all API functions available at
import time, so do not describe import-time access as universally forbidden.
Heavy work still delays plugin loading. On `plugin_unloaded()`, remove settings
callbacks, invalidate generations and stop owned workers so reloaded module
instances cannot apply stale results.

## Commands and edit ownership

Use `TextCommand` for a view's text, `WindowCommand` for window/project behavior
and `ApplicationCommand` for application actions. CamelCase class names map to
snake_case command IDs. A minimal synchronous edit:

```python
import sublime
import sublime_plugin

class ExampleWrapCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        if self.view.is_read_only():
            return
        for region in reversed(list(self.view.sel())):
            text = self.view.substr(region)
            self.view.replace(edit, region, "[" + text + "]")
```

Reverse order prevents earlier replacements shifting later offsets. Define
empty-selection and undo behavior for the real feature. The `edit` token belongs
only to that command invocation: background callbacks must invoke a fresh
command with data rather than storing the token. For overlapping selections,
normalize according to the feature instead of applying ambiguous replacements.
[API reference][ref-3].

Expose the command through a `Default.sublime-commands` array such as
`[{"caption":"Example: Wrap","command":"example_wrap"}]`. Keymaps and menus use
the same public ID with contextual enablement. Do not overwrite user bindings
merely because the command exists. Settings belong in a named
`.sublime-settings` default resource, with user overrides kept separately.

## Async events and state

`EventListener` sees general events; `ViewEventListener` scopes state to a view.
Keep synchronous callbacks short; use the documented async variants or
`sublime.set_timeout_async` for blocking computation, then `sublime.set_timeout`
for a main-thread apply command. Capture immutable text, view ID,
`change_count()` and request generation before leaving the callback. Re-check
`view.is_valid()`, read-only state and change count inside the fresh TextCommand
before applying results.

Cancellation can invalidate a generation even if a Python worker cannot stop
immediately. Do not capture live views forever in a global future table. Named
`settings.add_on_change` registrations need matching `clear_on_change` on
unload. A timeout scheduled by an old module may still fire, so cleanup alone is
not freshness validation.

## Packed resources and syntax

A `.sublime-package` is a ZIP and may lack ordinary filesystem resource paths.
Use `sublime.load_resource("Packages/Example/resource.json")` or
`load_binary_resource`; use a deliberate cache/temp extraction only when an
external process needs a file. Avoid assuming `__file__` points to an unpacked
asset. Escape workspace text when generating minihtml popups; minihtml is not a
full browser DOM. [Packages][ref-4], [minihtml][ref-5].

For a `.sublime-syntax`, define name, file extensions, top-level scope and
contexts. Match captures/scopes to the grammar; push/pop contexts to preserve
nesting, and test unterminated strings/comments and embedded languages. Use
syntax-test fixtures with the host's syntax-test command; parsing YAML alone
cannot establish correct scope stacks. [Syntax definitions][ref-6].

## Debugging, packaging and distribution

Use View > Show Console for plugin tracebacks, `sublime.version()` for the
actual build, and `sys.version` in the relevant plugin host to establish
runtime. Reload in an isolated/portable profile where supported; do not use the
user's installed configuration as a scratch test. Run pure logic with a
compatible interpreter and API checks inside Sublime.

Inspect the ZIP root: plugin modules, `.python-version`, commands, settings,
syntaxes and resources must appear directly at package-relative paths, not under
an accidental extra directory. Exclude caches, credentials and irrelevant
tests/build output. Package Control distribution uses repository metadata and
release selectors; declare supported Sublime builds/platforms and dependency
requirements, and follow current submission validation. Verify registry
acceptance separately from archive creation. [Package Control
submission][ref-7].

For Package Control submission, prepare a public repository with the package at
its root, license and a tagged release. Fork/clone the Package Control Channel
repository, add the package to the appropriate JSON file under `repository/`,
and submit the scoped PR after its established validation. A structural entry
is:

```json
{
  "name": "Example Tools",
  "details": "https://github.com/example/sublime-example-tools",
  "releases": [{ "sublime_text": ">=4200", "tags": true }]
}
```

The URL is a placeholder; the build selector must reflect actual minimum-version
support. Tags select releases rather than causing every commit to become a
release. Preserve platform/dependency selectors for packages that need them, and
verify repository metadata before asking users to install. Existing packages
ship updates through their declared release source; changing the channel entry
is needed when that source/compatibility contract changes. [Submission
procedure][ref-7].

Refresh for a build-4205+ runtime request, an API marked newer than the minimum,
a native dependency ABI or a changed distribution schema. When using the
starter, replace public names and their registrations consistently.

[ref-1]: https://www.sublimetext.com/download
[ref-2]: https://www.sublimetext.com/docs/api_environments.html
[ref-3]: https://www.sublimetext.com/docs/api_reference.html
[ref-4]: https://www.sublimetext.com/docs/packages.html
[ref-5]: https://www.sublimetext.com/docs/minihtml.html
[ref-6]: https://www.sublimetext.com/docs/syntax.html
[ref-7]: https://packagecontrol.io/docs/submitting_a_package
