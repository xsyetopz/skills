# Domain model and authority

## Terms

| Term | Operational meaning |
| --- | --- |
| **Compatibility behavior** | Code or configuration that accepts, translates, emulates, or preserves an older/different external contract. |
| **Never-required support** | Behavior introduced for an imagined or mistaken consumer without an authoritative obligation. |
| **Retired support** | Previously legitimate behavior whose governing policy/decision now permits removal. |
| **Public contract** | An externally supported API, CLI, data, config, protocol, package export, or behavior subject to compatibility policy. |
| **Persisted consumer** | Stored data/config/artifact whose future reading depends on the compatibility path. |
| **Unresolved support** | Evidence is insufficient to determine whether removal is allowed. |

## Invariants

- Authority is established independently from the existence of code or tests.
- External/public and persisted-data consumers are not declared absent from
  local grep alone.
- Removed behavior is not silently retained through another alias or fallback.
- Supported contracts retain their validation, errors, cleanup, and packaging.
- Removal scope does not expand into general legacy cleanup.

## Authority and source hierarchy

- The current user and actual version/support/deprecation policy control
  removal.
- Declared stable public contracts and real persisted/external consumers remain
  obligations until retired.
- Tests, comments, age, and current implementation are evidence, not authority
  by themselves.
- Telemetry and code graphs must be current and applicable before use.

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
