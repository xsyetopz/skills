# Codex hooks

Facts from the [Codex hooks page][ref], fetched on 2026-09-25, and the
generated schemas at tag `rust-v0.157.0`, vendored in
`assets/schemas/codex-0.157.0/`. The installed CLI is
`codex-cli 0.157.0`. The page warns that `main`-branch schemas can run
ahead of a release, so use the schemas for the installed release.

## Contents

- Locations and trust review
- Config shape and TOML form
- Matcher support per event
- PreToolUse decision
- Stop continuation
- SessionStart context
- Validating against the generated schemas

## Locations and trust review

**Definition.** Codex reads `hooks.json`, or `[hooks]` tables in
`config.toml`, next to each active config layer:

- `~/.codex/hooks.json`
- `~/.codex/config.toml`
- `<repo>/.codex/hooks.json`
- `<repo>/.codex/config.toml`

All sources load; no layer replaces another. Project hooks load only
when the project `.codex/` layer is trusted, and every non-managed hook
must also be reviewed and trusted in `/hooks`. Trust is recorded
against the hook's hash, so any edit sends the hook back to review.

**Use when.** Installing a project or user hook.

**Do not use when.** Reaching for `--dangerously-bypass-hook-trust`
outside automation that vets hooks another way.

**Example.** [`assets/config/codex/.codex/hooks.json`][asset],
installed into a scratch project with the handlers, and checked from
the skill root:

```sh
P=$(mktemp -d)
cp -R assets/config/codex/. "$P/"
mkdir "$P/.agent-hooks" && cp assets/handlers/*.py "$P/.agent-hooks/"
python3 scripts/check_hook_config.py "$P/.codex/hooks.json" \
  --host codex --project "$P" | tail -n 1
```

```text
0 error(s), 0 warning(s)
```

**Cost removed.** Hooks that silently do not run. Codex prints a
startup warning that points to `/hooks` when hooks need review.

**Verify.**

1. `check_hook_config.py .codex/hooks.json --host codex --project .`
   reports `0 error(s)`.
1. `/hooks` shows the hook as trusted. Not run here.

## Config shape and TOML form

**Definition.** Three levels: event, then matcher group, then
handlers.

- `command` and `mcp_tool` handlers run. `prompt` and `agent` handlers
  are parsed and skipped.
- `timeout` is in seconds. The default is 600. `SessionEnd` and
  `Interrupt` default to 1 s and allow at most 3 s.
- Commands run in the session `cwd`. Resolve repository scripts from
  the git root.

**Use when.** Writing either form. Keep one form per layer: when a
layer has both, Codex merges them and warns.

**Do not use when.** Using a relative path such as `.codex/hooks/x.py`.
Codex can start in a subdirectory, where that path does not exist.

**Example.** The command, which is one line in the file:

```sh
python3 "$(git rev-parse --show-toplevel)/.agent-hooks/guard_shell.py" \
  --host codex
```

In JSON, as in [`assets/config/codex/.codex/hooks.json`][asset], with
the command abbreviated as `CMD`:

```json
{"matcher": "^Bash$",
 "hooks": [{"type": "command", "command": "CMD", "timeout": 10}]}
```

The same entry in TOML:

```toml
[[hooks.PreToolUse]]
matcher = "^Bash$"
[[hooks.PreToolUse.hooks]]
type = "command"
command = 'CMD'
timeout = 10
```

**Cost removed.** Hooks that fail only when the session starts in a
subdirectory.

**Verify.**

1. `check_hook_config.py` warns about prompt and agent handlers, and
   rejects a `SessionEnd` timeout above 3.

## Matcher support per event

**Definition.** Matchers are regexes, and not every event uses them:

- tool name: `PreToolUse`, `PostToolUse`, `PermissionRequest`;
- source (`startup|resume|clear|compact`): `SessionStart`;
- trigger (`manual|auto`): `PreCompact` and `PostCompact`;
- ignored: `UserPromptSubmit`, `Stop`, `Interrupt`.

Shell commands match as `Bash`. `apply_patch` also matches `Edit` and
`Write`. Hosted tools such as `WebSearch` never reach tool hooks.

**Use when.** Filtering tool hooks.

**Do not use when.** Expecting a matcher on `Stop` to filter anything.
Codex ignores it.

**Example.** `"^Bash$"` for the guard, and `"Edit|Write"` for patch
review. A matcher on `Stop`, checked from the skill root:

```sh
cat > stop.json <<'JSON'
{"hooks": {"Stop": [{"matcher": "x",
  "hooks": [{"type": "command", "command": "true"}]}]}}
JSON
python3 scripts/check_hook_config.py stop.json --host codex
rm stop.json
```

```text
stop.json: warning: Stop: codex ignores matcher on this event
0 error(s), 1 warning(s)
```

