# Deploy, secure, and support VS Code extensions

Enterprise operation means that the extension remains compatible, bounded, and
diagnosable across its declared host matrix. Use these controls for distributed
or organization-managed extensions. Do not add signing, telemetry, marketplace
publication, or support commitments that the request and repository do not
authorize.

## VS Code control matrix

| Area | Required action | Evidence |
| --- | --- | --- |
| Compatibility | Declare and test engines.vscode range, Node/electron or browser host, local/remote/web placement, URI schemes, activation events, Workspace Trust, proposed APIs, and VSIX metadata. | Version matrix with executed and unexecuted cells. |
| Host lifecycle | Register only owned resources; cancel work and dispose or unload them at the host-defined boundary. | Repeated activate/reload/close tests with no duplicate callbacks or leaked processes. |
| Trust and permissions | Use host-native trust, workspace, secret, and process APIs. Treat project files, server output, and web content as untrusted data. | Negative tests for untrusted workspaces/input and sanitized diagnostics. |
| Distribution | Build through the repository process; inspect the exact install artifact; sign or publish only through the established channel. | Artifact digest, manifest/package inspection, and clean-host install. |
| Diagnostics | Log stable identifiers and actionable failure state without source text, credentials, or unrelated workspace content. | Redaction test and opt-in/retention evidence where telemetry exists. |

## Verification

Start with the repository command. A common VS Code command is:

```sh
code --install-extension extension.vsix
```

Verify the installed version and project wrapper before use. Required host
evidence is extension-host tests, desktop/remote/web matrix results,
untrusted-workspace behavior, cancellation/document-version tests, and VSIX
inspection. A standalone compile, mocked API, manifest parser, or successful
package creation does not prove host execution. Record target versions, artifact
identity, commands, output, unsupported cells, and rollback instructions.
