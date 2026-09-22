# Operational decisions for Local Git State

Use this guide after inspecting the request and target system for local Git
operation. It selects an evidence path; it does not grant permission for an
external write or another consequential operation.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| Need to remove assistant changes while preserving user edits in same file | Use patch/three-way/snapshot-aware restoration. | `git checkout -- file` or hard reset. |
| Need to undo a published commit | Prefer revert unless authorized history rewrite is explicitly required. | Local reset followed by force push. |
| Need isolated parallel work | Use project-native isolation or a worktree with recorded base/ownership. | Multiple agents in one working tree. |
| Push rejected because remote advanced | Fetch and inspect; integrate or ask according to policy. | Blind force retry. |
| Hook modifies files during commit | Inspect new working/index/commit state and amend only with authority. | Assuming pre-hook staged snapshot was committed. |

## Unresolved decisions

A material scope, compatibility, interface, deployment, or policy choice for the
local Git operation remains user-owned when repository evidence does not settle
it. Present concrete alternatives and consequences. Resolve routine internal
details that do not change an external contract.

## Avoiding false precision

Use thresholds, limits, versions, and acceptance criteria that govern the local
Git operation. If none exists, report measurements or uncertainty. Do not invent
a timeout, reviewer count, confidence score, target, or error budget and then
treat it as a requirement.
