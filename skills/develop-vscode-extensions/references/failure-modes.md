# Failure modes and recovery

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Visual Studio conflation** | VS Code APIs/package are mixed with Visual Studio extension concepts. | Use exact VS Code extension API/VSIX tooling. |
| **Filesystem assumption** | `uri.fsPath`/Node fs is used for remote/virtual/web resources. | Use `workspace.fs` and URI APIs when appropriate. |
| **Stale async edit** | Analysis for version N applies to N+1. | Capture and revalidate document identity/version/generation. |
| **Disposable leak** | Reload creates duplicate commands/watchers/processes. | Own and dispose all registrations/resources. |
| **Trust bypass** | Workspace-controlled command runs in untrusted workspace. | Enforce trust at execution boundary. |
| **Node-only web bundle** | Extension declares web support but imports unavailable APIs. | Separate/conditional host implementation and test. |
| **Package omission** | Runtime asset is not included in VSIX. | Inspect package manifest and archive contents. |

## Recovery discipline

Preserve the first useful error and the state that produced it. Stop dependent
work when a prerequisite is false. Change strategy when another equivalent edit
or retry cannot produce new evidence. Undo only attributable experimental
changes; never reset or overwrite unrelated user work to obtain a clean result.

Do not convert a failure into success by swallowing the error, weakening the
assertion, regenerating an unexplained snapshot, adding speculative fallback
behavior, or reporting an intermediate checkpoint as the completed task.
