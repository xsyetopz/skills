# Configure Gemini CLI coding-agent event hooks

Original source note dated 2026-09-12, referring to the official [Gemini CLI
hooks reference][ref-gemini-cli-hooks-reference] and [configuration
reference][ref-configuration-reference].

Hooks are under `hooks` in `settings.json`; project scope uses
`.gemini/settings.json`. Each event contains matcher groups and command
handlers. `timeout` is milliseconds and defaults to 60000. Groups may run
sequentially or in parallel. Hooks communicate with JSON over stdin/stdout;
stdout must contain only the final JSON object.

Exit `0` parses JSON, `2` blocks according to the event, and other nonzero codes
warn and continue. Several lifecycle events are advisory or best-effort and
ignore flow control. Do not apply `BeforeTool` blocking semantics to
`SessionStart`, `SessionEnd`, `Notification`, or `PreCompress`. Use `/hooks` to
list and temporarily disable handlers. Review repository hooks and enable
environment-variable redaction where sensitive inherited values are possible.

Copy the asset to `.gemini/settings.json`, copy the handler to
`.agent-hooks/observe.py`, trigger a new isolated session, inspect `/hooks`, and
remove only the added matcher group to roll back.

Lifecycle matcher values are exact strings; tool matchers use the documented
regex semantics. Do not put `startup|resume` into a SessionStart matcher and
expect regex alternation. The supplied SessionStart fixture omits the matcher so
it applies to the event's startup modes without that false assumption.

[ref-gemini-cli-hooks-reference]: https://geminicli.com/docs/hooks/reference/
[ref-configuration-reference]: https://geminicli.com/docs/reference/configuration/
