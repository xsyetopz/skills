# MCP servers and debuggers

Cards for context servers (MCP) and Debug Adapter Protocol (DAP)
integrations. Runnable crates: [`mcp-server-memory/`][mcp-dir] runs
`@modelcontextprotocol/server-memory` on Zed's Node.js, and
[`lldb-dap-debugger/`][dap-dir] exposes LLVM's `lldb-dap` plus a locator
for `cc` and `clang` tasks. Both build for wasm32-wasip2 with
`zed_extension_api` 0.7.0, pass `clippy -D warnings`, and pass native
unit tests for their pure logic (Executed: 3 and 4 tests). Zed-side
behavior is Not runnable here: Zed is not installed.

## Contents

- [Context server registration](#context-server-registration)
- [context\_server\_configuration](#context_server_configuration)
- [Context server settings](#context-server-settings)
- [Removed extension kinds](#removed-extension-kinds)
- [Debug adapter registration](#debug-adapter-registration)
- [get\_dap\_binary](#get_dap_binary)
- [dap\_request\_kind](#dap_request_kind)
- [dap\_config\_to\_scenario](#dap_config_to_scenario)
- [Debug locators](#debug-locators)

## Context server registration

**Definition.** An empty `[context_servers.<id>]` table in
`extension.toml`, plus `fn context_server_command(&mut self, id:
&ContextServerId, project: &Project) -> Result<Command>`, which returns
the stdio command Zed starts for the Agent Panel ([MCP docs][mcp-docs],
[trait docs][trait-docs]). Zed plans to deprecate MCP server extensions
in favor of the official MCP registry, and the docs ask authors to
publish there too (tracking issue #59351).

**Use when.**

- The server ships as a binary or npm package and users should get it
  from the Zed extension store.

**Do not use when.**

- The server is remote (HTTP). Add it in Zed's MCP settings UI;
  extensions cover local command servers only ([MCP docs][mcp-docs]).
- The extension provides anything else. The prerequisites allow exactly
  one MCP server and nothing else, with an ID that starts with
  `mcp-server-` or ends with `-mcp-server` ([prerequisites][prereq]).

**Example.** Runnable: `assets/examples/mcp-server-memory/`.

```toml
[context_servers.mcp-server-memory]
```

```rust
fn context_server_command(
    &mut self,
    id: &ContextServerId,
    project: &Project,
) -> Result<zed::Command> {
    let latest = zed::npm_package_latest_version(PACKAGE)?;
    let installed = zed::npm_package_installed_version(PACKAGE)?;
    if installed.as_deref() != Some(latest.as_str()) {
        zed::npm_install_package(PACKAGE, &latest)?;
    }
    let settings = ContextServerSettings::for_project(id.as_ref(), project)?;
    let entry = env::current_dir()
        .map_err(|error| error.to_string())?
        .join(ENTRY);
    Ok(zed::Command {
        command: zed::node_binary_path()?,
        args: vec![entry.to_string_lossy().into_owned()],
        env: server_env(settings.settings.as_ref())?,
    })
}
```

**Cost removed.** Manual MCP setup for each user. The checker counts
violations of the one-server rule
(`an MCP extension ships one server only`).

**Verify.**

1. `check_extension.py --registry assets/examples/mcp-server-memory`
   prints `0 errors`. Executed.
1. In Zed, the Agent Panel lists `mcp-server-memory` as running (Not
   runnable here).

## context\_server\_configuration

**Definition.** `fn context_server_configuration(&mut self, id,
project) -> Result<Option<ContextServerConfiguration>>` returns
`installation_instructions` (Markdown), `settings_schema` (a JSON Schema
string), and `default_settings` (a JSON string), which Zed shows when
the user configures the server ([context-server.wit][wit-cs]).

**Use when.**

- The server has user-facing options, such as a file path, a token
  variable name, or a mode.

**Do not use when.**

- Putting secrets in `default_settings`. Defaults ship to every user;
  tell users where to put their own value.
- Returning a `serde_json::Value` where the record wants a string. Call
  `.to_string()` on the schema; the compiler catches the type error.

**Example.**

```rust
fn settings_schema() -> Value {
    json!({
        "type": "object",
        "properties": {
            "memory_file_path": {
                "type": "string",
                "description": "Absolute path of the JSONL memory file."
            }
        }
    })
}

Ok(Some(ContextServerConfiguration {
    installation_instructions: "Optional: set `memory_file_path` \
        to keep the graph outside the extension directory."
        .to_string(),
    settings_schema: settings_schema().to_string(),
    default_settings: "{}".to_string(),
}))
```

**Cost removed.** Guessing the settings shape: Zed validates the user's
settings against the schema. The unit test
`schema_documents_the_single_setting` pins the schema shape.

**Verify.**

1. `cargo test` passes 3 tests. Executed.
1. In Zed, the configure dialog shows the instructions and validates
   `memory_file_path` as a string (Not runnable here).

## Context server settings

**Definition.** `ContextServerSettings::for_project(id, project)`
returns `{ command, settings }` from the global `context_servers.<id>`
value, preferring a worktree value when one differs
([settings.rs][settings-rs]). `settings` is the user's free-form JSON
object.

**Use when.**

- Mapping user settings to the server's environment or arguments. For
  example, `memory_file_path` becomes `MEMORY_FILE_PATH`, which the
  server reads in `dist/index.js` (checked in the npm tarball
  2026.8.31).

**Do not use when.**

- Ignoring a value of the wrong type. Return an error.

**Example.**

```rust
fn server_env(settings: Option<&Value>) -> Result<Vec<(String, String)>> {
    let Some(path) = settings.and_then(|s| s.get("memory_file_path")) else {
        return Ok(Vec::new());
    };
    let path = path
        .as_str()
        .ok_or("`memory_file_path` must be a string")?;
    Ok(vec![("MEMORY_FILE_PATH".to_string(), path.to_string())])
}
```

User settings:

```json
{
  "context_servers": {
    "mcp-server-memory": {
      "settings": { "memory_file_path": "/Users/me/.mcp/memory.jsonl" }
    }
  }
}
```

**Cost removed.** A server that silently falls back to its default file
on an invalid setting; the user gets an error instead. The unit test
`rejects_a_non_string_path` covers it.

**Verify.**

1. `cargo test` passes `maps_memory_file_path_to_env` and
   `rejects_a_non_string_path`. Executed.
1. In Zed, the JSONL file appears at the configured path after the
   server first writes (Not runnable here).

## Removed extension kinds

**Definition.** Zed removed extension slash commands; the docs page
redirects to MCP servers ([slash commands][slash-docs]). The
`zed-extension` packager rejects any manifest with `slash_commands`
("Slash commands have been deprecated...") or
`language_model_providers` ([CLI][cli-rs]). Agent server (ACP)
extensions were deprecated in Zed v1.5.0 in favor of the ACP Registry,
and new submissions are not accepted ([agent servers][agent-docs],
[prerequisites][prereq]). The 0.7.0 crate keeps the slash-command trait
methods for older extensions.

**Use when.**

- A request asks for "a slash command extension" or "an agent server
  extension". Build an MCP server (see
  [Context server registration](#context-server-registration)) or
  publish to the ACP Registry.

**Do not use when.**

- Implementing `run_slash_command` in new code because the crate has
  it. Current Zed never calls it, and packaging fails.

**Example.** A manifest that `check_extension.py` rejects:

```toml
[slash_commands.echo]
description = "echoes its argument"
requires_argument = true
```

```text
ERROR extension.toml: slash commands were removed; use an MCP server
```

**Cost removed.** Building a feature that cannot be published; the
checker flags it before any Rust is written.

**Verify.**

1. `python3 scripts/test_check_extension.py` passes
   `test_slash_commands_are_rejected` (exit 1 on `[slash_commands.*]`).
   Executed.
1. The v1.21.0 docs source is titled "Slash Commands (Removed)"
   ([source][slash-docs]); read in this session. The live URL
   `https://zed.dev/docs/extensions/slash-commands` returned HTTP 404
   on 2026-09-25.

## Debug adapter registration

**Definition.** `[debug_adapters.<name>]` with an optional
`schema_path`, defaulting to `debug_adapter_schemas/<name>.json`. The
key is optional but the schema is mandatory ([debugger docs][dap-docs],
[manifest source][manifest-rs]); the packager fails if it cannot read
the schema file. `<name>` is the `adapter` value users write in
`debug.json`.

**Use when.**

- Exposing a DAP server that Zed does not build in.

**Do not use when.**

- Bundling the adapter binary. The prerequisites require downloading it
  or finding it in the user's environment.

**Example.** Runnable: `assets/examples/lldb-dap-debugger/`.

```toml
[debug_adapters.lldb-dap]
schema_path = "debug_adapter_schemas/lldb-dap.json"
```

The schema covers the `lldb-dap` launch and attach keys: `request`,
`program`, `args`, `cwd`, `env`, `stopOnEntry`, and `pid`
([lldb-dap README][lldb-dap]).

**Cost removed.** A packaging failure. `check_extension.py` parses each
schema as JSON and reports a missing or invalid file.

**Verify.**

1. `check_extension.py --registry assets/examples/lldb-dap-debugger`
   prints `0 errors`. Executed.
1. `python3 -m json.tool debug_adapter_schemas/lldb-dap.json` exits 0.
   Executed.

## get\_dap\_binary

**Definition.** `fn get_dap_binary(&mut self, adapter_name: String,
config: DebugTaskDefinition, user_provided_debug_adapter_path:
Option<String>, worktree: &Worktree) -> Result<DebugAdapterBinary>`.
`DebugAdapterBinary` fields: `command: Option<String>`, `arguments`,
`envs`, `cwd`, `connection` (TCP when `Some`, otherwise stdio), and
`request_args: StartDebuggingRequestArguments {
configuration, request }` ([dap.wit][wit-dap]). Zed calls it at every
debug session start.

**Use when.**

- Every registered debug adapter.

**Do not use when.**

- Ignoring `user_provided_debug_adapter_path`. When it is `Some`, use it
  first.
- Checking for adapter updates on every call. The function runs per
  session, so the docs ask for periodic checks only.

**Example.**

```rust
fn get_dap_binary(
    &mut self,
    _adapter_name: String,
    config: DebugTaskDefinition,
    user_provided_debug_adapter_path: Option<String>,
    worktree: &Worktree,
) -> Result<DebugAdapterBinary> {
    let parsed: Value = zed::serde_json::from_str(&config.config)
        .map_err(|error| format!("invalid configuration: {error}"))?;
    let command = match user_provided_debug_adapter_path {
        Some(path) => path,
        None => find_adapter(worktree)?,
    };
    Ok(DebugAdapterBinary {
        command: Some(command),
        arguments: Vec::new(),
        envs: Vec::new(),
        cwd: None,
        connection: None,
        request_args: StartDebuggingRequestArguments {
            request: request_kind(&parsed)?,
            configuration: config.config,
        },
    })
}
```

`find_adapter` tries `worktree.which("lldb-dap")`, then `xcrun -f
lldb-dap` on macOS (see
[Process execution capability][proc-cap]).

**Cost removed.** A session started with a malformed configuration:
invalid JSON fails before any process starts.

**Verify.**

1. `cargo build --release --target wasm32-wasip2` and `cargo clippy -D
   warnings` succeed. Executed.
1. In Zed, a `debug.json` entry with `"adapter": "lldb-dap"` stops at a
   breakpoint in `build/app` (Not runnable here).

## dap\_request\_kind

**Definition.** `fn dap_request_kind(&mut self, adapter_name: String,
config: serde_json::Value) -> Result<StartDebuggingRequestArgumentsRequest>`
returns `Launch` or `Attach`. Per the trait docs, it must return an
error when the kind is unclear, not fall back to a default
([trait docs][trait-docs]).

**Use when.**

- Every adapter. Zed uses the result to choose launch or attach and to
  decide whether a locator runs.

**Do not use when.**

- Defaulting to `Launch` when `request` is missing. That starts a
  process when the user meant to attach.

**Example.**

```rust
fn request_kind(config: &Value) -> Result<Kind> {
    match config.get("request").and_then(Value::as_str) {
        Some("launch") => Ok(Kind::Launch),
        Some("attach") => Ok(Kind::Attach),
        other => Err(format!(
            "`request` must be \"launch\" or \"attach\", got {other:?}"
        )),
    }
}
```

**Cost removed.** Launching a process by mistake. The unit test
`request_kind_rejects_missing_or_unknown_values` fixes the behavior for
a missing value and for `"run"`.

**Verify.**

1. `cargo test` passes the test. Executed.
1. In Zed, a `debug.json` entry without `request` shows the error
   instead of starting a process (Not runnable here).

## dap\_config\_to\_scenario

**Definition.** `fn dap_config_to_scenario(&mut self, config:
DebugConfig) -> Result<DebugScenario>` turns the adapter-neutral
`DebugConfig { label, adapter, request: Launch{program, cwd, args,
envs} | Attach{process_id}, stop_on_entry }` from the New Process modal
into a `DebugScenario` whose `config` is the adapter's own JSON
([dap.wit][wit-dap], [debugger docs][dap-docs]).

**Use when.**

- Users should start sessions from the UI without writing `debug.json`.
  The docs "strongly" recommend it.

**Do not use when.**

- Passing Zed's field names through unchanged. The adapter expects its
  own keys (`lldb-dap`: `program`, `args`, `cwd`, `env` as an object,
  `stopOnEntry`, and `pid`).

**Example.**

```rust
fn dap_config_to_scenario(
    &mut self,
    config: DebugConfig,
) -> Result<DebugScenario> {
    let adapter_config =
        adapter_config(&config.request, config.stop_on_entry);
    Ok(DebugScenario {
        label: config.label,
        adapter: config.adapter,
        build: None,
        config: adapter_config.to_string(),
        tcp_connection: None,
    })
}
```

The `adapter_config` helper in `src/lib.rs` builds
`{"request":"launch","program":..,"args":..,"env":{..},"cwd":..}` or
`{"request":"attach","pid":..}`.

**Cost removed.** Hand-written `debug.json` for common launches. The
unit tests `launch_maps_to_lldb_dap_keys` and
`attach_without_pid_omits_the_key` pin the key mapping.

**Verify.**

1. `cargo test` passes both tests. Executed.
1. In Zed, the New Process modal with the `lldb-dap` adapter starts
   `build/app` (Not runnable here).

## Debug locators

**Definition.** A `[debug_locators.<name>]` table plus two hooks.
`dap_locator_create_scenario(locator_name, build_task, resolved_label,
debug_adapter_name) -> Option<DebugScenario>` runs for every task and
returns `Some` only for tasks it understands. If the scenario has
`build: Some(...)`, Zed runs the build task and, after it succeeds,
calls `run_dap_locator(locator_name, build_task) ->
Result<DebugRequest>` to find the program ([debugger docs][dap-docs],
[trait docs][trait-docs]). Zed's built-in Cargo locator returns a null
config with a build task ([cargo.rs][cargo-locator]).

**Use when.**

- The language has tasks, such as a `cc`/`clang` compile or `cargo run`,
  that users should debug with one click.

**Do not use when.**

- The task is not yours. Return `None` fast: every task goes through
  every locator.
- The program path is known up front. Skip the build phase and return
  the full configuration from `dap_locator_create_scenario`.

**Example.**

```toml
[debug_locators.clang-build]
```

```rust
fn output_path(args: &[String]) -> Option<&str> {
    let at = args.iter().position(|arg| arg == "-o")?;
    args.get(at + 1).map(String::as_str)
}

fn is_c_compile(task: &TaskTemplate) -> bool {
    matches!(task.command.as_str(), "cc" | "clang")
        && output_path(&task.args).is_some()
}

fn run_dap_locator(
    &mut self,
    _locator_name: String,
    build_task: TaskTemplate,
) -> Result<DebugRequest> {
    let program = output_path(&build_task.args)
        .ok_or("build task has no -o output path")?;
    Ok(DebugRequest::Launch(LaunchRequest {
        program: program.to_string(),
        cwd: build_task.cwd,
        args: Vec::new(),
        envs: Vec::new(),
    }))
}
```

**Cost removed.** Hand-written debug configurations for compile tasks.
The test `locator_accepts_only_compiles_with_an_output` checks that
`make` tasks and `-c` compiles are rejected before any work.

**Verify.**

1. `cargo test` passes the locator test. Executed.
1. In Zed, the task `clang -g main.c -o app` offers "Debug" and starts
   `app` under `lldb-dap` (Not runnable here).

[mcp-dir]: ../assets/examples/mcp-server-memory/
[proc-cap]: manifest-and-build.md#process-execution-capability
[dap-dir]: ../assets/examples/lldb-dap-debugger/
[mcp-docs]: https://zed.dev/docs/extensions/mcp-extensions
[dap-docs]: https://zed.dev/docs/extensions/debugger-extensions
[slash-docs]: https://github.com/zed-industries/zed/blob/v1.21.0/docs/src/extensions/slash-commands.md
[agent-docs]: https://zed.dev/docs/extensions/agent-servers
[prereq]: https://zed.dev/docs/extensions/publishing/prerequisites
[trait-docs]: https://docs.rs/zed_extension_api/0.7.0/zed_extension_api/trait.Extension.html
[settings-rs]: https://docs.rs/crate/zed_extension_api/0.7.0/source/src/settings.rs
[wit-cs]: https://docs.rs/crate/zed_extension_api/0.7.0/source/wit/since_v0.6.0/context-server.wit
[wit-dap]: https://docs.rs/crate/zed_extension_api/0.7.0/source/wit/since_v0.6.0/dap.wit
[manifest-rs]: https://github.com/zed-industries/zed/blob/v1.21.0/crates/extension/src/extension_manifest.rs
[cli-rs]: https://github.com/zed-industries/zed/blob/v1.21.0/crates/extension_cli/src/main.rs
[cargo-locator]: https://github.com/zed-industries/zed/blob/v1.21.0/crates/project/src/debugger/locators/cargo.rs
[lldb-dap]: https://github.com/llvm/llvm-project/blob/main/lldb/tools/lldb-dap/README.md
