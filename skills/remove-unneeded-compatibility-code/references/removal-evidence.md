# Verify consumers before retiring software compatibility

Original source note dated 2026-09-12, referring to Node package exports and
SemVer 2.0.0. Verify the actual ecosystem loading contract for non-Node
candidates.

## Establish an eligible candidate

For each alias, shim, deprecated path or fallback, identify its surviving
behavior, exposure, and support authority. Distinguish support never required
from support actually retired; the former needs no invented deprecation cycle.
Trace direct imports, re-exports, configuration strings, CLI registrations,
dependency injection, reflection, plugin discovery, package manifests, generated
registries, tests and deployment files. Use the available evidence suitable for
each consumer. Check a code graph's freshness before relying on it; combine
source, configuration, history, and dynamic evidence where the boundary requires
them.

Classify consumers as active, historical, generated, external-supported, or
unknown. A changelog can record a former promise. A test can record intended
support or merely mirror an agent-invented fallback. Trace each to the current
request and applicable public contract before deciding. Neither a test nor an
empty import search independently settles whether published-package users must
still be supported.

If the surface is still supported, retain it and continue independent eligible
removals. Do not silently expand cleanup into consumer migration.

## Package-boundary example

Suppose a package exposes:

```json
{
  "exports": {
    ".": "./dist/index.js",
    "./legacy": "./dist/legacy.js"
  }
}
```

### Deleting only the wrapper source

**Deciding condition:** The user has authorized retirement of the public
`./legacy` entry point under its support policy. Consumer evidence establishes
what must migrate; the canonical package remains supported.

```sh
rm src/legacy.ts
# Running source tests alone misses package exports and stale build output.
```

Why it fails:

- `exports` still advertises `./legacy`;
- stale `dist/legacy.js` can survive incremental packaging;
- source-tree tests do not prove the published archive contract.

### Retire the complete confirmed public route

Remove the export mapping, wrapper source, wrapper-only resources, and build
inclusion together. Rebuild through the existing clean packaging path and
inspect the archive. Retain tests for the canonical behavior.

Why it works:

- package metadata and archive contents agree;
- the supported entrypoint remains covered;
- the retired entrypoint fails because it is absent, not because the whole
  package failed to build.

Check:

- install the produced archive in a clean consumer, import the canonical path,
  and confirm `./legacy` is neither exported nor packaged.

A wildcard export such as `"./*"` can still expose an old filename, so inspect
patterns as well as explicit keys. Conditional `import`, `require`, and `types`
entries can have different consumers. [Node package entrypoints][source-1].

Removing a supported public path is ordinarily an incompatible API change under
SemVer; a deprecation notice does not itself terminate the promise. For an
internal-only alias with all callers gone, removal can be a nonbreaking
implementation detail. Classify the contract before choosing release
notes/version impact. [SemVer](https://semver.org/).

[source-1]: https://nodejs.org/api/packages.html#package-entry-points

## Generated and serialized surfaces

Trace generated output to schema/registry inputs, generator version, invocation
and artifact owner. Remove the obsolete registration at its source and
regenerate; hand-deleting generated output can resurrect it on the next run.
Preserve vendored licenses and upstream provenance. A generated client may
retain a method because supported server versions still expose it; this is not
automatically dead code.

Serialized enum values, persisted settings, database fields and command IDs
survive beyond code references. Example: no current code writes `mode:"legacy"`,
but supported saved documents may still contain it. A loader fallback remains
active until the storage/support contract confirms those documents no longer
need it. Retiring the reader requires an authorized migration or compatibility
decision, outside confirmed-cleanup scope.

## Retire without residual routes

Remove the eligible surface and its dedicated tests, fixtures, docs, assets and
packaging entries together. Update current examples to the canonical route;
preserve useful historical migration records. Do not leave an alias, forwarding
wrapper, hidden flag or catch-all fallback merely to make a test pass when
complete removal was requested.

Check retained consumers with the repository's focused tests, compile/type
checks and export/package inspection relevant to the boundary. Verify no active
route references removed resources, including case-sensitive paths and generated
manifests. Check exported archive contents to confirm retirement. Test the
retained public entrypoint from the produced package, not only its source tree.
Verify that the retired public route fails for the intended reason; a missing
canonical build must not make a negative test appear successful. If incremental
output retains obsolete files, correct the owned build/packaging clean step
rather than hand-editing generated files or deleting arbitrary output
directories.

Report completed retirements, evidence and unresolved candidates separately.
Identify the missing consumer evidence for each unresolved candidate.
