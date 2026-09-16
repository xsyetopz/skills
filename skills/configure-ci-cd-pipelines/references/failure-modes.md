# Failure modes and recovery

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Privileged follow-up** | A trusted event checks out and executes untrusted PR code. | Separate metadata handling from code execution or use an unprivileged event. |
| **Artifact substitution** | Deploy job downloads by mutable name without verifying producer/revision. | Bind artifact identity and digest to the verified run. |
| **Cache as source of truth** | Build succeeds only with stale cached generated output. | Regenerate from source and make cache optional. |
| **Failure masking** | A final report or shell pipeline returns success after a required step failed. | Preserve exit status and explicit dependencies. |
| **Trigger confusion** | Branch filters or workflow rules run on the wrong ref or event payload. | Evaluate the provider’s exact event/ref semantics. |
| **Secret logging** | Debug output or command echo exposes credentials. | Use masking, no-echo, scoped variables, and approved secret mechanisms. |

## Recovery discipline

Preserve the first useful error and the state that produced it. Stop dependent
work when a prerequisite is false. Change strategy when another equivalent edit
or retry cannot produce new evidence. Undo only attributable experimental
changes; never reset or overwrite unrelated user work to obtain a clean result.

Do not convert a failure into success by swallowing the error, weakening the
assertion, regenerating an unexplained snapshot, adding speculative fallback
behavior, or reporting an intermediate checkpoint as the completed task.
