---
name: maintain-agent-hooks
description: >-
  Audit, install, test, update, or remove coding-agent lifecycle hooks for Codex,
  Claude Code, and other agents. Not for Git hooks or editor events.
---

# Maintain Agent Hooks

Installing, removing, or executing a hook requires that exact requested effect.
Agent hooks execute code with the harness's privileges; repository hook files
are executable trust boundaries.

For an audit-only request, inspect configuration and invoked code, then report
findings and unverified provider behavior without installing, removing or
triggering hooks. Apply the mutation and smoke-test steps below only to an
authorized change. Reuse authorization already supplied for that effect; do
not ask again for each harmless check within it.

1. Detect the actual provider and installed version. Do not infer it from a
   similarly named configuration file. Select **project** or **user** scope
   explicitly before editing.
1. Read the matching current provider reference below and open its official
   lifecycle/schema documentation. Preserve its exact event names, matcher
   syntax, input/output, ordering, blocking, timeout, trust, and reload rules.
1. Review every invoked executable and argument. Check shell quoting, paths with
   spaces, inherited secrets, network and filesystem effects, destructive
   operations, untrusted input, recursion, concurrency, ordering, and timeout.
   Prefer direct executable/argument forms when the provider supports them.
1. Record the exact existing configuration. Merge only the requested hook;
   preserve unrelated provider settings and higher-precedence managed policy.
1. Parse the resulting configuration with the provider's schema or parser.
   Trigger one harmless matching event in an isolated project. Verify received
   input, stdout JSON, stderr, exit behavior, timeout, and expected side effect.
1. Report the provider, version, scope, changed file, event, matcher, command,
   trust step, observed test, and rollback. If the harmless test fails, remove
   only the entry and files introduced by the task; do not replace the current
   configuration with a broad backup.

## Provider routes

- [Codex](references/codex.md)
- [Claude Code](references/claude-code.md)
- [Gemini CLI](references/gemini-cli.md)
- [OpenCode](references/opencode.md)
- [Cursor](references/cursor.md)
- [GitHub Copilot CLI and cloud agent](references/github-copilot.md)
- [VS Code agent hooks](references/vscode.md)

Do not normalize configurations between providers. VS Code can read some
Claude-format files but currently differs in matcher behavior; a file accepted
by both does not imply identical execution.

Use the [harmless handler](assets/shared/observe.py), provider fixture payloads,
and matching configuration asset for local validation. The handler only parses
one JSON object and returns `{}`; it neither logs secrets nor writes files.

## Validation

Run `python3 scripts/test_assets.py`. A JSON parse and direct handler test do
not replace a real harness smoke test. Report unavailable provider binaries,
authentication, cloud execution, UI trust review, or preview-host checks rather
than claiming them from configuration parsing.
