# Domain model and authority

## Terms

| Term | Operational meaning |
| --- | --- |
| **Explicit** | Important behavior, ownership, units, errors, and state transitions are visible at the appropriate interface—not necessarily verbose. |
| **Simple** | Contains no unnecessary concepts for the actual requirements; it is not synonymous with fewest lines. |
| **Complex** | Inherent problem constraints that must be represented. |
| **Complicated** | Accidental structure that obscures or duplicates those constraints. |
| **Canonical path** | The primary supported mechanism for one concern, while native escape hatches remain available when justified. |
| **Practicality** | An evidenced tradeoff that preserves the important contract; not a blanket excuse to ignore design problems. |

## Invariants

- The target language and project conventions remain the implementation
  vocabulary.
- Behavioral and compatibility contracts outrank stylistic preference.
- Names communicate domain meaning, units, ownership, and effects at their point
  of use.
- Errors remain observable unless the contract explicitly handles or translates
  them.
- An abstraction is retained or introduced for demonstrated invariants,
  ownership, substitution, or extension boundaries—not familiarity alone.

## Authority and source hierarchy

- PEP 20 supplies aphorisms; the user and repository define the target contract.
- Language specifications, standard libraries, project APIs, and established
  architecture control concrete implementation choices.
- Existing code is evidence, not automatically the desired state.
- Tests support behavior claims but do not create a product requirement by
  themselves.

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
