# Concepts, contracts, and invariants for Compatibility Retirement

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

For compatibility removal, the user's request and documented external contract
define the goal. Existing source, tests, comments, generated files, issue text,
and agent reports describe observed state; none can expand mutation authority.

## Enterprise boundary

When compatibility removal work spans a large repository, identify the owning
component, declared consumers, support policy, distribution boundary, and
established review mechanism before changing an external contract. Record
durable decisions only in the repository's existing system.
