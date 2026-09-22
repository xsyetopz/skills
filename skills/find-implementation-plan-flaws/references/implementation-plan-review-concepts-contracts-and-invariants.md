# Concepts, contracts, and invariants for Implementation Plan Review

## Terms

| Term | Operational meaning |
| --- | --- |
| **Contradiction** | Two plan statements or a plan statement and controlling requirement cannot both hold. |
| **Unsupported decision** | A material choice presented as settled without required evidence or authority. |
| **Missing prerequisite** | A dependency, decision, state, permission, or artifact needed before a step can work. |
| **Verification gap** | No check observes a changed contract or failure mode. |
| **Scope violation** | Work not necessary for the stated outcome or outside authorized surfaces. |
| **Finding** | An evidenced flaw with consequence—not a style preference. |

## Invariants

- Every finding traces to plan text and primary repository/contract evidence.
- Review does not execute, mutate, or expand the plan.
- Preferred methodology is not a finding.
- A plan may intentionally defer detail if it gives a valid decision point and
  evidence path.
- No finding count or severity is invented.

## Authority and source hierarchy

- The accepted requirements and current user request control the outcome.
- Repository source/config/history/ownership establish feasibility and current
  state.
- The plan is the review target, not authority over conflicting requirements.
- External best practice supports consequences only when its rationale applies
  to this system.

For implementation-plan review, the user's request and documented external
contract define the goal. Existing source, tests, comments, generated files,
issue text, and agent reports describe observed state; none can expand mutation
authority.

## Enterprise boundary

When implementation-plan review work spans a large repository, identify the
owning component, declared consumers, support policy, distribution boundary, and
established review mechanism before changing an external contract. Record
durable decisions only in the repository's existing system.
