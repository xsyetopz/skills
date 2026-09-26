//! Runs `@modelcontextprotocol/server-memory` on Zed's bundled Node.js.
use std::env;

use zed_extension_api::{
    self as zed,
    serde_json::{json, Value},
    settings::ContextServerSettings,
    ContextServerConfiguration, ContextServerId, Project, Result,
};

const PACKAGE: &str = "@modelcontextprotocol/server-memory";
const ENTRY: &str = "node_modules/@modelcontextprotocol/server-memory/dist/index.js";

/// Maps the `memory_file_path` setting to the server's environment.
fn server_env(settings: Option<&Value>) -> Result<Vec<(String, String)>> {
    let Some(path) = settings.and_then(|s| s.get("memory_file_path")) else {
        return Ok(Vec::new());
    };
    let path = path.as_str().ok_or("`memory_file_path` must be a string")?;
    Ok(vec![("MEMORY_FILE_PATH".to_string(), path.to_string())])
}

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

struct MemoryServerExtension;

impl zed::Extension for MemoryServerExtension {
    fn new() -> Self {
        Self
    }

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

    fn context_server_configuration(
        &mut self,
        _id: &ContextServerId,
        _project: &Project,
    ) -> Result<Option<ContextServerConfiguration>> {
        Ok(Some(ContextServerConfiguration {
            installation_instructions: "Optional: set `memory_file_path` \
                to keep the graph outside the extension directory."
                .to_string(),
            settings_schema: settings_schema().to_string(),
            default_settings: "{}".to_string(),
        }))
    }
}

zed::register_extension!(MemoryServerExtension);

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn maps_memory_file_path_to_env() {
        let settings = json!({ "memory_file_path": "/tmp/memory.jsonl" });
        assert_eq!(
            server_env(Some(&settings)).unwrap(),
            vec![("MEMORY_FILE_PATH".into(), "/tmp/memory.jsonl".into())]
        );
        assert!(server_env(None).unwrap().is_empty());
    }

    #[test]
    fn rejects_a_non_string_path() {
        let settings = json!({ "memory_file_path": 3 });
        assert!(server_env(Some(&settings)).is_err());
    }

    #[test]
    fn schema_documents_the_single_setting() {
        let schema = settings_schema();
        assert!(schema["properties"]["memory_file_path"].is_object());
    }
}
