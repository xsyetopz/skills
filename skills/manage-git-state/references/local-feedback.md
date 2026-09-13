# Local feedback and existing Git hooks

Inspect repository task commands, message policy, `core.hooksPath`, executable
hooks, and hook-manager configuration before a commit-producing operation or
push. Existing hooks are part of the repository contract: review their commands,
run the configured checks, and do not bypass failures with `--no-verify`.

Do not install or replace Git hooks merely because a CI, bisect, commit, push,
or hosted-repository workflow is active. Add or change hook policy only when the
repository already requires that mechanism or the user requested hook work.
Preserve existing ownership and never force-reset `core.hooksPath`.

Use the repository's task runner so local feedback and CI execute the same
underlying checks where practical. Formatting hooks should check rather than
rewrite or stage unrelated work. Keep deployments, publication, destructive
tests, and secret-dependent production jobs out of local hooks.

For commits, verify the staged snapshot immediately before the operation and
reinspect it after a failed hook because hooks can modify files. For pushes,
bind validation to the object IDs supplied to `pre-push` when the configured
hook claims snapshot accuracy. A direct task invocation does not prove that Git
ran its hook; test changed hook configuration in a disposable repository.

For message-policy selection and the no-policy fallback, use
[snapshots and refs](snapshots-and-refs.md#commit-messages). Passing a message
hook proves neither behavioral slicing nor the correctness of committed code.

Sources: [Git hooks](https://git-scm.com/docs/githooks) and the configured hook
manager's documentation.
