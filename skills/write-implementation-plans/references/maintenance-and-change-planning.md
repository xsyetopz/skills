# Plan changes to an existing software system

Identify what survives release: supported users/platforms, data, interfaces,
dependencies, deployment artifacts, operational ownership, and known defects.
Reuse the existing support policy. Unknown support duration or staffing is a
decision to resolve, not permission to promise indefinite maintenance.

Classify incoming work by its effect: corrective repairs restore intended
behavior; adaptive changes address the environment; perfective changes improve
capability or quality; preventive work reduces evidenced future failure or
change cost. These categories help reveal omitted work, not justify speculative
rewrites or four mandatory backlogs.

For each material change, trace affected requirements, callers, data formats,
tests, build/configuration identities, release notes, and operator procedures.
Assess compatibility and migration before estimating implementation alone.
Record acceptance criteria for the changed behavior and retained consumers. Keep
change-request priority distinct from incident urgency.

Plan intake and triage, ownership, capacity for supported obligations,
dependency/security update response where applicable, and how urgent work
displaces forecast scope. Specify actionable monitoring and recovery evidence
when the product is operated, not a universal on-call organization. Preserve the
ability to identify which source/configuration produced an affected release.

For migration, define supported old/new combinations, rollout order, data
conversion, reconciliation, rollback limits, and the evidence that ends support
for the old path. For retirement, identify consumers and retained records,
communication obligations, final data disposition, and acceptance of replacement
behavior. Plan authorized effects; do not execute removals or publication here.

Example: a renamed configuration key still appears in supported installations.
Plan compatibility, migration documentation, a supported observation window, and
a retirement decision based on consumer evidence. Do not delete the alias
because repository search finds no callers. Once retirement is established, the
compatibility-removal workflow owns implementation and package verification.

Finish with owned obligations where known, unresolved support decisions, change
dependencies, acceptance/recovery checks, and capacity impacts in the delivery
plan. A maintenance plan is not a verified repair, an executed rollback, or
evidence that compatibility can already be removed.
