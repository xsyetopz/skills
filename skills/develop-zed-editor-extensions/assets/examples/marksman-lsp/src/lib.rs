//! Starts Marksman for Zed's built-in Markdown language.
//!
//! Resolution order: a `marksman` on the worktree PATH, then a binary
//! this extension downloaded earlier, then a GitHub release: the tag in
//! the shell variable `MARKSMAN_RELEASE`, else the latest release.
use std::fs;

use zed_extension_api::{self as zed, settings::LspSettings, LanguageServerId, Result};

const REPO: &str = "artempyanykh/marksman";
const PREFIX: &str = "marksman-";
/// Shell variable that pins a release tag, e.g. `2026-02-08`.
const PIN_VAR: &str = "MARKSMAN_RELEASE";

struct MarksmanExtension {
    cached_binary_path: Option<String>,
}

/// Maps the host platform to a Marksman release asset name.
fn asset_name(os: zed::Os, arch: zed::Architecture) -> Option<&'static str> {
    use zed::{Architecture as A, Os};
    match (os, arch) {
        (Os::Mac, A::Aarch64 | A::X8664) => Some("marksman-macos"),
        (Os::Linux, A::X8664) => Some("marksman-linux-x64"),
        (Os::Linux, A::Aarch64) => Some("marksman-linux-arm64"),
        (Os::Windows, A::X8664) => Some("marksman.exe"),
        _ => None,
    }
}

/// Path of the binary for one release, relative to the work directory.
fn binary_path(version: &str, os: zed::Os) -> String {
    let file = match os {
        zed::Os::Windows => "marksman.exe",
        zed::Os::Mac | zed::Os::Linux => "marksman",
    };
    format!("{PREFIX}{version}/{file}")
}

/// Version directories that belong to releases other than `keep`.
fn stale_dirs<'a>(names: &'a [String], keep: &str) -> Vec<&'a str> {
    names
        .iter()
        .map(String::as_str)
        .filter(|name| name.starts_with(PREFIX) && *name != keep)
        .collect()
}

/// The pinned release tag from the worktree's shell environment, if any.
fn release_pin(env: &[(String, String)]) -> Option<&str> {
    env.iter()
        .find(|(key, value)| key == PIN_VAR && !value.is_empty())
        .map(|(_, value)| value.as_str())
}

fn fetch_release(pin: Option<&str>) -> Result<zed::GithubRelease> {
    match pin {
        Some(tag) => zed::github_release_by_tag_name(REPO, tag),
        None => zed::latest_github_release(
            REPO,
            zed::GithubReleaseOptions {
                require_assets: true,
                pre_release: false,
            },
        ),
    }
}

fn is_file(path: &str) -> bool {
    fs::metadata(path).is_ok_and(|stat| stat.is_file())
}

impl MarksmanExtension {
    fn binary(&mut self, id: &LanguageServerId, wt: &zed::Worktree) -> Result<String> {
        if let Some(path) = wt.which("marksman") {
            return Ok(path);
        }
        if let Some(path) = &self.cached_binary_path {
            if is_file(path) {
                return Ok(path.clone());
            }
        }
        let env = wt.shell_env();
        let path = download(id, release_pin(&env)).inspect_err(|error| {
            let failed = zed::LanguageServerInstallationStatus::Failed(error.clone());
            zed::set_language_server_installation_status(id, &failed);
        })?;
        self.cached_binary_path = Some(path.clone());
        Ok(path)
    }
}

