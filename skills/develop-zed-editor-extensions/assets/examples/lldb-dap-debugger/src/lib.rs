//! Exposes LLVM's `lldb-dap` adapter and a locator for `cc`/`clang` tasks.
use zed_extension_api::{
    self as zed,
    process::Command,
    serde_json::{json, Map, Value},
    BuildTaskDefinition, BuildTaskDefinitionTemplatePayload,
    DebugAdapterBinary, DebugConfig, DebugRequest, DebugScenario,
    DebugTaskDefinition, LaunchRequest, Result, StartDebuggingRequestArguments,
    StartDebuggingRequestArgumentsRequest as Kind, TaskTemplate, Worktree,
};

const ADAPTER: &str = "lldb-dap";

/// Reads `request` from an adapter configuration; never guesses.
fn request_kind(config: &Value) -> Result<Kind> {
    match config.get("request").and_then(Value::as_str) {
        Some("launch") => Ok(Kind::Launch),
        Some("attach") => Ok(Kind::Attach),
        other => Err(format!(
            "`request` must be \"launch\" or \"attach\", got {other:?}"
        )),
    }
}

/// Translates the adapter-agnostic request into lldb-dap's JSON keys.
fn adapter_config(request: &DebugRequest, stop: Option<bool>) -> Value {
    let mut config = match request {
        DebugRequest::Launch(launch) => {
            let env: Map<String, Value> = launch
                .envs
                .iter()
                .map(|(key, value)| (key.clone(), json!(value)))
                .collect();
            let mut config = json!({
                "request": "launch",
                "program": launch.program,
                "args": launch.args,
                "env": env,
            });
            if let Some(cwd) = &launch.cwd {
                config["cwd"] = json!(cwd);
            }
            config
        }
        DebugRequest::Attach(attach) => {
            let mut config = json!({ "request": "attach" });
            if let Some(pid) = attach.process_id {
                config["pid"] = json!(pid);
            }
            config
        }
    };
    if let Some(stop) = stop {
        config["stopOnEntry"] = json!(stop);
    }
    config
}

/// The value after `-o` in a compiler command line.
fn output_path(args: &[String]) -> Option<&str> {
    let at = args.iter().position(|arg| arg == "-o")?;
    args.get(at + 1).map(String::as_str)
}

fn is_c_compile(task: &TaskTemplate) -> bool {
    matches!(task.command.as_str(), "cc" | "clang")
        && output_path(&task.args).is_some()
}

/// `lldb-dap` from PATH, else from Xcode via `xcrun -f` on macOS.
fn find_adapter(worktree: &Worktree) -> Result<String> {
    if let Some(path) = worktree.which(ADAPTER) {
        return Ok(path);
    }
    if !matches!(zed::current_platform().0, zed::Os::Mac) {
        return Err(format!("{ADAPTER} is not on PATH"));
    }
    let output = Command::new("xcrun")
        .args(["-f", ADAPTER])
        .envs(worktree.shell_env())
        .output()?;
    let path = String::from_utf8_lossy(&output.stdout).trim().to_string();
    if output.status == Some(0) && !path.is_empty() {
        Ok(path)
    } else {
        Err(format!("{ADAPTER} is not on PATH and xcrun cannot find it"))
    }
}

struct LldbDapExtension;

impl zed::Extension for LldbDapExtension {
    fn new() -> Self {
        Self
    }

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

    fn dap_request_kind(
        &mut self,
        _adapter_name: String,
        config: Value,
    ) -> Result<Kind> {
        request_kind(&config)
    }

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

    fn dap_locator_create_scenario(
        &mut self,
        locator_name: String,
        build_task: TaskTemplate,
        resolved_label: String,
        debug_adapter_name: String,
    ) -> Option<DebugScenario> {
        if !is_c_compile(&build_task) {
            return None;
        }
        let payload = BuildTaskDefinitionTemplatePayload {
            locator_name: Some(locator_name),
            template: build_task,
        };
        Some(DebugScenario {
            label: format!("Debug {resolved_label}"),
            adapter: debug_adapter_name,
            build: Some(BuildTaskDefinition::Template(payload)),
            config: Value::Null.to_string(),
            tcp_connection: None,
        })
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
}

zed::register_extension!(LldbDapExtension);

#[cfg(test)]
mod tests {
    use super::*;
    use zed::AttachRequest;

    #[test]
    fn request_kind_rejects_missing_or_unknown_values() {
        assert!(matches!(
            request_kind(&json!({ "request": "attach" })),
            Ok(Kind::Attach)
        ));
        assert!(request_kind(&json!({})).is_err());
        assert!(request_kind(&json!({ "request": "run" })).is_err());
    }

    #[test]
    fn launch_maps_to_lldb_dap_keys() {
        let request = DebugRequest::Launch(LaunchRequest {
            program: "build/app".into(),
            cwd: Some("/work".into()),
            args: vec!["--fast".into()],
            envs: vec![("MODE".into(), "debug".into())],
        });
        assert_eq!(
            adapter_config(&request, Some(true)),
            json!({
                "request": "launch",
                "program": "build/app",
                "args": ["--fast"],
                "env": { "MODE": "debug" },
                "cwd": "/work",
                "stopOnEntry": true,
            })
        );
    }

    #[test]
    fn attach_without_pid_omits_the_key() {
        let request = DebugRequest::Attach(AttachRequest { process_id: None });
        assert_eq!(
            adapter_config(&request, None),
            json!({ "request": "attach" })
        );
    }

    #[test]
    fn locator_accepts_only_compiles_with_an_output() {
        let task = |command: &str, args: &[&str]| TaskTemplate {
            label: "build".into(),
            command: command.into(),
            args: args.iter().map(|arg| arg.to_string()).collect(),
            env: Vec::new(),
            cwd: None,
        };
        assert!(is_c_compile(&task("clang", &["-g", "main.c", "-o", "app"])));
        assert!(!is_c_compile(&task("clang", &["-c", "main.c"])));
        assert!(!is_c_compile(&task("make", &["-o", "app"])));
        assert_eq!(output_path(&["-o".into(), "app".into()]), Some("app"));
    }
}
