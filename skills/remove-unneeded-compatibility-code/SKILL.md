---
name: remove-unneeded-compatibility-code
description: >-
  Removes compatibility code proven unneeded: dead version branches, import
  fallbacks, deprecated aliases, polyfills, rolled-out flags. Checks support
  policy, callers, and stored data first. Use after dropping old versions. Not
  for code that only looks old.
---

# Remove Unneeded Compatibility Code

Delete compatibility paths that no supported version, consumer, or stored
data needs, and prove it.

## Workflow

1. Read the support policy: minimum runtime and platform versions,
   deprecation policy, release plan
   ([support policy](references/evidence-and-removal.md#support-policy)).
1. Find candidates: `python3 scripts/find_compat_python.py SRC
   --min-python X.Y` and `ruff check --select UP036` for Python; the
   searches in [candidates](references/candidates.md) for other
   ecosystems.
1. Trace consumers of each candidate: code, strings, config, generated
   registries, tests, packaging, persisted data, external users
   ([tracing](references/evidence-and-removal.md#consumer-tracing)).
1. Classify each as never required, retired, required, or unresolved;
   stop for a decision on unresolved public surfaces.
1. Remove each removable candidate completely (manifests, dependencies,
   exports, tests, docs) in its own change.
1. Verify on the minimum supported version with deprecation warnings as
   errors, and inspect the packaged artifact when exports changed.
1. Record the version impact.

## Route the candidate to a card

| Candidate | Card |
| --- | --- |
| `sys.version_info`, `#if NET...`, `cfg`, `@available` | [Version-gated branch](references/candidates.md#version-gated-branch) |
| `try: import X except ImportError` | [Import fallback](references/candidates.md#import-fallback) |
| Old name that warns and forwards | [Deprecated alias](references/candidates.md#deprecated-alias) |
| Old config keys, enum values, columns | [Persisted alias](references/candidates.md#persisted-or-serialized-alias) |
| Old import path in `exports` or a re-export module | [Package export alias](references/candidates.md#package-export-alias) |
| `hasattr`/`typeof` checks, polyfills | [Feature probe](references/candidates.md#feature-probe-and-polyfill) |
| Flag on everywhere | [Rolled-out flag](references/candidates.md#fully-rolled-out-feature-flag) |
| Old methods in generated clients | [Generated surface](references/candidates.md#generated-compatibility-surface) |
| Is it still supported? | [Support policy](references/evidence-and-removal.md#support-policy), [classification](references/evidence-and-removal.md#classification) |
| Who uses it? | [Consumer tracing](references/evidence-and-removal.md#consumer-tracing) |
| Removing it | [Complete removal](references/evidence-and-removal.md#complete-removal), [version impact](references/evidence-and-removal.md#version-impact) |
| Proving it | [Proof after removal](references/evidence-and-removal.md#proof-after-removal) |

## Rules

- Age, a failing test, or an empty local search does not authorize
  deleting a published surface; the support policy and consumer evidence
  do.
- Stored data outlives code: keep readers of old formats until a
  migration or policy retires them.
- Remove completely: no forwarding wrapper, hidden flag, or fallback left
  to keep a test green.
- Removing a supported public API is an incompatible change; ship it in a
  major release with a changelog entry.

## Bundled tools

- `scripts/find_compat_python.py PATH... [--min-python X.Y] [--json]`:
  lists version branches (marking dead ones), import fallbacks,
  deprecated aliases, and feature probes.
- `assets/examples/`: a `before/` package with three removable candidates
  and one required alias, the cleaned `after/` package, and `verify.sh`,
  which finds the candidates, checks callers, runs both test suites, and
  shows that removing the persisted-key alias breaks saved files.

## References

- [Compatibility candidates](references/candidates.md): version branches,
  import fallbacks, deprecated aliases, persisted aliases, package
  exports, feature probes, rolled-out flags, generated surfaces.
- [Evidence and removal](references/evidence-and-removal.md): support
  policy, consumer tracing, classification, complete removal, version
  impact, proof after removal.

## Completion evidence

The report lists every candidate with its class and the evidence behind
it (policy line, search results, data check), the removals made with the
tests run on the minimum version, packaging inspection when exports
changed, the version impact, and unresolved candidates with what is
missing.
