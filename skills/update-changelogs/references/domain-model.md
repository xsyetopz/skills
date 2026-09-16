# Domain model and authority

## Terms

| Term | Operational meaning |
| --- | --- |
| **Unreleased** | Changes accepted into the tracked branch but not assigned/published under a release according to project process. |
| **Release notes** | Audience-facing description for a particular release; may differ from complete changelog history. |
| **Breaking change** | A change that violates an actual supported contract; not every internal refactor. |
| **Deprecation** | Supported behavior marked for future removal under a policy; not equivalent to retirement. |
| **Revision range** | Exact commits included/excluded in the update. |
| **Publication** | Provider/package action making a release available; separate from writing text. |

## Invariants

- Every entry maps to a change in the stated range and its real effect.
- Release metadata reflects actual authorized state.
- Internal-only work is not inflated into user-facing features.
- Breaking/deprecation claims follow real public contracts and policy.
- Links/identifiers resolve and formatting matches the repository.

## Authority and source hierarchy

- The user and release process control version/date/publication.
- Git diffs/history, merged changes, package artifacts, and product behavior
  establish content.
- Existing changelog format controls style; old entries may contain stale facts
  and are not copied blindly.
- SemVer applies only to declared public API/version policy.

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
