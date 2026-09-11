# Embedded runtime, commands, and lifecycle

## Select the actual host

The [stable download](https://www.sublimetext.com/download) lists build 4200 as
of 2026-09-11. The
[API environments](https://www.sublimetext.com/docs/api_environments.html) page
also describes development build 4205. Version badges matter: documentation for
a later development build is not evidence that an API exists in 4200.

Sublime uses embedded Python, not the interpreter on PATH. A root
`.python-version` containing `3.8` selects the newer host in build 4200; no
selector defaults to legacy Python 3.3 outside the User package. In 4205, Python
3.14 replaces the 3.8 host and accepts `3.8` as a compatibility selector. Thus
the marker does not pin an exact interpreter across Sublime builds. Test all
declared host generations, especially native dependencies; do not bundle a
system-Python wheel merely because the language version looks close.

Plugins are root-level Python modules loaded under the package namespace.
Package-relative imports can load pure helper modules. Do not split a tiny
synchronous operation into a service, worker, config layer, and utility module.
The host's `sublime` and `sublime_plugin` modules are not ordinary PyPI runtime
dependencies. Use supported host stubs or host-aware analysis when needed, not
missing-import suppression directives or replacement runtime modules.

## Own commands and edits

Use TextCommand for buffer edits, WindowCommand for project/window operations,
and ApplicationCommand for application-wide work. Command class names map to
snake_case IDs; keep palette registrations and callers consistent when renaming.
Consult the [API reference](https://www.sublimetext.com/docs/api_reference.html)
and the installed Default package before recreating a built-in operation.

`Edit` belongs to one TextCommand invocation. Never retain it in an event
listener, future, timer, or object for later reuse. Apply background results
through a new text command. One synchronous command can group multiple changes
into one undo step; exercise undo/redo through the real host, not a mock token.

`view.sel()` already provides sorted, non-overlapping Regions. Snapshot those
regions before editing and replace from the end of the buffer toward the start
when replacements change lengths. Do not add an overlap-normalization algorithm
for selections that the host has already normalized. Regions supplied by other
sources need the feature's explicit overlap policy.

Define caret-only, reversed-selection, multi-selection, read-only, and undo
behavior for the feature. Use `is_enabled` for command availability and verify
programmatic `run_command` behavior in the target host. Build 4200 also checks
enablement for direct `run_command` calls, so a synchronous command need not
duplicate that guard in `run`. A deferred apply command still needs current
state checks; earlier enablement cannot validate later results. Preserve
untouched text and avoid whole-buffer fallbacks for a selection-only feature.

The [starter](../assets/package-template/TEMPLATE.md) implements a concrete
selection transformation using the stdlib JSON encoder. It does not implement
escaping rules itself or pretend a greeting test proves editor integration.

## Add asynchronous state only when needed

EventListener observes general events; ViewEventListener attaches behavior to a
view. Keep synchronous handlers short. `set_timeout` schedules main-thread work;
`set_timeout_async` schedules work on an alternate thread. The API's
thread-safety does not make a sequence of reads atomic or a captured buffer
snapshot current. Do not equate an async callback with unbounded task isolation.

For an asynchronous transformation, capture immutable input, the intended view,
its change count, and the request generation. On the main-thread apply path,
check view validity, current generation, read-only status, and change count
before invoking a fresh TextCommand. Recheck the relevant state inside that
command if another callback can run before it. Discard stale results rather than
overwriting later user edits. A generation token is unnecessary for a purely
synchronous transformation with no deferred work.

API-dependent initialization can live in `plugin_loaded()` for lifecycle clarity
and compatibility. Build 4180 release notes include unrestricted API access at
import time; do not claim that all import-time API calls are forbidden on every
supported build. Heavy work still delays loading.

Own every callback or worker you create. On unload, clear named settings
callbacks, invalidate outstanding generations, and stop owned workers without
blocking the UI indefinitely. A previously scheduled timeout can still execute
its old closure after a module reload. Avoid indefinite global retention of
views. Do not add empty lifecycle functions or a no-op settings listener merely
to demonstrate these APIs.

A module-global `unloaded` boolean that resets on import is not sufficient for
reload cancellation. The installed 4200 loader calls unload then
`importlib.reload`, reusing the module globals. Old callbacks can see the reset
boolean. Capture a per-load cancellation object and invalidate that object on
unload, or use a captured generation identity that cannot become current again.
Validate the old callback after module re-execution, not just after unload.
