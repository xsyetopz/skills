# Domain model and authority

## Terms

| Term | Operational meaning |
| --- | --- |
| **L1 metadata** | Name and description available during discovery; the routing bottleneck. |
| **L2 instructions** | `SKILL.md` content loaded after activation; core workflow and invariants. |
| **L3 resources** | Conditional references, scripts, and assets loaded or run only when needed. |
| **Trigger evaluation** | Measurement of whether realistic target prompts activate the skill and near-misses do not. |
| **Task evaluation** | Measurement of observable output quality, directive compliance, and operational efficiency with the skill active. |
| **Resource graph** | The linked paths from the entrypoint to references, scripts, and assets, including their loading conditions. |

## Invariants

- Every bundled file has a concrete consumer or workflow purpose.
- Critical restrictions appear before the risky action; conditional detail is
  linked where needed.
- Names and descriptions distinguish neighboring skills without keyword
  catchalls.
- Scripts are deterministic, input-validated, and tested for expected failures.
- Assets are complete enough to copy/adapt; they are not unexplained fragments.
- Evaluation claims identify the actual model, harness, prompts, repetitions,
  grader, and unexecuted limits.

## Authority and source hierarchy

- The current user controls the requested capability, edit boundary, and
  packaging.
- The Agent Skills specification controls portable structure; harness
  documentation controls provider-specific metadata and loading behavior.
- Domain primary sources and target repository evidence control technical
  instructions.
- Public skill repositories are examples to inspect, not authority to copy
  patterns blindly.

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
