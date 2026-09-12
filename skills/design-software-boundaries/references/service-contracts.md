# Service contracts and observability

Read this when a design crosses a network or independently deployed consumer
boundary. It is not a reason to turn local modules into services or introduce a
new telemetry stack.

## Choose an existing contract

Start with the protocol already used by consumers. HTTP suits resource-oriented
request/response APIs; an existing RPC ecosystem may justify gRPC or JSON-RPC.
Unidirectional event delivery and bidirectional sessions have different needs;
evaluate SSE or WebSocket only when the interaction requires them. Discover the
selected protocol's framing, cancellation and delivery contracts before choosing
an implementation. Do not invent a generic message envelope first and research
interoperability later.

For HTTP APIs, keep the existing OpenAPI document authoritative when present.
Choose the specification version and schema dialect supported by both producer
and consumer tooling; accepting a YAML file is not evidence of dialect support.
Describe media types, required fields, security requirements, responses and
errors. Generated types do not provide runtime validation or authorization.
Check representative requests and responses against the actual validator and
regenerate clients through the existing workflow. [OpenAPI specification][oas].

Before changing a public shape, test old and new consumers. New required fields,
restricted values and newly possible enum variants can break consumers even when
a JSON document still parses. Specify unknown-field handling and the actual
support window. Do not add an independent schema-version field when the existing
protocol, media type or package contract already supplies the necessary
identity.

## HTTP behavior is part of the API

Select methods and status codes from [HTTP semantics][http], not a custom
success/error convention. Safe methods must not request mutations. Idempotency
concerns repeated intended effects, not identical response bytes. A timeout does
not prove that a write failed; use the ownership reference's reconciliation
contract before retrying.

For lost-update protection, evaluate a strong ETag with `If-Match`. Compare and
commit atomically at the authoritative writer; checking a header and later
writing without a concurrency condition still races. A stale precondition
normally produces 412. Weak validators cannot satisfy strong comparison. For
conditional reads, `If-None-Match` uses weak comparison and takes precedence
over `If-Modified-Since`. Reuse framework header parsers and
conditional-response support rather than splitting entity-tag lists or dates
manually. [HTTP preconditions][preconditions].

Decide cacheability alongside authorization and representation selection.
`no-cache` permits storage but requires successful validation before reuse;
`no-store` prohibits storage by compliant caches. `private` excludes shared
caches but does not mean encrypted. Include relevant representation-selection
headers in `Vary`. Test cache keys and isolation for personalized responses
rather than assuming a response status or JSON content type prevents caching.
[HTTP caching][caching].

Where a new HTTP error representation is needed, evaluate RFC 9457 Problem
Details before creating another envelope. Keep HTTP status authoritative,
provide stable problem identities when needed, and avoid leaking stack traces,
credentials or private resource details. Do not replace a supported existing
error contract without a migration reason. [Problem Details][problems].

## Telemetry must preserve the boundary

Reuse the application's logging and OpenTelemetry instrumentation before adding
custom wrappers. Define the operational question: latency, failures, saturation,
missing work or retained resources. Use trace context for causal correlation,
metrics for aggregation and bounded logs for useful event detail; none is a
substitute for business state or authorization.

Check semantic-convention stability and instrumentation versions before renaming
attributes. Use route templates rather than raw user-specific paths for
low-cardinality route dimensions. Do not attach credentials, arbitrary request
bodies, user IDs or full URLs to every metric. Decide which attributes are
allowed, how long data is retained, and who can read it. Propagated context and
baggage are not trusted identity. [HTTP conventions][otel-http], [sensitive
telemetry data][otel-security].

Bound export queues and account for sampling, dropped data and exporter failure.
A telemetry outage must not silently change whether the business operation
commits. Validate the configured exporter and a real failed request; an emitted
span alone does not prove usable correlation, correct aggregation or secret
redaction. Use existing collector filtering where appropriate instead of a new
application-wide redaction protocol.

## Prove the selected boundary

Exercise successful, malformed, unauthorized, conflicting and cancelled requests
as applicable. Include a real consumer or generated-client contract check, a
stale conditional write, personalized-cache isolation, and a telemetry failure
case when those features are part of the design. Keep tests tied to selected
requirements rather than requiring every protocol or test category everywhere.

[oas]: https://spec.openapis.org/oas/latest.html
[http]: https://www.rfc-editor.org/rfc/rfc9110.html
[preconditions]: https://www.rfc-editor.org/rfc/rfc9110.html#section-13
[caching]: https://www.rfc-editor.org/rfc/rfc9111.html
[problems]: https://www.rfc-editor.org/rfc/rfc9457.html
[otel-http]: https://opentelemetry.io/docs/specs/semconv/http/http-spans/
[otel-security]: https://opentelemetry.io/docs/security/handling-sensitive-data/
