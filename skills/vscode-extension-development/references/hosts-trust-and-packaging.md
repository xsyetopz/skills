# Manifest, host placement, trust and VSIX

Research: 2026-09-09. Stable baseline: **VS Code 1.136.2**, listed in the [1.136
release notes][ref-1]. Proposed APIs and Insiders features are separate from
stable extension contracts.

## Manifest and activation

Manifest fragment:

```json
{
  "name": "example-tools",
  "publisher": "example",
  "version": "0.1.0",
  "engines": { "vscode": "^1.136.0" },
  "main": "./dist/extension.js",
  "browser": "./dist/browser.js",
  "extensionKind": ["workspace"],
  "contributes": {
    "commands": [{ "command": "example.inspect", "title": "Example: Inspect" }],
    "configuration": {
      "title": "Example",
      "properties": {
        "example.enabled": {
          "type": "boolean",
          "default": true,
          "scope": "resource"
        }
      }
    }
  }
}
```

Keep public IDs stable across upgrades. Register the contributed command in
`activate(context)`; current hosts activate contributed commands/languages
automatically, while pre-1.74 support needs matching explicit activation events.
Use feature-specific activation events. `@types/vscode` must not silently permit
APIs newer than the minimum engine. `main` and `browser` must resolve to actual
packaged JavaScript, with `vscode` externalized from the bundle.
[Manifest][ref-2], [activation][ref-3].

## Host and resource placement

A workspace extension runs near workspace tools, potentially on
SSH/container/WSL; UI extensions run locally; a web extension runs in a browser
worker. `extensionKind` expresses placement preference, not a way to inject Node
into a web worker. Browser code cannot import Node filesystem/process APIs. Use
`workspace.fs.readFile(uri)` and `Uri.joinPath` for supported virtual/remote
resources, not blanket `uri.fsPath` conversion. Determine the correct workspace
folder in multi-root projects. [Hosts][ref-4], [virtual workspaces][ref-5].

Store workspace state in `workspaceState`, extension-global state in
`globalState`, secrets in `context.secrets`, and larger files under the
appropriate storage URI. Await updates when later behavior depends on
persistence. A setting's resource/workspace scope differs from a global memento.
Keep cached document/version data out of long-lived persistent storage unless a
migration/revalidation strategy exists.

## Trust and webviews

Declare `capabilities.untrustedWorkspaces` and `virtualWorkspaces` according to
actual supported behavior, including a description for limited support. Guard
process execution with `workspace.isTrusted`; the manifest does not enforce
every code path. Listen for trust grant when enabling a previously disabled
feature. Workspace-controlled executable paths/configuration are not safe merely
because a command was activated. [Workspace Trust][ref-6].

For a webview, allow scripts only when required, constrain `localResourceRoots`,
convert assets with `asWebviewUri`, and set a CSP using `webview.cspSource` plus
a per-page nonce for scripts. Validate message discriminants and payloads before
commands or file access. Escape rendered workspace text. `acquireVsCodeApi()`
state belongs to the webview; serializer-based restoration must rebuild
validated state rather than replaying privileged actions. Dispose listeners when
the panel closes. [Webview API][ref-7].

## Debug, package and distribute

Use the repository's Extension Development Host launch configuration
(`--extensionDevelopmentPath`); set breakpoints in activation and inspect the
Extension Host log when commands do not appear. A missing command can be
activation, registration or manifest mismatch. Test desktop, remote and web
hosts only for the advertised surfaces, using `@vscode/test-electron` or
`@vscode/test-web` where established. Use extension-host tests for host
behavior. [Testing][ref-8].

With the project's selected `vsce` available, run `vsce ls` to inspect inclusion
and `vsce package` for a local VSIX. Ensure production output, runtime
dependencies and assets are included; exclude secrets and irrelevant build
files. `.vscodeignore` and bundler externals must agree. A native dependency may
need platform-specific VSIXs and a compatible host ABI. Inspect the archive
before a clean-profile install. [Publishing and packaging][ref-9].

For an isolated VSIX installation, run this with the intended executable:

```sh
code --user-data-dir /case/vscode-user \
  --extensions-dir /case/vscode-extensions \
  --install-extension ./example-tools-0.1.0.vsix
```

The two directories isolate the profile and extensions. For native assets,
`vsce package --target linux-x64` selects that platform; produce other required
architecture packages separately and keep a `web` target for an advertised
browser build. `--pre-release` selects the Marketplace prerelease channel;
extension versions still use numeric `major.minor.patch`, not SemVer suffixes.

Publication requires a matching Marketplace publisher identity. With publishing
credentials configured, `vsce publish` publishes; alternatively upload the
reviewed VSIX through publisher management. Current documentation recommends
Entra workload federation/managed identity for automation, with publisher
Contributor access and `vsce publish --azure-credential` inside the
authenticated Azure task. Establish the federation's exact issuer/subject and
restrict service-connection access to publishing pipelines. Existing PAT
workflows use `vsce login PUBLISHER` with the secret entered securely; the
documentation announces global PAT retirement on 2026-12-01, so do not introduce
that as a new long-term automation dependency. Verify the published version,
target and channel independently. [Current publication procedure and
authentication][ref-10].

Refresh a different minimum engine, proposed API, native ABI or changed
packaging tool. Read [document lifecycle](document-lifecycle.md) when
implementing providers, edits or asynchronous state.

[ref-1]: https://code.visualstudio.com/updates/v1_136
[ref-2]: https://code.visualstudio.com/api/references/extension-manifest
[ref-3]: https://code.visualstudio.com/api/references/activation-events
[ref-4]: https://code.visualstudio.com/api/advanced-topics/extension-host
[ref-5]: https://code.visualstudio.com/api/extension-guides/virtual-workspaces
[ref-6]: https://code.visualstudio.com/api/extension-guides/workspace-trust
[ref-7]: https://code.visualstudio.com/api/extension-guides/webview
[ref-8]:
  https://code.visualstudio.com/api/working-with-extensions/testing-extension
[ref-9]:
  https://code.visualstudio.com/api/working-with-extensions/publishing-extension
[ref-10]:
  https://github.com/microsoft/vscode-docs/blob/main/api/working-with-extensions/publishing-extension.md
