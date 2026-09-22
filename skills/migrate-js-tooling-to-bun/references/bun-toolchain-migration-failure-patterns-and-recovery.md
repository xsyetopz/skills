# Failure patterns and recovery for Bun Toolchain Migration

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Total-toolchain replacement** | Package-manager request silently changes runtime/test/bundler/deploy. | Define and preserve responsibility boundaries. |
| **Lockfile blindness** | Old lockfile is deleted and a different graph accepted. | Compare resolutions and explain authorized differences. |
| **Registry loss** | Scopes/auth/mirrors disappear. | Migrate approved registry configuration without exposing secrets. |
| **Lifecycle suppression** | Install scripts are disabled to obtain success. | Understand and preserve required scripts or reject unsupported package. |
| **Compatibility folklore** | Node API compatibility is assumed from memory. | Check selected Bun version and run project behavior. |
| **One-platform proof** | Native dependency works on one OS and is claimed portable. | Test declared target matrix or state limits. |

## Recovery discipline

Preserve the first observable Bun migration failure and the state that produced
it. Stop dependent work after a false prerequisite. If another equivalent retry
cannot add evidence, change the source, instrument, or hypothesis. Undo only
task-owned experiments; preserve unrelated user work.

Do not make the Bun migration appear successful by swallowing its error,
weakening its oracle, regenerating an unexplained snapshot, adding an
unsupported fallback, or reporting an intermediate checkpoint as completion.
