# Concepts, contracts, and invariants for Release History

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

For changelog entry, the user's request and documented external contract define
the goal. Existing source, tests, comments, generated files, issue text, and
agent reports describe observed state; none can expand mutation authority.

## Enterprise boundary

When changelog entry work spans a large repository, identify the owning
component, declared consumers, support policy, distribution boundary, and
established review mechanism before changing an external contract. Record
durable decisions only in the repository's existing system.
