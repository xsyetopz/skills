# Configure GitHub Copilot CLI and cloud-agent event hooks

Original source note dated 2026-09-12, referring to the official [GitHub Copilot
hooks reference][ref-github-copilot-hooks-reference].

Copilot CLI reads repository `.github/hooks/*.json`, user hook directories,
inline settings, and plugin hooks. Hook files use version `1` and lower-camel
event names. Direct `exec`/`args` avoids shell interpretation in CLI; cloud
agent honors Linux `bash` or `command` entries, not PowerShell. Project and user
sources are combined rather than replaced.

The cloud agent supports fewer events, runs non-interactively in an ephemeral
Linux sandbox, and has restricted outbound network. Its environment contains
Copilot tokens; never log or forward inherited variables. Policy hooks load
first and cannot be disabled by ordinary configuration. Exact payload, matcher,
output decision, and exit code behavior vary by event.

Copy the asset to a new `.github/hooks/observe.json`, copy the handler to
`.agent-hooks/observe.py`, and test first in a disposable local CLI repository.
A cloud-agent run is required to establish cloud behavior. Roll back by deleting
only those two added files.

[ref-github-copilot-hooks-reference]: https://docs.github.com/en/copilot/reference/hooks-reference
