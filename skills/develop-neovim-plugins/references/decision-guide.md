# Decision guide

Use this guide after inspecting the target repository and current request. It
selects an evidence path; it does not grant permission for writes or external
operations.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| Personal one-off mapping requested | Edit config, not create a plugin. | Plugin scaffold. |
| Async result targets buffer | Capture buffer + changedtick/generation; schedule and revalidate. | Using current buffer on completion. |
| Autocmds need reload safety | Use named augroup and clear only that group. | Global autocmd clear. |
| libuv/job used | Define stop/close/wait and error/exit handling. | Garbage-collection hope. |
| Feature requires newer API | Gate declared minimum version or provide evidenced compatibility. | pcall catch-all fallback. |
| UI state is ephemeral | Use namespaces/extmarks and deterministic cleanup. | Persistent global tables without lifecycle. |

## Unresolved decisions

A material product, compatibility, public-interface, deployment, or policy
choice remains user-owned when repository evidence does not settle it. Present
the concrete alternatives and consequences. Routine implementation details that
do not change an external contract remain the agent's responsibility.

## Avoiding false precision

Use project-defined thresholds, limits, versions, and acceptance criteria. When
none exists, report measurements or uncertainty; do not invent a timeout,
reviewer count, confidence score, supported version, performance target, or
error budget and then treat it as a requirement.
