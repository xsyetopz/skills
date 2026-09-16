# Worked implementation-plan review examples

## Missing producer before consumer

Plan:

1. Update deployment to read `manifest.v2.json`.
1. Change generator to emit `manifest.v2.json`.

Finding: step 1 can deploy a consumer before its required artifact exists. Cite
the deployment path and generator output. Correction: generate and validate the
new artifact first, then switch consumers under an explicit coexistence or
atomic rollout strategy.

## Unsupported compatibility work

A plan adds aliases for two historical CLI flags, but the support policy and
history show they were never released. Flag scope/compatibility invention; do
not require a deprecation phase for imaginary users.

## Not a finding

A plan uses an existing repository helper rather than the reviewer’s preferred
library. If it meets the contract, target versions, and verification needs, no
finding exists merely because another design is possible.
