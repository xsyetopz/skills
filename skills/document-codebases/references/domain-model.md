# Domain model and authority

## Terms

| Term | Operational meaning |
| --- | --- |
| **Reader task** | The concrete operation the documentation enables. |
| **Canonical path** | The primary supported procedure for a concern. |
| **Reference documentation** | Precise interface/options/format material, distinct from a tutorial. |
| **Tutorial** | A learning sequence with a working end state, not an exhaustive option list. |
| **Generated documentation** | Output derived from source or schema; edit its generator/source unless documented otherwise. |
| **Support claim** | A statement about versions, platforms, guarantees, or availability that creates expectations. |

## Invariants

- Examples match supported source and actual command syntax.
- Formatting-only edits do not change technical meaning.
- Unreleased and optional behavior is labeled accurately.
- No secret or sensitive value appears in examples.
- Diagrams match the described source relationships and are not treated as
  executable proof.
- Documentation does not create new product or compatibility commitments.

## Authority and source hierarchy

- The current request defines the documentation outcome.
- Source code, public interfaces, manifests, config, tests, generated
  relationships, and release records establish current behavior.
- Existing docs are evidence and style context, not automatically authoritative.
- Official external docs control third-party APIs only for the matching version.

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
