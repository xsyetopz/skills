---
name: develop-editor-plugins
description: >-
  Builds, tests, and packages editor extensions for VS Code, IntelliJ,
  Eclipse, Neovim, Sublime Text, and Zed. Use when writing or debugging a
  plugin, manifest, or extension API call.
---

# Develop Editor Plugins

Editor extensions run inside a host that owns the UI thread, the
activation schedule, and the API versions. Most failures come from work
the host did not expect: slow startup, blocked UI, a manifest that
names an API the target host lacks, or behavior never run in the host.
Identify the editor first, then read its reference.

## Rules

- Mistake: loading everything at startup. Fix: register entry points
  cheaply and load code on first use (VS Code activation events,
  Neovim `require` inside callbacks, IntelliJ and Eclipse lazy
  extensions). Reason: every extension's startup cost is paid by every
  session, used or not.
- Mistake: file, network, process, or index work on the UI thread. Fix:
  move it to the host's background mechanism (Jobs, background tasks,
  `vim.system` with a callback, `set_timeout_async`) and return results
  to the UI thread with the host's scheduler. Reason: a blocked UI
  thread freezes the whole editor.
- Mistake: applying an async result to state that changed. Fix: capture
  the document or buffer handle and version first, and recheck both
  when the result arrives.
- Mistake: declaring a manifest version, engine range, or API level from
  memory. Fix: read the minimum the target host supports from its docs
  or the built artifact, and pin to it. Reason: a newer declaration
  installs nowhere older and fails at load, not at build.
- Mistake: treating a build, unit test, or mock as proof of editor
  behavior. Fix: run the extension inside the real host (extension-host
  tests, IDE test fixtures, headless `nvim`, UnitTesting, a dev install)
  and report host steps that did not run as not verified.
- Mistake: publishing with an unchecked package. Fix: run the editor's
  packaging check below and inspect the archive contents first. Do not
  publish or open registry pull requests unless the user explicitly asks;
  Marketplace versions are public and cannot be reused.

## Scripts

- `bun scripts/check_vscode_manifest.mjs [--src DIR] [--built]
  [--pre-release] PACKAGE_JSON`: checks `package.json` fields,
  activation, and packaging rules.
- `python3 scripts/check_intellij_plugin_xml.py [--src-root DIR]
  PLUGIN_XML...`: checks `plugin.xml` and that registered classes exist.
- `python3 scripts/check_eclipse_bundle.py BUNDLE_DIR...`: checks
  `MANIFEST.MF`, `build.properties`, and `plugin.xml` of each bundle.
- `python3 scripts/check_sublime_package.py PACKAGE_DIR [--external CMD]`:
  checks `.python-version`, resource files, and command names.
- `python3 scripts/check_zed_extension.py EXT_DIR [--registry]`: checks
  `extension.toml` and language config.
- `python3 scripts/check_zed_queries.py LANGUAGE_DIR [--node-types FILE]`:
  checks Tree-sitter query files.
- `python3 scripts/check_zed_theme.py FILE --schema SCHEMA`: validates a
  Zed theme or icon theme.
- `python3 scripts/wasm_api_version.py BUILT.wasm --max 0.7.0`: prints
  the API version a Zed extension build declares.

Run each with `--help` first; arguments are listed there. On Windows, use
`py -3` for `python3`.

## References

- Read [references/vscode.md](references/vscode.md) when the target is
  VS Code.
- Read [references/intellij.md](references/intellij.md) when the target
  is an IntelliJ Platform IDE.
- Read [references/eclipse.md](references/eclipse.md) when the target is
  Eclipse.
- Read [references/neovim.md](references/neovim.md) when the target is
  Neovim.
- Read [references/sublime-text.md](references/sublime-text.md) when the
  target is Sublime Text.
- Read [references/zed.md](references/zed.md) when the target is Zed.
