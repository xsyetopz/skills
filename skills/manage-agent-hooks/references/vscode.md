# VS Code agent hooks

Reviewed 2026-09-12 against the official [VS Code agent hooks
documentation](https://code.visualstudio.com/docs/agent-customization/hooks).
The feature is Preview; recheck the installed VS Code version and documentation
before changing configuration.

Workspace hooks live in `.github/hooks/*.json`; user hooks default to
`~/.copilot/hooks`. VS Code can also read Claude-format locations and
agent-scoped hooks. Native VS Code files use PascalCase events such as
`SessionStart`, `PreToolUse`, and `PostToolUse`. Commands receive JSON on stdin
and may return event-specific JSON. Exit `0` succeeds, `2` blocks where the
event supports blocking, and other nonzero codes warn and continue.

The extension-host platform selects OS-specific command overrides, which may be
remote rather than local. Workspace Trust and organization policy can prevent
execution. VS Code currently ignores matcher values imported from Claude files,
so cross-loading can broaden execution. Do not claim Claude/Copilot parity from
format compatibility.

Copy the asset to `.github/hooks/observe.json` and the handler to
`.agent-hooks/observe.py`. Use **Developer: Show Agent Debug Logs** after a new
isolated session. Delete the added files to roll back; configuration parsing
does not replace this real-host check.
