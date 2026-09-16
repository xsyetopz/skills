# Domain model and authority

## Terms

| Term | Operational meaning |
| --- | --- |
| **Phase gate** | The required completion conditions and evidence that control whether the next lifecycle phase may begin. |
| **Baseline** | An accepted requirements or design state used as the reference for downstream work; not an immutable truth. |
| **Work item** | A bounded child assignment with goal, evidence, authority, ownership, return shape, and stop condition. |
| **Coordinator** | The root agent responsible for preserving the user goal, assigning work, consuming results, and integrating evidence. |
| **Independent review** | A separate check that has a distinct question and access to primary evidence, not a quota for finding defects. |
| **Change control** | The project’s process for revising an accepted decision and replaying affected downstream verification. |

## Invariants

- Only the current phase may create production outputs for that phase;
  later-phase implementation does not begin while an earlier gate is open.
- Parallel work has disjoint write ownership or is read-only; dependent work is
  serialized.
- Child output is inspected and consumed before use.
- The coordinator preserves root scope and authorization.
- No phase passes on unsupported assertions or a subset of required checks.
- Reviewer count is proportional to distinct risk and evidence needs, never
  borrowed mechanically from an example.

## Authority and source hierarchy

- The current user and actual repository governance control scope, approvals,
  release authority, and public decisions.
- Project requirements, code, configuration, tests, and history provide
  evidence; none lets a child expand the goal.
- Harness status/configuration is the authority for effective model,
  permissions, cancellation, workspace, and terminal state.
- External workflow examples such as Bun’s rewrite inform techniques, not
  universal staffing or worktree requirements.

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