fn download(id: &LanguageServerId, pin: Option<&str>) -> Result<String> {
    use zed::LanguageServerInstallationStatus as Status;
    zed::set_language_server_installation_status(id, &Status::CheckingForUpdate);
    let release = fetch_release(pin)?;
    let (os, arch) = zed::current_platform();
    let name = asset_name(os, arch)
        .ok_or_else(|| format!("marksman has no release for {os:?} {arch:?}"))?;
    let asset = release
        .assets
        .iter()
        .find(|asset| asset.name == name)
        .ok_or_else(|| format!("release {} lacks {name}", release.version))?;
    let dir = format!("{PREFIX}{}", release.version);
    let path = binary_path(&release.version, os);
    if !is_file(&path) {
        zed::set_language_server_installation_status(id, &Status::Downloading);
        fs::create_dir_all(&dir).map_err(|e| format!("create {dir}: {e}"))?;
        zed::download_file(
            &asset.download_url,
            &path,
            zed::DownloadedFileType::Uncompressed,
        )?;
        zed::make_file_executable(&path)?;
        let names: Vec<String> = fs::read_dir(".")
            .map_err(|e| format!("list work dir: {e}"))?
            .filter_map(|entry| entry.ok())
            .filter_map(|entry| entry.file_name().into_string().ok())
            .collect();
        for stale in stale_dirs(&names, &dir) {
            fs::remove_dir_all(stale).ok();
        }
    }
    zed::set_language_server_installation_status(id, &Status::None);
    Ok(path)
}

impl zed::Extension for MarksmanExtension {
    fn new() -> Self {
        Self {
            cached_binary_path: None,
        }
    }

    fn language_server_command(
        &mut self,
        id: &LanguageServerId,
        worktree: &zed::Worktree,
    ) -> Result<zed::Command> {
        Ok(zed::Command {
            command: self.binary(id, worktree)?,
            args: vec!["server".to_string()],
            env: Default::default(),
        })
    }

    fn language_server_initialization_options(
        &mut self,
        id: &LanguageServerId,
        worktree: &zed::Worktree,
    ) -> Result<Option<zed::serde_json::Value>> {
        let settings = LspSettings::for_worktree(id.as_ref(), worktree)?;
        Ok(settings.initialization_options)
    }

    fn language_server_workspace_configuration(
        &mut self,
        id: &LanguageServerId,
        worktree: &zed::Worktree,
    ) -> Result<Option<zed::serde_json::Value>> {
        let settings = LspSettings::for_worktree(id.as_ref(), worktree)?;
        Ok(settings.settings)
    }
}

zed::register_extension!(MarksmanExtension);

#[cfg(test)]
mod tests {
    use super::*;
    use zed::{Architecture as A, Os};

    #[test]
    fn maps_every_published_platform() {
        assert_eq!(asset_name(Os::Mac, A::Aarch64), Some("marksman-macos"));
        assert_eq!(asset_name(Os::Mac, A::X8664), Some("marksman-macos"));
        assert_eq!(
            asset_name(Os::Linux, A::Aarch64),
            Some("marksman-linux-arm64")
        );
        assert_eq!(asset_name(Os::Windows, A::X8664), Some("marksman.exe"));
        assert_eq!(asset_name(Os::Windows, A::Aarch64), None);
        assert_eq!(asset_name(Os::Linux, A::X86), None);
    }

    #[test]
    fn pin_comes_from_a_non_empty_shell_variable() {
        let env = |value: &str| vec![(PIN_VAR.to_string(), value.to_string())];
        assert_eq!(release_pin(&env("2026-02-08")), Some("2026-02-08"));
        assert_eq!(release_pin(&env("")), None);
        assert_eq!(release_pin(&[]), None);
    }

    #[test]
    fn binary_lives_in_a_versioned_directory() {
        assert_eq!(
            binary_path("2026-02-08", Os::Linux),
            "marksman-2026-02-08/marksman"
        );
        assert_eq!(
            binary_path("2026-02-08", Os::Windows),
            "marksman-2026-02-08/marksman.exe"
        );
    }

    #[test]
    fn keeps_only_the_current_version_directory() {
        let names = ["marksman-2025-01-01", "marksman-2026-02-08", "other"].map(String::from);
        assert_eq!(
            stale_dirs(&names, "marksman-2026-02-08"),
            vec!["marksman-2025-01-01"]
        );
    }
}
