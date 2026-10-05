# Versioning Details

Sources: [SemVer 2.0.0][spec]. Re-read the linked source when a tool version is newer than the
claim.

## Contents

- [Increments](#increments)
- [0.y.z](#0yz)
- [Deprecation and Removal](#deprecation-and-removal)
- [Dependency Updates](#dependency-updates)
- [Accidental Breaking Release](#accidental-breaking-release)
- [Pre-release Trains and Precedence](#pre-release-trains-and-precedence)
- [Build Metadata](#build-metadata)
- [Ecosystems](#ecosystems)

## Increments

- Patch: backward-compatible bug fixes only.
- Minor: new backward-compatible functionality, or public API marked deprecated. Resets patch to 0.
- Major: any backward-incompatible change. Resets minor and patch to 0.
- The highest-ranked change decides. A bug fix that changes documented behavior consumers rely on is
  breaking.
- Removing or renaming a public function, flag, field, endpoint, exit code, or output format is
  major, including a rename with no behavior change.
- Read the public API diff, not commit types: a `fix:` can break and a `refactor:` can change public
  behavior.
- No written public API: ask which surfaces are public before choosing major or minor.

```sh
git diff --stat v1.4.7..HEAD -- src/ docs/   # then read the public parts
python3 scripts/semver.py bump 1.4.7 minor    # 1.5.0: added --json flag
python3 scripts/semver.py bump 1.4.7 major    # 2.0.0: removed --legacy
```

## 0.y.z

Item 4 of the [spec][spec]: major version zero is initial development and "Anything MAY change at
any time". The FAQ: if the software is used in production, or users depend on a stable API, it
should be 1.0.0 (recommend it; do not bump to 1.0.0 unasked). Resolvers make the minor the breaking
slot: npm `^0.2.3` is `>=0.2.3 <0.3.0-0` ([node-semver][node-semver]) and Cargo `0.2.3` is
`>=0.2.3, <0.3.0` ([Cargo][cargo-req]). So in 0.y.z bump minor for a break and patch for everything
else; a break published as `0.9.4` reaches every `^0.9.3` user.

```sh
python3 scripts/semver.py bump 0.9.3 minor   # 0.10.0: breaking in 0.x
python3 scripts/semver.py bump 0.9.3 patch   # 0.9.4: compatible fix
```

## Deprecation and Removal

Marking public API deprecated is a minor release; remove it in a later major, with at least one
minor in between that carries the deprecation (FAQ). A security fix that requires immediate removal
ships as a major with the reason stated.

```text
1.5.0  add --output; deprecate --out (warning, docs point to --output)
2.0.0  remove --out
```

Before a major, list the deprecated surface due for removal:

```sh
rg -n '@deprecated|#\[deprecated|\[Obsolete|DeprecationWarning|@Deprecated|@available\(.*deprecated'
```

## Dependency Updates

Per the FAQ, updating a dependency without changing the public API is compatible: patch when done to
fix a bug, minor when done to add functionality. It is breaking when consumers see it: a re-exported
type, a raised runtime minimum, a peer dependency's major. Check the manifest fields consumers read
(`engines`, `peerDependencies`, `requires-python`, `rust-version`), not the commit title.

```text
lodash 4.17.20 -> 4.17.21, internal only        -> patch
engines.node ">=18" -> ">=20"                    -> major
re-exported `Schema` type from zod 3 -> zod 4     -> major
```

## Accidental Breaking Release

Per the FAQ, once a break ships as minor or patch, do not modify or delete the release. Publish a
new minor that restores compatibility and document the offending version. Registries can mark it
without deleting (ask first; it changes installs for every user): [`npm deprecate`][npm-deprecate],
[`cargo yank`][cargo-publish], PyPI [yanked files][pypi-yank]. If the break was intended, the answer
is the next major, and the bad release is still documented.

```text
1.4.0  accidentally removed Client.close()   (published, kept)
1.5.0  restores Client.close(); notes name 1.4.0 as breaking
npm deprecate pkg@1.4.0 "Removes Client.close(); use 1.5.0"
```

## Pre-release Trains and Precedence

- A train is pre-releases of one target: `2.0.0-alpha.1`, `-beta.1`, `-rc.1`, `-rc.2`, `2.0.0`. A
  pre-release sorts below its release: `2.0.0-rc.1 < 2.0.0`.
- Precedence (spec item 11) compares dot-separated identifiers left to right: numeric ones
  numerically, alphanumeric ones in ASCII order, numeric below alphanumeric, a shorter set below a
  longer one with the same prefix. So `rc.2 < rc.10`, but `rc2 > rc10`. End on a numeric identifier.
- Plain string sort puts `rc.10` below `rc.9` and `1.10.0` below `1.9.0`; `sort -V` puts `1.0.0`
  below `1.0.0-rc.1`. Use `scripts/semver.py sort` or `compare`.
- Numeric identifiers have no leading zeros: `1.2.3-01` is invalid.
- Next after `2.0.0-rc.3` is `2.0.0-rc.4` or `2.0.0`; `semver.py bump 2.0.0-rc.3 prerelease` and
  `release` compute them.
- npm matches a pre-release only when a range comparator with the same `[major, minor, patch]` has
  one (`^1.2.0` excludes `1.3.0-beta.1`); Cargo excludes pre-releases unless the requirement names
  one ([node-semver][node-prerelease], [Cargo][cargo-req]).

## Build Metadata

Metadata after `+` is ignored by precedence: `1.0.0+a` and `1.0.0+b` are equal. Registries also
reject or drop it: npm keeps a name and version unique forever ([npm publish][npm-publish]) so a
metadata-only difference is the same version; crates.io rejects a metadata-only difference
([crates.io #6518][crates-6518]); PyPI rejects local `+label` versions ([PEP 440][pep440-local]);
OCI tags forbid `+`. Use it for provenance only, never to publish two artifacts of one version. Use
separate packages or pre-release identifiers for variants.

## Ecosystems

State these only from the source; do not validate them with the SemVer regex.

- npm and Cargo: the left-most non-zero component is the compatibility boundary: `^0.0.3` is
  `>=0.0.3 <0.0.4-0`.
- Go: a module version is `v` plus a semantic version. From major 2 the module path must end in a
  matching `/vN`; suffixes are not allowed at v0 or v1; `+incompatible` marks pre-module v2+ tags
  ([Go modules][go-mod]).

  ```sh
  go mod edit -module example.com/mod/v2
  # then fix imports; tag v2.0.0 only when asked
  ```

- Python: versions follow PEP 440 (`1.0.0rc1`, `.postN`, `.devN`), and `1.0.0-rc.1` normalizes to
  `1.0.0rc1` ([PEP 440][pep440]):

  ```text
  2.0.0-alpha.1 -> 2.0.0a1     2.0.0-rc.2 -> 2.0.0rc2
  ```

- Maven and Gradle order versions differently from SemVer: Maven does not special-case `+` and ranks
  `alpha < beta < milestone < rc < snapshot < "" < sp` ([POM][maven]); Gradle splits on `. - _ +`
  ([Gradle][gradle]). `-SNAPSHOT` is a development build, not a SemVer pre-release.
- OCI image tags match `[a-zA-Z0-9_][a-zA-Z0-9._-]{0,127}` ([distribution spec][oci]): replace `+`
  with `_` or drop it.
- End-user apps (store marketing version plus build number), CalVer: keep the existing scheme; see
  [Apple][apple] and [Android][android] for the two fields.
- A `v` prefix belongs to tags, not versions: manifests hold `1.2.3`.

[spec]: https://semver.org/spec/v2.0.0.html
[node-semver]: https://github.com/npm/node-semver#caret-ranges-123-025-004
[node-prerelease]: https://github.com/npm/node-semver#prerelease-tags
[cargo-req]: https://doc.rust-lang.org/cargo/reference/specifying-dependencies.html#default-requirements
[cargo-publish]: https://doc.rust-lang.org/cargo/reference/publishing.html
[npm-deprecate]: https://docs.npmjs.com/cli/v10/commands/npm-deprecate
[npm-publish]: https://docs.npmjs.com/cli/v10/commands/npm-publish
[pypi-yank]: https://packaging.python.org/en/latest/specifications/simple-repository-api/
[crates-6518]: https://github.com/rust-lang/crates.io/pull/6518
[pep440]: https://packaging.python.org/en/latest/specifications/version-specifiers/
[pep440-local]: https://packaging.python.org/en/latest/specifications/version-specifiers/#local-version-identifiers
[go-mod]: https://go.dev/ref/mod#versions
[maven]: https://maven.apache.org/pom.html#version-order-specification
[gradle]: https://docs.gradle.org/current/userguide/dependency_versions.html
[oci]: https://github.com/opencontainers/distribution-spec/blob/main/spec.md
[apple]: https://developer.apple.com/library/archive/documentation/General/Reference/InfoPlistKeyReference/Articles/CoreFoundationKeys.html
[android]: https://developer.android.com/studio/publish/versioning
