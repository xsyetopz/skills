---
name: create-agent-hooks
description: >-
  Creates, debugs, and audits coding-agent hooks for Claude Code, Codex,
  Gemini CLI, Cursor, Copilot, VS Code, and OpenCode: events, decision output,
  exit codes, Stop gates. Use when a hook should block, allow, or add context.
  Not for Git hooks.
---

# Create Agent Hooks

Write a hook for one host at a time, using that host's exact event
name, payload fields, and decision shape. Parse the payload as
untrusted input, and treat the hook as a guardrail behind the host's
permission system. Every bundled handler runs on fixtures copied from
the hosts' docs, and the Codex payloads and outputs validate against the
published 0.157.0 schemas.

## Workflow

1. Identify the host and its version (`claude --version`,
   `codex --version`, ...). Find the target file for the scope: user,
   project, local, or managed. Read the existing file, and keep
   everything in it.
1. Pick the event by its authority: observe, add context, modify, or
   block ([authority][authority]). If the requirement is a hard
   boundary, put it in permissions or the sandbox first
   ([guardrail][guardrail]).
1. Write the handler:
   - read stdin with a size limit, and use documented fields only;
   - exit 2 on unreadable input when the hook is a policy
     ([parsing][parsing], [failure policy][failure]);
   - emit the host's own deny shape;
   - print no decision when the hook has no opinion
     ([deny and allow][decision]).
1. Build a fixture from the host doc's example payload. Test deny,
   no-decision, a non-matching tool, and malformed input. For Codex,
   validate both the fixture and the output with
   `scripts/validate_schema.py`.
1. Reference scripts through the host's root variable
   ([paths][paths]). Merge the one entry with `scripts/merge_hooks.py`,
   then run `scripts/check_hook_config.py --project`.
1. Test in the host if it is available and the user agrees to a model
   session: `/hooks` lists the entry, and a triggering action shows the
   decision. Otherwise report the host run as not run.
1. Report: the file, the entry, the fixture results, the checker
   output, the rollback command (`merge_hooks.py ... --remove`), and
   what was not run.

## Route the task to a card

| Task | Card |
| --- | --- |
| Block dangerous shell commands | [Deny/allow][decision], host PreToolUse cards below |
| "Hook doesn't fire" | [Config check][check], matcher cards per host |
| "Hook fires but doesn't block" | [Authority][authority], [failure policy][failure] |
| Don't finish until tests pass | [Stop gate][stop] |
| Add branch or issue context at start | [Session context][context] |
| Install into existing settings, or undo | [Install and roll back][install] |
| Hook needs tokens or logs payloads | [Environment and secrets][secrets] |
| Claude Code specifics | [Claude Code](references/claude-code.md) |
| Codex specifics, schemas, trust | [Codex](references/codex.md) |
| Gemini CLI or Cursor | [Gemini and Cursor](references/gemini-and-cursor.md) |
| Copilot CLI/cloud, VS Code, OpenCode | [Copilot, VS Code, OpenCode][cvo] |

## Rules

- Use only event names, fields, and outputs from the host's own
  reference. Formats are not interchangeable: Cursor uses `preToolUse`,
  Claude uses `PreToolUse`, and Gemini uses `BeforeTool`.
- A hook is not the only control for a hard security requirement,
  because a hook runs only on the paths where the host fires it. Pair it
  with permission, sandbox, or policy settings.
- Policy hooks exit 2 on bad input or crash paths. On Claude Code and
  Gemini, exit 1 lets the action through.
- A "no opinion" answer is no decision, never `allow`. `allow` skips
  prompts on Claude Code.
- Never execute payload text, never log the environment, and never
  send the payload anywhere without an explicit requirement.
- Merge one entry into existing files, and remove only that entry to
  roll back. Do not overwrite settings or managed files.
- Keep policy handlers fast and offline. Timeouts fail open on Claude
  Code (`PreToolUse` command hooks) and on Copilot.
- A static check and fixture tests do not show that the host loaded the
  hook; report the host run as run or not run.

## Bundled tools

- `assets/handlers/guard_shell.py --host HOST [--deny REGEX]` is a
  pre-tool guard with adapters for the `claude`, `codex`, `gemini`,
  `cursor`, `copilot`, `copilot-pascal`, and `vscode` shapes.
- `assets/handlers/stop_gate.py --check CMD` is a Stop gate for Claude
  Code and Codex, with a loop guard.
- `assets/handlers/session_context.py` adds the branch and changed
  files at SessionStart.
- `assets/opencode/guard.ts` is an OpenCode plugin (v1 API), with
  `guard.test.ts`.
- `assets/config/<host>/...` holds a wiring example for each host.
  `assets/fixtures/` holds the payloads from each host's docs.
- `assets/schemas/codex-0.157.0/` holds the Codex input and output
  schemas.
- `scripts/check_hook_config.py FILE --host H [--project DIR] [--json]`
  checks events, handler types, matchers, timeout units, and script paths.
- `scripts/merge_hooks.py FILE --host H --event E --handler JSON
  [--matcher M] [--remove] [--dry-run] [--json]` installs or rolls back
  one entry.
- `scripts/validate_schema.py SCHEMA DOC [--json]` is a draft-07 subset
  validator that refuses keywords it does not support.
- `sh assets/verify.sh [network]` runs everything. The `network` mode
  also type-checks the OpenCode plugin.

## References

- [Hook design across hosts](references/hook-design.md)
- [Claude Code](references/claude-code.md)
- [Codex](references/codex.md)
- [Gemini CLI and Cursor](references/gemini-and-cursor.md)
- [Copilot, VS Code, and OpenCode][cvo]

## Completion evidence

- Host, version, scope, and file. The merged entry, shown as the diff
  from `merge_hooks.py --dry-run`.
- Fixture results for deny, no-decision, a non-matching tool, and
  malformed input. For Codex, the schema validation output.
- `check_hook_config.py` output with 0 errors, and each warning
  explained.
- The rollback command, and the permission or sandbox rule that backs
  any security claim.
- Host runs marked done or not run, with the reason.

## Stop and ask

- The hook would change managed or policy files.
- Running the host needs a model session or account the user has not
  approved.
- The host version predates a field the design needs, such as exec
  form or `defer`.

[authority]: references/hook-design.md#event-authority-observe-modify-or-block
[guardrail]: references/hook-design.md#guardrail-not-enforcement-boundary
[parsing]: references/hook-design.md#untrusted-input-parsing
[failure]: references/hook-design.md#fail-open-or-fail-closed
[decision]: references/hook-design.md#deny-allow-and-no-decision
[paths]: references/hook-design.md#script-path-resolution
[check]: references/hook-design.md#configuration-check-before-the-host-loads-it
[stop]: references/hook-design.md#stop-gate-with-a-loop-guard
[context]: references/hook-design.md#session-context-injection
[install]: references/hook-design.md#install-and-roll-back-one-entry
[secrets]: references/hook-design.md#environment-and-secrets
[cvo]: references/copilot-vscode-opencode.md
