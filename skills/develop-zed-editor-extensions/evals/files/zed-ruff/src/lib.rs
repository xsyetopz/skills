use zed_extension_api::{self as zed, LanguageServerId, Result};

struct RuffExtension;

impl zed::Extension for RuffExtension {
    fn new() -> Self {
        RuffExtension
    }

    fn language_server_command(
        &mut self,
        _language_server_id: &LanguageServerId,
        worktree: &zed::Worktree,
    ) -> Result<zed::Command> {
        let path = worktree
            .which("ruff")
            .ok_or_else(|| "ruff is not on PATH; install it with `uv tool install ruff`".to_string())?;
        Ok(zed::Command {
            command: path,
            args: vec!["server".into()],
            env: worktree.shell_env(),
        })
    }
}

zed::register_extension!(RuffExtension);
