# Threat review and evidence

## Model the actual system

Use the repository's existing threat model or a short boundary inventory, not a
new document framework. Identify valuable data, entrypoints, processes, stores,
identities, and the assumptions each boundary relies on. Include build and admin
paths where they can affect the reviewed feature. Draw a small Mermaid data-flow
diagram only when it clarifies these relationships.

For each relevant boundary, ask what an attacker can control and what privileged
effect follows. Spoofing, tampering, repudiation, disclosure, denial of service,
and privilege escalation are useful STRIDE prompts, not six mandatory findings.
Record mitigations and how to verify them. Revisit the model after meaningful
boundary changes. [OWASP threat modeling][threats] describes this process and
explicitly does not prescribe one universal method.

For web applications, select applicable requirements from a specific published
[OWASP ASVS release][asvs]. Record its version with any requirement identifiers;
do not copy identifiers from memory or claim full ASVS coverage from a sample.
The inspected upstream release is 5.0.0; the development branch is not the same
contract. For mobile/native/embedded systems, investigate their platform
security guidance instead of imposing web-only controls.

[NIST's SSDF publication index][ssdf] distinguishes final guidance from drafts.
At review on 2026-09-11 it lists SSDF 1.1 as final and 1.2 as draft. Verify that
status before a new audit; do not call a draft a compliance requirement or
assume any framework is legally required merely because it exists.

## Establish reachability before severity

Trace source to sink, including normalization, authentication, authorization,
parameterization, escaping, sandboxing, transaction boundaries, and error paths.
An unsafe-looking helper is not necessarily reachable by an adversary;
conversely, a safe framework default can be disabled by a wrapper or
configuration override. Inspect callers before concluding either way.

Keep three evidence classes distinct:

- Confirmed defect: observed or fully traced unauthorized behavior under stated
  preconditions.
- Design risk: a required control is absent from the design; implementation and
  deployment still need verification.
- Unresolved hypothesis: evidence is missing or contradictory. State the exact
  observation needed to resolve it instead of assigning confident severity.

Rank by attacker access, exposure, business impact, blast radius, and existing
controls. Use the project's severity system. If CVSS is required, use its actual
specified version and calculator; do not invent a score from a label.

## Example: tenant export review

An authenticated export handler accepts a record ID, loads the record by ID, and
writes its contents to the response. The handler's user object includes a tenant
ID. This is not enough evidence to assert cross-tenant disclosure: inspect
whether the query, row-level policy, or authorization middleware constrains the
read.

If no effective constraint exists, reproduce locally with synthetic tenants A
and B. Authenticate as A and request B's known test record. Prove both the
unauthorized bytes and the missing check. A repaired path should retain A's
valid export and reject B's export without disclosing its contents or causing
side effects. Match the application's existing not-found/forbidden policy rather
than inventing one. Apply authorization to the authoritative resource operation;
opaque IDs and UI hiding are not substitutes. [OWASP authorization
guidance][authorization].

Do not add duplicate checks to every helper if an unavoidable upstream boundary
already enforces the invariant. Test that the boundary is in fact unavoidable,
including alternative routes, batch operations, and background work in scope.

## Close the review

A finding needs a precise location or design element, preconditions, observed
data/control flow, impact, minimal repair, and a regression criterion. Include
the smallest necessary synthetic payload or trace; redact credentials and
personal data. Prefer the project's issue/report format. Use SARIF only when a
consumer expects SARIF, and let existing tooling emit it.

For a fix, rerun the reproducer and an authorized-success case, then relevant
integration checks. Track mitigated, accepted, and unresolved risks separately.
State excluded components, unavailable environments, and version assumptions. Do
not advertise a static scan or a small test suite as proof of security.

[threats]:
  https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html
[asvs]: https://github.com/OWASP/ASVS/tree/v5.0.0
[ssdf]: https://csrc.nist.gov/projects/ssdf/publications
[authorization]:
  https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html
