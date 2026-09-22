# Extension failures and recovery for Zed WASM Extension

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Capability invention** | Unsupported UI/provider API is fabricated. | Check selected-version API and report gap. |
| **Grammar/query drift** | Node names do not match pinned grammar. | Pin/test grammar and queries together. |
| **Forced stable Rust** | Instructions override project-selected toolchain. | Resolve repository rust-toolchain/host requirement. |
| **Binary latest drift** | Unpinned newest server is downloaded. | Resolve approved version and verify artifact. |
| **Path/platform assumption** | Binary mapping ignores OS/architecture/remote environment. | Use explicit supported matrix and errors. |
| **Local-only validation** | Source loads but registry/package clean install fails. | Test packaged extension in target host. |

## Recovery discipline

Preserve the first observable Zed extension failure and the state that produced
it. Stop dependent work after a false prerequisite. If another equivalent retry
cannot add evidence, change the source, instrument, or hypothesis. Undo only
task-owned experiments; preserve unrelated user work.

Do not make the Zed extension appear successful by swallowing its error,
weakening its oracle, regenerating an unexplained snapshot, adding an
unsupported fallback, or reporting an intermediate checkpoint as completion.
