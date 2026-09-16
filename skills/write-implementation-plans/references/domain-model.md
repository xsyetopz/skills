# Domain model and authority

## Terms

| Term | Operational meaning |
| --- | --- |
| **Implementation plan** | An ordered, evidence-backed work description for producing an agreed change. |
| **Task** | A bounded change with prerequisites, concrete target, and acceptance evidence. |
| **Dependency** | An output, decision, state, or contract that must exist before another task can proceed. |
| **Migration** | A transition of data/config/API/runtime/deployment state while preserving required behavior. |
| **Rollback** | A defined return or recovery path for a failed rollout/migration; not always possible or free. |
| **Completion condition** | Evidence that the task’s changed contract is satisfied, not a progress checkpoint. |

## Invariants

- Every planned file/component/API exists or is explicitly introduced for a
  demonstrated need.
- Task ordering follows real dependencies and state transitions.
- Verification observes changed boundaries.
- Out-of-scope cleanup and speculative extensibility are excluded.
- Plan does not claim execution, approval, estimates, or readiness not
  established.

## Authority and source hierarchy

- The user-approved requirements and design/public contracts control intended
  behavior.
- Current repository source/config/tests/history/tooling establish
  implementation state.
- Existing planning process controls format and approvals when applicable.
- A plan cannot grant mutation, release, or deployment authority.

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
