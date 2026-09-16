# Decision guide

Use this guide after inspecting the target repository and current request. It
selects an evidence path; it does not grant permission for writes or external
operations.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| Need to remove assistant changes while preserving user edits in same file | Use patch/three-way/snapshot-aware restoration. | `git checkout -- file` or hard reset. |
| Need to undo a published commit | Prefer revert unless authorized history rewrite is explicitly required. | Local reset followed by force push. |
| Need isolated parallel work | Use project-native isolation or a worktree with recorded base/ownership. | Multiple agents in one working tree. |
| Push rejected because remote advanced | Fetch and inspect; integrate or ask according to policy. | Blind force retry. |
| Hook modifies files during commit | Inspect new working/index/commit state and amend only with authority. | Assuming pre-hook staged snapshot was committed. |

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
