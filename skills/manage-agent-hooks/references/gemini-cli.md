# Gemini CLI hooks

Reviewed 2026-09-12 against the official [Gemini CLI hooks
reference](https://geminicli.com/docs/hooks/reference/) and [configuration
reference](https://geminicli.com/docs/reference/configuration/).

Hooks are under `hooks` in `settings.json`; project scope uses
`.gemini/settings.json`. Each event contains matcher groups and command
handlers. `timeout` is milliseconds and defaults to 60000. Groups may run
sequentially or in parallel. Hooks communicate with JSON over stdin/stdout;
stdout must contain only the final JSON object.

Exit `0` parses JSON, `2` blocks according to the event, and other nonzero codes
warn and continue. Several lifecycle events are advisory or best-effort and
ignore flow control. Do not apply `BeforeTool` blocking semantics to
`SessionStart`, `SessionEnd`, `Notification`, or `PreCompress`. Use `/hooks`
to list and temporarily disable handlers. Review repository hooks and enable
environment-variable redaction where sensitive inherited values are possible.

Copy the asset to `.gemini/settings.json`, copy the handler to
`.agent-hooks/observe.py`, trigger a new isolated session, inspect `/hooks`, and
remove only the added matcher group to roll back.
