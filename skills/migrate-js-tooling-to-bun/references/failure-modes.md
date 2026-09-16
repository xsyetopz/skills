# Failure modes and recovery

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Total-toolchain replacement** | Package-manager request silently changes runtime/test/bundler/deploy. | Define and preserve responsibility boundaries. |
| **Lockfile blindness** | Old lockfile is deleted and a different graph accepted. | Compare resolutions and explain authorized differences. |
| **Registry loss** | Scopes/auth/mirrors disappear. | Migrate approved registry configuration without exposing secrets. |
| **Lifecycle suppression** | Install scripts are disabled to obtain success. | Understand and preserve required scripts or reject unsupported package. |
| **Compatibility folklore** | Node API compatibility is assumed from memory. | Check selected Bun version and run project behavior. |
| **One-platform proof** | Native dependency works on one OS and is claimed portable. | Test declared target matrix or state limits. |

## Recovery discipline

Preserve the first useful error and the state that produced it. Stop dependent
work when a prerequisite is false. Change strategy when another equivalent edit
or retry cannot produce new evidence. Undo only attributable experimental
changes; never reset or overwrite unrelated user work to obtain a clean result.

Do not convert a failure into success by swallowing the error, weakening the
assertion, regenerating an unexplained snapshot, adding speculative fallback
behavior, or reporting an intermediate checkpoint as the completed task.
