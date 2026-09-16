# Phase 5: prepare and deliver the verified software release

Goal: deliver the verified baseline without introducing unverified changes.

## Release preparation

Produce only what the project needs:

- immutable release candidate identifier;
- build/package provenance and reproducible command where supported;
- deployment or installation procedure;
- data/config migration procedure;
- rollback/recovery procedure;
- compatibility and known-deviation notes;
- operational health checks;
- acceptance evidence linked to the verification matrix.

## Release freeze

After the verification phase completion check, any code/config change
invalidates the affected verification evidence. Cosmetic documentation changes
may be handled according to project policy, but do not assume they are free if
packaging hashes or signed artifacts change.

## Acceptance

The release phase completion check records:

- requirements baseline identifier;
- design baseline identifier;
- implementation/release candidate identifier;
- verification evidence identifier/location;
- approved deviations and residual risks;
- deployment/rollback readiness;
- authorized acceptance when the project requires human approval.

Do not manufacture approval. If a human or external authority is required and
has not acted, report the phase completion check as awaiting acceptance.
