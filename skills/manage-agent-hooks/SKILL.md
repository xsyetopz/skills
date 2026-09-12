---
name: manage-agent-hooks
description: >-
  Use only when explicitly invoked by name. Audit, install, test, update, or
  remove lifecycle hooks for supported coding-agent harnesses. Excludes Git
  hooks, editor extension events, prompts, MCP configuration, and unverified
  cross-provider schema translation.
---

# Manage Agent Hooks

Run this workflow only when the user explicitly invokes this skill by name.
Agent hooks execute code with the harness's privileges; repository hook files
are executable trust boundaries.

1. Detect the actual provider and installed version. Do not infer it from a
   similarly named configuration file. Select **project** or **user** scope
   explicitly before editing.
2. Read the matching current provider reference below and open its official
   lifecycle/schema documentation. Preserve its exact event names, matcher
   syntax, input/output, ordering, blocking, timeout, trust, and reload rules.
3. Review every invoked executable and argument. Check shell quoting, paths with
   spaces, inherited secrets, network and filesystem effects, destructive
   operations, untrusted input, recursion, concurrency, ordering, and timeout.
   Prefer direct executable/argument forms when the provider supports them.
4. Back up the exact existing configuration. Merge only the requested hook;
   preserve unrelated provider settings and higher-precedence managed policy.
5. Parse the resulting configuration with the provider's schema or parser.
   Trigger one harmless matching event in an isolated project. Verify received
   input, stdout JSON, stderr, exit behavior, timeout, and expected side effect.
6. Report the provider, version, scope, changed file, event, matcher, command,
   trust/approval step, observed test, and rollback. Restore the backup if the
   harmless test fails.

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

## RED / GREEN

**Deciding condition:** install a project-local observer for one documented
event without granting it additional authority.

### RED — DO NOT: assume one universal hook

```text
Put a post-tool hook with the same event and JSON in every agent.
```

The event spelling, nesting, command form, scope, trust, and exit semantics are
provider-specific.

### GREEN — DO: validate the selected provider

```text
Provider/version -> scope -> official event/schema -> command security review
-> merge -> parse -> harmless trigger -> rollback proof
```

Use the [harmless handler](assets/shared/observe.py), provider fixture payloads,
and matching configuration asset for local validation. The handler only parses
one JSON object and returns `{}`; it neither logs secrets nor writes files.

## Validation

Run `python3 scripts/test_assets.py`. A JSON parse and direct handler test do
not replace a real harness smoke test. Report unavailable provider binaries,
authentication, cloud execution, UI trust review, or preview-host checks rather
than claiming them from configuration parsing.
