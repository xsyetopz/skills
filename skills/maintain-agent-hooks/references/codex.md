# Codex hooks

Reviewed 2026-09-12 against Codex CLI 0.154.0 and the official
[hooks reference](https://developers.openai.com/codex/hooks).

Codex discovers `hooks.json` or inline `[hooks]` beside active configuration,
notably `~/.codex/` for user scope and `<repo>/.codex/` for project scope. Do
not define both forms in one layer. Project hooks load only for a trusted
project. Every new or changed non-managed definition is skipped until its exact
hash is reviewed and trusted through `/hooks`.

The configuration is event -> matcher group -> handler. Matchers are regular
expressions but not every event honors them. Command handlers receive JSON on
stdin, run from the session working directory, and use seconds for `timeout`.
Most default to 600 seconds; `SessionEnd` and `Interrupt` have shorter limits.
Synchronous output and blocking meaning vary by event. Async handlers can
finish out of order and are canceled at session end. Inspect the event's exact
input/output section before returning a decision.

For a project fixture, copy `assets/codex/hooks.json` to `.codex/hooks.json` and
the shared handler to `.agent-hooks/observe.py`. Resolve the handler from the
Git root because Codex can start in a subdirectory. Open `/hooks`, inspect the
source and command, trust it, start an isolated session, then remove both files
to roll back.
