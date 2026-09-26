# Copilot, VS Code, and OpenCode hooks

Facts from the [GitHub Copilot hooks reference][copilot], the
[VS Code agent hooks page][vscode] (Preview), and the
[OpenCode plugins page][opencode], all fetched on 2026-09-25. None of
these hosts runs here. `bun test` executes the OpenCode plugin
directly, and it is type-checked against `@opencode-ai/plugin@1.18.32`.

## Contents

- Copilot: locations and file format
- Copilot: payload shapes and matchers
- Copilot: preToolUse decision and exit codes
- Copilot cloud agent constraints
- VS Code Local hooks and shared .github/hooks
- OpenCode plugin hooks
- OpenCode V2 plugin API

## Copilot: locations and file format

**Definition.** Copilot CLI loads hook sources in this order and runs
all of them:

- policy: `/etc/github-copilot/policy.d/*.json`, root-owned; cannot be
  disabled;
- user: `~/.copilot/hooks/*.json`;
- repository: `.github/hooks/*.json`;
- inline `hooks` in `.github/copilot/settings.json` or
  `~/.copilot/settings.json`;
- plugins.

A file has `{"version": 1, "hooks": {...}}`. A command entry has
`bash`, `powershell`, or `command`; `cwd`; `env`; and `timeoutSec`.
Copilot CLI also supports `exec` plus `args`, which runs with no shell.

**Use when.** Wiring Copilot CLI or cloud agent hooks.

**Do not use when.** Relying on `exec`/`args` or `powershell` in the
cloud agent. It honors only `bash`, falling back to `command`.

**Example.** [`assets/config/copilot/.github/hooks/guard.json`][asset]:

```json
{"version": 1, "hooks": {"preToolUse": [{"type": "command",
 "bash": "python3 .agent-hooks/guard_shell.py --host copilot",
 "matcher": "bash", "timeoutSec": 10}]}}
```

**Cost removed.** Hooks that run locally but not in the cloud.

**Verify.**

1. `check_hook_config.py .github/hooks/guard.json --host copilot
   --project .` reports `0 error(s)`.

## Copilot: payload shapes and matchers

**Definition.** Copilot accepts two event naming styles, and each sends
a different payload:

| Event name style | Payload |
| --- | --- |
| camelCase (`preToolUse`) | `toolName` (`bash`, `view`, `edit`, ...), `toolArgs` |
| PascalCase (`PreToolUse`) | snake_case, as VS Code uses: `tool_name` with Claude names (`Bash`, `Read`, `Edit`), `tool_input` |

Matchers are compiled as `^(?:PATTERN)$`, so they must match the whole
tool name. PascalCase events use Claude's matcher semantics.

**Use when.** Choosing an event name and a matcher.

**Do not use when.** Writing `"matcher": "Bash"` on a camelCase event.
The runtime tool name there is `bash`, so the matcher never matches.

**Example.** The guard reads both shapes: `copilot` handles camelCase
events, and `copilot-pascal` the PascalCase fixture. It parses the
camelCase `toolArgs` string as JSON. From
`assets/handlers/guard_shell.py`:

```python
def shell_command(host: str, event: dict) -> str | None:
    """Return the shell command, or None when the tool is not a shell."""
    if host == "copilot" and "toolName" in event:
        tool, args = event.get("toolName"), event.get("toolArgs")
        if isinstance(args, str):  # toolArgs may arrive as a JSON string
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                raise BadEvent("toolArgs is not JSON") from None
    else:
        tool, args = event.get("tool_name"), event.get("tool_input")
    names = SHELL_TOOLS[host]
    if host == "copilot" and "toolName" not in event:
        # VS Code's Local harness also loads .github/hooks/*.json and sends
        # its own snake_case payload; tool names then follow that host.
        names = None
    if not isinstance(tool, str):
        raise BadEvent("missing tool name")
    if names is not None and tool not in names:
        return None
    if not isinstance(args, dict):
        return None
    command = args.get("command")
    return command if isinstance(command, str) else None
```

**Cost removed.** Guards that read the wrong fields and exit 2 on every
call, which for `preToolUse` denies everything.

**Verify.**

1. `GuardTests` pass for `copilot` and `copilot-pascal`.

## Copilot: preToolUse decision and exit codes

**Definition.**

- Output: `permissionDecision` (`allow`, `deny`, or `ask`),
  `permissionDecisionReason` (required for deny), and `modifiedArgs`.
- Exit 2 denies `preToolUse` and `permissionRequest`, and is a warning
  elsewhere.