**Cost removed.** Filters that silently do nothing.
`check_hook_config.py` warns: "codex ignores matcher on this event".

**Verify.**

1. `test_codex_ignores_stop_matcher_and_skips_prompt` passes.

## PreToolUse decision

**Definition.** Deny with
`hookSpecificOutput.permissionDecision: "deny"` and a reason. The
legacy `{"decision": "block"}`, and exit 2 with stderr, also deny.
`updatedInput` is allowed only together with `"allow"`, and Bash and
`apply_patch` need a string `command` in it. Plain stdout is ignored.

The following are parsed but not supported: `"ask"`, legacy
`"approve"`, `continue: false`, `stopReason`, `suppressOutput`. Codex
marks such a run as failed and continues the tool call.

**Use when.** Blocking or rewriting a shell command, a patch, or an
MCP call.

**Do not use when.** You want Codex to prompt the user. `"ask"` is not
supported and the call proceeds.

**Example.** The guard's Codex output validates against
`pre-tool-use.command.output.schema.json`. From the skill root:

```sh
python3 assets/handlers/guard_shell.py --host codex \
  < assets/fixtures/codex-pretooluse.json |
  python3 scripts/validate_schema.py \
  assets/schemas/codex-0.157.0/pre-tool-use.command.output.schema.json -
```

```text
valid
```

**Cost removed.** A Claude `"ask"` hook ported to Codex, where it lets
the call through.

**Verify.**

1. `test_codex_input_and_output_match_schemas` passes.

## Stop continuation

**Definition.** A `Stop` hook must print JSON on exit 0. Plain text is
invalid. `{"decision": "block", "reason": R}` continues the turn with R
as a new user prompt. `continue: false` from any Stop hook overrides
continuation. The input includes `stop_hook_active` and
`last_assistant_message`.

**Use when.** A check must pass before the turn ends.

**Do not use when.** The handler prints human-readable text. Codex
rejects that for Stop.

**Example.** `stop_gate.py` prints `{}` or a block object, never plain
text. A passing check, then a failing one validated against the
schema, from the skill root:

```sh
python3 assets/handlers/stop_gate.py --check true \
  < assets/fixtures/codex-stop.json
python3 assets/handlers/stop_gate.py --check false \
  < assets/fixtures/codex-stop.json |
  python3 scripts/validate_schema.py \
  assets/schemas/codex-0.157.0/stop.command.output.schema.json -
```

```text
{}
valid
```

**Cost removed.** Invalid-output errors from a Stop hook.

**Verify.**

1. The stop-gate output validates against `stop.command.output.schema.json`
   (`test_blocks_when_check_fails_and_output_is_schema_valid`).

## SessionStart context

**Definition.** Plain stdout, or
`hookSpecificOutput.additionalContext`, becomes developer context.
`additionalContextLimit` on the handler caps what is sent, and the full
text is saved to disk. After compaction, hooks that match `compact`
run before the next model request.

**Use when.** The repository facts change per session.

**Do not use when.** The context is static. Put it in `AGENTS.md`
(`$write-agents-md`).

**Example.** `session_context.py`. Its output validates against
`session-start.command.output.schema.json`. In a new repository with
one untracked file, from the skill root:

```sh
git -c init.defaultBranch=main init -q demo && touch demo/new.txt
printf '{"hook_event_name": "SessionStart", "cwd": "demo"}' |
  python3 assets/handlers/session_context.py |
  python3 scripts/validate_schema.py \
  assets/schemas/codex-0.157.0/session-start.command.output.schema.json -
rm -rf demo
```

```text
valid
```

**Cost removed.** Discovery turns.

**Verify.**

1. `test_reports_branch_and_changed_files` passes.

## Validating against the generated schemas

**Definition.** Codex publishes JSON Schemas for the input and output
of each command hook. `scripts/validate_schema.py` checks documents
against them. It supports exactly the draft-07 keywords that these
files use, and refuses any other keyword with exit 2.

**Use when.**

- Writing a Codex handler.
- Updating the vendored schemas for a new release.

**Do not use when.** Validating another host's payload. The other
hosts publish no equivalent schema set, so use their docs' examples as
fixtures.

**Example.**

```sh
python3 scripts/validate_schema.py \
  assets/schemas/codex-0.157.0/pre-tool-use.command.input.schema.json \
  assets/fixtures/codex-pretooluse.json      # valid
```

To update, download the files from `codex-rs/hooks/schema/generated/`
at tag `rust-v<VERSION>` of the `openai/codex` repository, into
`assets/schemas/codex-<VERSION>/`.

**Cost removed.** Output fields that Codex rejects at run time, such
as `permission`, which is flagged as an unexpected property.

**Verify.**

1. `verify.sh` validates the three fixtures and the guard output.

[ref]: https://developers.openai.com/codex/hooks
[asset]: ../assets/config/codex/.codex/hooks.json
