# Extension case studies for Zed WASM Extension

## Zed: explicit language-server binary resolution

```rust
fn language_server_command(
    &mut self,
    id: &LanguageServerId,
    worktree: &Worktree,
)
    -> Result<Command>
{
    if let Some(path) = worktree.which("my-language-server") {
        return Ok(Command {
            command: path,
            args: vec!["--stdio".into()],
            env: Default::default(),
        });
    }
    let asset = resolve_approved_asset(platform(), configured_version())?;
    verify_and_unpack(asset)?;
    Ok(Command {
        command: cached_binary(asset),
        args: vec!["--stdio".into()],
        env: Default::default(),
    })
}
```

Use the actual Zed API signatures for the target version. Test platform mapping,
user override, invalid download, checksum failure, cache reuse, and clean host
startup.

## Lifecycle evidence checklist

- activate/load once and twice;
- invoke normal and failing inputs;
- start async work, then edit/close/dispose before completion;
- cancel and verify no late publication;
- unload/reload or close/reopen project/workspace;
- inspect duplicate registrations, processes, timers, handles, and persisted
  state;
- build package, inspect contents, install in a clean declared host;
- distinguish stub/unit tests from real host execution.