- For `preToolUse`, any other nonzero exit also denies ("hook
  errored"), so the event fails closed.
- Timeouts fail open for every event, including policy hooks.
- In the cloud agent, `ask` becomes `deny`.

**Use when.** Blocking tool calls.

**Do not use when.** The guard does slow I/O. A timeout lets the call
through.

**Example.** The guard's deny output:

```json
{"permissionDecision": "deny",
 "permissionDecisionReason": "Blocked by guard_shell (force push): ..."}
```

**Cost removed.** Bypass through slow checks. Keep the handler fast,
with no network.

**Verify.**

1. Time the handler on its fixture with
   `time python3 guard_shell.py --host copilot < fixture`. It finishes
   well under `timeoutSec`.

## Copilot cloud agent constraints

**Definition.** The cloud agent runs hooks in an ephemeral Linux
sandbox:

- working directory `/workspace`;
- restricted outbound network;
- non-interactive, with all tools pre-approved;
- only `.github/hooks/*.json` from the cloned repository is loaded;
- `GITHUB_COPILOT_API_TOKEN` and `GITHUB_COPILOT_GIT_TOKEN` are in the
  environment.

**Use when.** A hook must hold for cloud agent jobs.

**Do not use when.** The hook depends on user-level files, a local
network, or logs you expect to keep. The sandbox filesystem is
discarded when the job ends.

**Example.** The guard needs only `python3` and the repository file,
and it neither logs nor sends anything. The whole file,
[`assets/config/copilot/.github/hooks/guard.json`][asset]:

```json
{
  "version": 1,
  "hooks": {
    "preToolUse": [
      {
        "type": "command",
        "bash": "python3 .agent-hooks/guard_shell.py --host copilot",
        "matcher": "bash",
        "timeoutSec": 10
      }
    ]
  }
}
```

**Cost removed.** Leaked tokens and hooks that cannot run in the cloud.

**Verify.**

1. A cloud agent run shows the deny in its log. Not run here: it needs
   a cloud job.

## VS Code Local hooks and shared .github/hooks

**Definition.** VS Code's Local harness reads the following locations,
subject to Workspace Trust and the `chat.useHooks` setting:

- `.github/hooks/*.json` and `~/.copilot/hooks/*.json`;
- Claude-format `.claude/settings.json`, `.claude/settings.local.json`,
  and `~/.claude/settings.json`, with `chat.useClaudeHooks`.

The native format is PascalCase with no `version`. VS Code reads a file
that has `version` as a Copilot file: it maps the file but sends its
own Local payload. For Claude-format files, the Local harness ignores
matcher values, so every command for the event runs.

Local events: `SessionStart`, `UserPromptSubmit`, `PreToolUse`,
`PostToolUse`, `PreCompact`, `SubagentStart`, `SubagentStop`, `Stop`.

**Use when.** Hooks for VS Code's Local agent.

**Do not use when.** Assuming one `.github/hooks` file behaves the same
in Copilot CLI and VS Code. Both read it, but send different payloads,
and VS Code ignores Claude-format matchers.

**Example.** [`assets/config/vscode/.github/hooks/guard.json`][vs-asset]
uses the native format, with a `windows` override. The guard's
`copilot` adapter also accepts the VS Code payload
(`test_copilot_adapter_accepts_vscode_payload`). The page does not list
Local tool names; read them from **Developer: Show Agent Debug Logs**.
So the VS Code fixture's tool name is a placeholder, and the vscode
adapter checks any tool with a string `command`. From
`assets/config/vscode/.github/hooks/guard.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "type": "command",
        "command": "python3 .agent-hooks/guard_shell.py --host vscode",
        "windows": "py -3 .agent-hooks\\guard_shell.py --host vscode",
        "timeout": 10
      }
    ]
  }
}
```

**Cost removed.** A Claude hook with `"matcher": "Bash"` that runs for
every tool in VS Code.

**Verify.**

1. `check_hook_config.py FILE --host vscode` warns when the file has a
   `version`.
1. The debug log shows the hook for the right tool. Not run here.

## OpenCode plugin hooks

**Definition.** OpenCode has plugins, not JSON hooks. A plugin is a
JS/TS module whose exported async function returns hook handlers.

- Load order: `~/.config/opencode/opencode.json` (`"plugin"` list),
  project `opencode.json`, `~/.config/opencode/plugins/`, then
  `.opencode/plugins/`.
- Throwing from `"tool.execute.before"` stops the call.
- The event list includes `tool.execute.before`/`after`,
  `session.idle`, `file.edited`, `permission.asked`, and `shell.env`.
- Local plugins that need packages declare them in
  `.opencode/package.json`, which OpenCode installs with Bun at
  startup.

**Use when.** Guarding or observing tools in OpenCode.

**Do not use when.** The guard needs undeclared dependencies at run
time. Keep the plugin dependency-free, or declare the packages.

**Example.** [`assets/opencode/guard.ts`][oc]:

```ts
export const GuardPlugin: Plugin = async () => ({
  "tool.execute.before": async (input, output) => {
    if (input.tool !== "bash") return;
    const command = String(output.args?.command ?? "");
    for (const [label, pattern] of DENY) {
      if (pattern.test(command)) {
        const shown = command.slice(0, 200);
        throw new Error(`Blocked by guard (${label}): ${shown}`);
      }
    }
  },
});
```

**Cost removed.** Destructive shell calls in OpenCode sessions.
`bun test` calls the hook directly: the force push throws, and other
commands pass.

**Verify.**

1. `bun test` in `assets/opencode` passes (2 tests).
1. `verify.sh network` type-checks against the published hook signature
   `(input: {tool, sessionID, callID}, output: {args: any})`.

## OpenCode V2 plugin API

**Definition.** The V2 docs define plugins with `Plugin.define(...)`,
and register hooks with `ctx.tool.hook(name, ...)`, where `name` is
`"execute.before"` or `"execute.after"`.
Plugins are listed under `plugins` (plural) in `opencode.json(c)`. The
V2 page states that OpenCode 1.18.29 supports the V1 object form.

**Use when.** The installed OpenCode is V2.

**Do not use when.** Mixing the V1 `"plugin"` config key and the V2
`plugins` key, or V1 hook names and V2 hook names, in one plugin.

**Example.** From the V2 page:

```ts
await ctx.tool.hook("execute.before", (event) => {
  if (event.tool === "read") console.log(event.input);
});
```

Verification tier: not runnable here. The V2 package was neither
installed nor type-checked.

**Cost removed.** Plugins written for the wrong major version.

**Verify.**

1. Run `opencode --version` before choosing the API.

[copilot]: https://docs.github.com/en/copilot/reference/hooks-reference
[vscode]: https://code.visualstudio.com/docs/agent-customization/hooks
[opencode]: https://opencode.ai/docs/plugins/
[asset]: ../assets/config/copilot/.github/hooks/guard.json
[vs-asset]: ../assets/config/vscode/.github/hooks/guard.json
[oc]: ../assets/opencode/guard.ts
