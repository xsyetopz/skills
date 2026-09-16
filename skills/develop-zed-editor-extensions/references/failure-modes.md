# Failure modes and recovery

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Capability invention** | Unsupported UI/provider API is fabricated. | Check selected-version API and report gap. |
| **Grammar/query drift** | Node names do not match pinned grammar. | Pin/test grammar and queries together. |
| **Forced stable Rust** | Instructions override project-selected toolchain. | Resolve repository rust-toolchain/host requirement. |
| **Binary latest drift** | Unpinned newest server is downloaded. | Resolve approved version and verify artifact. |
| **Path/platform assumption** | Binary mapping ignores OS/architecture/remote environment. | Use explicit supported matrix and errors. |
| **Local-only validation** | Source loads but registry/package clean install fails. | Test packaged extension in target host. |

## Recovery discipline

Preserve the first useful error and the state that produced it. Stop dependent
work when a prerequisite is false. Change strategy when another equivalent edit
or retry cannot produce new evidence. Undo only attributable experimental
changes; never reset or overwrite unrelated user work to obtain a clean result.

Do not convert a failure into success by swallowing the error, weakening the
assertion, regenerating an unexplained snapshot, adding speculative fallback
behavior, or reporting an intermediate checkpoint as the completed task.
