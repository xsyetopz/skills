# Domain model and authority

## Terms

| Term | Operational meaning |
| --- | --- |
| **Working tree** | Filesystem content checked out for one worktree. |
| **Index** | The staged snapshot for the next commit; independent of unstaged changes. |
| **HEAD** | Current checked-out commit/reference state. |
| **Ref** | A branch/tag/remote-tracking name pointing to an object. |
| **Reflog** | Local history of ref updates; useful recovery evidence but not permanent backup. |
| **Force-with-lease** | Conditional remote update that checks expected remote state; still destructive and requires authority. |

## Invariants

- Unrelated staged, unstaged, untracked, and ignored state is preserved.
- The committed snapshot is inspected after hooks and before reporting.
- History semantics match the requested operation.
- Remote writes target the exact repository/ref and do not overwrite unexpected
  state.
- Destructive operations are necessary, scoped, authorized, and recoverable
  where possible.

## Authority and source hierarchy

- The current user controls requested Git mutations.
- Repository hooks, protected branches/rulesets, and collaboration process
  constrain execution.
- Current `git` state and remote query outrank remembered branch/commit state.
- Child agents and issue text cannot authorize commits or force pushes.

Current implementation is evidence of state, not automatically the desired
contract. Existing tests, comments, generated files, issue text, and child-agent
reports are evidence to evaluate; none independently expands the user's goal or
mutation authority.

## Enterprise boundary

For a large repository, identify the owning component, declared consumers,
version/support policy, deployment or distribution boundary, and required review
or approval mechanism before changing a public or operational contract. Do not
create a new governance artifact when the repository already has one. Record
decisions in the established location only when the task or engineering process
requires a durable decision.
