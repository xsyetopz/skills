# Codex hooks

Codex only. Facts from the [Codex hooks page][ref], fetched 2026-09-25, and the generated schemas at
tag `rust-v0.157.0` of `openai/codex` (`codex-rs/hooks/schema/generated/`). The page warns that
`main` schemas can run ahead of a release: use the tag of the installed `codex --version`.

## Contents

- [Locations and trust](#locations-and-trust)
- [Config shape](#config-shape)
- [Matchers](#matchers)
- [PreToolUse decision](#pretooluse-decision)
- [Stop continuation](#stop-continuation)
- [SessionStart](#sessionstart)

## Locations and trust

Codex reads `hooks.json`, or `[hooks]` tables in `config.toml`, next to each active config layer:
`~/.codex/` and `<repo>/.codex/`. All sources load; no layer replaces another. Project hooks load
only when the project `.codex/` layer is trusted, and every non-managed hook must be reviewed in
`/hooks`. Trust is recorded against the hook's hash, so any edit sends the hook back to review. A
hook that "never runs" is usually awaiting review. Do not use `--dangerously-bypass-hook-trust`
outside automation that vets hooks another way.

## Config shape

- Three levels: event, matcher group, handlers.
- `command` and `mcp_tool` handlers run. `prompt` and `agent` handlers are parsed and skipped.
- `timeout` is in seconds, default 600. `SessionEnd` and `Interrupt` default to 1 and allow at
  most 3.
- Commands run in the session `cwd`, which can be a subdirectory, so `.codex/hooks/x.py` can be
  missing. Resolve from the git root:

```sh
python3 "$(git rev-parse --show-toplevel)/.codex/guard_shell.py"
```

```toml
[[hooks.PreToolUse]]
matcher = "^Bash$"
[[hooks.PreToolUse.hooks]]
type = "command"
command = 'python3 "$(git rev-parse --show-toplevel)/.codex/guard_shell.py"'
timeout = 10
```

Keep one form per layer: with both, Codex merges them and warns.

## Matchers

Matchers are regexes, and not every event uses them:

- tool name: `PreToolUse`, `PostToolUse`, `PermissionRequest`;
- source (`startup|resume|clear|compact`): `SessionStart`;
- trigger (`manual|auto`): `PreCompact`, `PostCompact`;
- ignored: `UserPromptSubmit`, `Stop`, `Interrupt`.

Shell commands match as `Bash`. `apply_patch` also matches `Edit` and `Write`. Hosted tools such as
`WebSearch` never reach tool hooks.

## PreToolUse decision

Deny with `hookSpecificOutput.permissionDecision: "deny"` and a reason. The legacy
`{"decision": "block"}` and exit 2 with stderr also deny. Plain stdout is ignored. `updatedInput` is
allowed only with `"allow"`, and Bash and `apply_patch` need a string `command` in it.

Parsed but unsupported: `"ask"`, legacy `"approve"`, `continue: false`, `stopReason`,
`suppressOutput`. Codex marks such a run failed and continues the tool call, so a Claude `"ask"`
hook ported here lets the call through. Cursor-style `permission` fields are rejected by the output
schema.

## Stop continuation

A `Stop` hook must print JSON on exit 0: plain text is invalid. `{"decision": "block", "reason": R}`
continues the turn with R as a new user prompt. `continue: false` from any Stop hook overrides
continuation. The input includes `stop_hook_active` and `last_assistant_message`. Print `{}` to let
the turn end.

## SessionStart

Plain stdout or `hookSpecificOutput.additionalContext` becomes developer context.
`additionalContextLimit` on the handler caps what is sent, and the full text is saved to disk. Hooks
matching `compact` run before the next model request after compaction. Static text belongs in
`AGENTS.md`.

[ref]: https://developers.openai.com/codex/hooks
