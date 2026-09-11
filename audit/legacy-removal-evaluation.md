# Legacy retirement evaluation

Evaluated 2026-09-12. Renamed `legacy-cleanup` to `remove-legacy-compatibility`
and consolidated five fragmented references into one
consumer/packaging/persistence workflow. Preserved explicit-only invocation.

## Sources and scope

Rechecked the official [Node package-entrypoint contract][node] and
[SemVer 2.0.0](https://semver.org/). Export maps, conditional routes, and
package contents must agree; deprecation alone does not authorize public API
removal. The guidance distinguishes historical, generated, active, and unknown
consumers. Persisted values can remain supported without current writers.

## Independent forward evaluation

An isolated Node package fixture contained a canonical normalizer, a retired
`./legacy` public export, a still-supported saved-mode reader, historical
release notes, and previously built output. Its written retirement decision
authorized only the old entrypoint removal, not data migration or publication.

A fresh-context evaluator received the skill, fixture, and task, without the
expected patch. It removed the wrapper and export, retained saved-mode behavior,
version and history, and passed two tests plus real npm archive inspection.

Integration found a material failure: the evaluator manually removed stale
`dist/legacy.js` but left the copy-only build unchanged. Reintroducing the
previously generated artifact and rebuilding reproduced its survival. Thus the
first green archive was not durable evidence of complete build-path retirement.

The integrated fixture corrects the existing build's owned `dist` clean step.
Rebuilding with stale output now removes the retired artifact. The skill's
entrypoint and reference explicitly prohibit hand-editing generated output and
require checking stale incremental output, not just a one-time clean archive. No
generic cleanup script or new build dependency was added to the skill.

## Validation

With Node 26.8.2 and npm 11.19.1:

- Both original behavior tests pass; canonical normalization and saved-mode
  compatibility remain intact.
- Root-package import succeeds; the retired route fails with
  `ERR_PACKAGE_PATH_NOT_EXPORTED`, not an unrelated missing-build error.
- Real `npm pack` produces only `package.json` and `dist/index.js`.
- Extracting that archive into an isolated consumer reproduces the retained API
  and rejected retired route.
- Original fixture source, tests, version, and historical notes are preserved.

The raw forward report is `/tmp/legacy-forward-result.md`; integrated output is
`/tmp/legacy-forward.aYzjgn`, with archive consumer at
`/tmp/legacy-packed-consumer`. The raw report predates the build-path
correction.

The package passes both skill validators, strict Markdown, local-link and
metadata checks. These tests do not prove remote consumer retirement, arbitrary
reflection/plugin registries, database migrations, or non-Node packaging. Those
require evidence at their actual compatibility boundary.

[node]: https://nodejs.org/api/packages.html#package-entry-points
