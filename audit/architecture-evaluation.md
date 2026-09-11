# Architecture skill evaluation

Date: 2026-09-11. Scope: `design-software-boundaries`, not the entire suite.

## Catalog-only activation test

An independent test-engineer agent read only name/description frontmatter for
all 38 current skills. It did not see the skill bodies, prior changes, expected
answers, or audit notes. It selected the following routes:

1. New maintained Python CSV CLI module ownership: architecture skill.
2. Simplify five tightly coupled Go packages without exported changes:
   architecture skill.
3. Architecture request missing deployment/reliability requirements:
   architecture skill, with unresolved requirements identified.
4. Interview about feature-plan gaps, explicitly no architecture decision: no
   skill. `interrogate-plan` semantically fits but its current description
   requires explicit invocation.
5. Run existing Python formatter without structural changes: no skill.
6. “Split this service”: architecture skill; ask what boundary and inspect the
   reason, rather than assuming microservices.
7. Move database access out of UI, then remove obsolete adapter: architecture
   followed by `remove-legacy-compatibility` after supported consumers move.

The architecture positives, non-trigger, ambiguity, and composition behaved as
intended. The plan-interview case exposes an explicit-only catalog limitation,
not an architecture misroute. Preserve its existing invocation policy until the
full boundary audit establishes whether changing it is authorized.

## Forward test

An independent reviewer used the skill to design a maintained Python CLI for a
six-person operations team. The request specified vendor CSV input, required
columns, invalid-row reports, cleaned CSV output, in-memory files, no network or
plug-ins, and no implementation yet. No intended answer or suspected defect was
provided. The reviewer consulted the skill, relevant references, Python docs,
RFC 4180, and local Python CSV behavior.

Observed successes: direct calls, standard CSV/argument parsing, one package,
explicit I/O ownership, native packaging checks, and no service/framework/custom
format scaffolding. No repository files were created.

Observed defect: the first answer treated rejecting blank values, partial
output, and specific exit codes as settled policy, although it listed those
decisions as questions later. Added an entrypoint requirement to separate
established facts from domain, data-loss, and failure-policy assumptions. Also
clarified that the standards-first gate permits existing standard-library
implementations rather than discouraging dependency-free code indiscriminately.

The reviewer reran the same request with the changed entrypoint. It separated
requirements from unresolved row rules, output/exit policy, dialect/encoding,
Python version, and installation model. It retained the simple implementation
direction and offered flat versus src layout conditionally.

Limitations: the second run was a targeted follow-up, not a fresh blinded trial.
There was no implemented CLI, installed artifact, or measured production
outcome. The independent example is design evidence, not proof of all
architecture modes. The full collection still needs its own activation and
forward tests.
