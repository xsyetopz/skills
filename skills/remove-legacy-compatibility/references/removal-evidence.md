# Consumer tracing and complete retirement

Reviewed 2026-09-12 against Node package exports and SemVer 2.0.0. Verify the
actual ecosystem loading contract for non-Node candidates.

## Establish an eligible candidate

For each alias, shim, deprecated path or fallback, record its canonical
replacement, exposure and retirement evidence. Trace direct imports, re-exports,
configuration strings, CLI registrations, dependency injection, reflection,
plugin discovery, package manifests, generated registries, tests and deployment
files. In an indexed repository, use its code graph first; text search
supplements dynamic/configuration evidence.

Classify consumers as active, historical, generated, external-supported or
unknown. A changelog mentioning an old API is historical evidence; a test
asserting the old API remains supported is an active contract until the
retirement decision says otherwise. Absence of imports in one repository does
not establish absence of published-package users.

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

Deleting `src/legacy.ts` alone leaves a broken advertised entrypoint, and stale
`dist/legacy.js` may survive incremental packaging. For a confirmed retirement,
remove the export mapping, wrapper source, wrapper-only resources and build
inclusion; rebuild through the existing clean packaging path and inspect the
archive. Retain tests for the canonical behavior. A wildcard export such as
`"./*"` can still expose an old filename, so inspect patterns as well as
explicit keys. Conditional `import`, `require` and `types` entries can have
different consumers. [Node package entrypoints][source-1].

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
