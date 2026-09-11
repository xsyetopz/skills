use zed_extension_api as zed;

struct ExampleExtension;

impl zed::Extension for ExampleExtension {
    fn new() -> Self {
        Self
    }

    fn language_server_command(
        &mut self,
        _language_server_id: &zed::LanguageServerId,
        worktree: &zed::Worktree,
    ) -> zed::Result<zed::Command> {
        let command = worktree.which("__SERVER_BINARY__").ok_or_else(|| {
            "Install __SERVER_BINARY__ in this worktree PATH or set lsp binary.path".to_owned()
        })?;

        Ok(zed::Command {
            command,
            args: Vec::new(),
            env: Vec::new(),
        })
    }
}

zed::register_extension!(ExampleExtension);
