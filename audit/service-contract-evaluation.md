# Service-contract coverage decision

Reviewed on 2026-09-12. Added a conditional service-contract reference to
`design-software-boundaries`, not a new umbrella implementation skill or one
micro-skill per protocol. Network compatibility, write authority and observable
failure behavior belong to an architecture boundary decision. Ordinary local
module work does not need this reference or a telemetry stack.

## Sources and scope

Checked current normative HTTP semantics (RFC 9110), HTTP caching (RFC 9111),
Problem Details (RFC 9457), the OpenAPI specification, and OpenTelemetry HTTP
and sensitive-data guidance. Sources are adjacent to claims in the reference.
The OpenAPI latest page currently identifies 3.2.1; the workflow still requires
the project's supported dialect rather than forcing an upgrade.

The added depth covers method/effect semantics, strong versus weak validators,
conditional-request precedence, atomic lost-update protection, personalized
cache boundaries, error contracts, generated versus runtime validation,
low-cardinality telemetry and sensitive propagated context. It routes to the
existing ownership reference for reconciliation rather than duplicating a
retry/idempotency implementation.

SSE, WebSocket and RPC are alternatives to investigate when the interaction
requires them, not claims that one transport solves every requirement. No custom
wire envelope, schema version, collector wrapper, authentication format or
mandatory service scaffold was introduced. The reference is not an OAuth, TLS,
DNS or QUIC implementation manual; it requires the applicable standard and
selected implementation when those mechanisms become part of the actual task.

## Bounded runtime evidence

Used actual Werkzeug 3.1.8 conditional-response and entity-tag APIs, not a mock
or hand-written header parser. Three executable checks passed:

- a matching weak `If-None-Match` validator produces 304 for GET;
- a nonmatching ETag takes precedence over an otherwise fresh
  `If-Modified-Since` date and produces 200;
- a weak entity tag does not satisfy strong comparison, although it satisfies
  weak comparison.

The first probe incorrectly assigned a string to the library's `last_modified`
property. It failed with a TypeError, then passed after using an aware datetime.
No library check or test assertion was suppressed. This fixture defect was not
copied into the guidance. Logs and the corrected probe are retained in
`/tmp/service-contract-evidence/`.

These checks establish selected HTTP contracts through a maintained library.
They do not prove a production cache, atomic database implementation, remote
collector, generated OpenAPI 3.2 client, authentication flow or network fault
scenario. No such executable asset is shipped by this reference. The earlier
[ecosystem intake](source-intake.md) separately exercised a real generated
OpenAPI consumer. Project-specific implementations still require their affected
behavior and deployment checks.

## Integration

The entrypoint conditionally links the reference. It retains the existing
architecture activation boundary and all other skills' explicit-only policy.
Skill validation, strict Markdown and local path checks supplement the source
and runtime evidence. No new default dependency or global configuration exists.
