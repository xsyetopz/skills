# SemVer 2.0.0 syntax, pre-release, build metadata, and precedence

Cards for the grammar and ordering rules of [Semantic Versioning
2.0.0][spec] (items 2, 3, 9, 10, 11, the BNF, the official regex, and the
`v` prefix FAQ). `scripts/semver.py` implements every rule here and
`assets/examples/verify.sh` runs each example below.

## Contents

- [Version syntax](#version-syntax)
- [Released versions are immutable](#released-versions-are-immutable)
- [Pre-release versions](#pre-release-versions)
- [Build metadata](#build-metadata)
- [Precedence](#precedence)
- [The v prefix is not part of the version][toc-1]

[toc-1]: #the-v-prefix-is-not-part-of-the-version

## Version syntax

**Definition.** A normal version is `X.Y.Z`: three non-negative integers
without leading zeros (item 2). An optional pre-release follows a `-`,
optional build metadata follows a `+`, in that order. The [BNF][bnf]
top level:

```text
<valid semver> ::= <version core>
                 | <version core> "-" <pre-release>
                 | <version core> "+" <build>
                 | <version core> "-" <pre-release> "+" <build>
```

Identifiers are dot-separated and use only `[0-9A-Za-z-]`; none may be
empty. A numeric pre-release identifier has no leading zero; an
alphanumeric one (containing a letter or `-`) may start with zeros, so
`1.0.0-0A` and `1.0.0-00A` are valid while `1.0.0-01` is not. Build
identifiers have no leading-zero rule: `1.0.0+001` is valid. The spec sets
no size limit. The [official regex][regex], split here only to fit the
page, is used with `re.ASCII` so `\d` matches ASCII digits only:

```python
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$",
    re.ASCII,
)
```

**Use when.**

- Writing, validating, or parsing any version string, tag, or manifest
  `version` field that claims to be SemVer.

**Do not use when.**

- The ecosystem has its own grammar (PEP 440, Maven, Apple bundle
  versions); validating those with this regex rejects valid versions
  and accepts invalid ones. See the ecosystem cards in
  [fit and ecosystems](fit-and-ecosystems.md).

**Example.**

```sh
python3 scripts/semver.py check 1.0.0-0A 1.0.0-x-y-z.-- 1.0.0-alpha+001
python3 scripts/semver.py check 1.2 01.2.3 1.2.3-01 1.2.3-a..b 1.2.3-a_b
# FAIL  1.2  - '1.2': expected MAJOR.MINOR.PATCH, got 2 ...
# FAIL  1.2.3-01  - '1.2.3-01': numeric pre-release identifier '01' ...
```

Runnable: `assets/examples/verify.sh`.

**Cost removed.** Versions a registry or resolver rejects at publish
time, or sorts wrongly after publish. Instrument: `semver.py check`
exit status (0 valid, 1 invalid) with the failing rule named.

**Verify.**

1. `python3 scripts/semver.py check VERSION...` exits 0.
1. For a repository: `python3 scripts/semver.py check --from-tags`.

## Released versions are immutable

**Definition.** Item 3: once a version is released, its contents must not
be modified; any change is released as a new version. Registries enforce
this: npm never reuses a name and version, even after unpublish
([npm publish][npm-publish]); a crates.io publish "is generally
permanent. The version can never be overwritten"
([cargo publishing][cargo-publish]).

**Use when.**

- A released artifact is wrong: a bad build, a missing file, a breaking
  change shipped as minor.

**Do not use when.**

- Nothing has been published or tagged publicly yet; a local, unpushed
  tag can still be moved.

**Example.**

```sh
# 1.4.0 shipped without its type declarations.
python3 scripts/semver.py bump 1.4.0 patch   # 1.4.1; never re-tag 1.4.0
```

**Cost removed.** Consumers whose lockfiles or caches hold the old 1.4.0
contents getting different code for the same version. Instrument:
`git tag --points-at` and the registry's version list show one artifact
per version.

**Verify.**

1. The fix ships under a new version; the old tag still points at its
   original commit (`git rev-parse 1.4.0^{commit}` unchanged).

## Pre-release versions

**Definition.** Item 9: `-` plus dot-separated identifiers after the
patch, such as `1.0.0-alpha`, `1.0.0-alpha.1`, `1.0.0-0.3.7`,
`1.0.0-x.7.z.92`, `1.0.0-x-y-z.--`. A pre-release "indicates that the
version is unstable and might not satisfy the intended compatibility
requirements as denoted by its associated normal version", and it has
lower precedence than that normal version.

**Use when.**

- Publishing a build for testing before the final version: alpha, beta,
  release candidates.

**Do not use when.**

- Marking build provenance (commit, CI run); that is build metadata.
- The ecosystem does not accept `-` pre-releases (PyPI uses `1.0.0rc1`).

**Example.**

```sh
python3 scripts/semver.py bump 1.4.7 major --pre-id rc   # 2.0.0-rc.1
python3 scripts/semver.py compare 2.0.0-rc.1 2.0.0       # <
```

**Cost removed.** Testers or resolvers treating an unstable build as the
final release. npm ranges match a pre-release only when a comparator with
the same `[major, minor, patch]` also has a pre-release
([node-semver][node-semver]); Cargo requirements exclude pre-releases
unless asked ([Cargo][cargo-req]).

**Verify.**

1. `semver.py compare PRERELEASE FINAL` prints `<`.

## Build metadata

**Definition.** Item 10: `+` plus dot-separated identifiers after the
patch or pre-release, such as `1.0.0-alpha+001`, `1.0.0+20130313144700`,
`1.0.0-beta+exp.sha.5114f85`. Build metadata "MUST be ignored when
determining version precedence"; two versions that differ only in build
metadata have the same precedence.

**Use when.**

- Recording provenance in a build that is not a separate release: commit
  SHA (`+sha.0a1b2c3`), CI build number (`+ci.4812`), build date
  (`+20260928`), or the bundled upstream version.

**Do not use when.**

- Two published artifacts must be told apart. Registries treat
  `1.0.0+a` and `1.0.0+b` as one version:
  - npm: node-semver drops it; local run (Bun 1.x, `semver` 7.8.5):
    `semver.valid("1.0.0+abc")` returns `1.0.0` and
    `semver.eq("1.0.0+a", "1.0.0+b")` returns `true`.
  - crates.io rejects publishing a version that differs from an existing
    one only in build metadata ([crates.io PR 6518][crates-6518], merged
    2023-05-30); Cargo says metadata "is generally ignored"
    ([manifest][cargo-version]).
  - PyPI: `+` starts a PEP 440 local version, which PyPI "MUST NOT allow"
    ([version specifiers][pep440]).
  - Container tags cannot contain `+` ([OCI tag grammar][oci]).
  - Maven does not special-case `+` at all ([POM][maven]); Gradle treats
    `+` as a plain separator, so `1.0.0+a` and `1.0.0+b` sort as
    different versions ([Gradle][gradle]).
- Ordering is needed; use a pre-release or a new patch instead.

**Example.**

```sh
python3 scripts/semver.py bump 2.0.0-rc.3 release --build sha.0a1b2c3
# 2.0.0+sha.0a1b2c3
python3 scripts/semver.py compare 1.0.0+a 1.0.0+b   # =
```

**Cost removed.** A second artifact that silently replaces, collides
with, or fails to publish next to the first. Instrument: `semver.py
compare` prints `=` for build-only differences.

**Verify.**

1. `semver.py check` accepts the version; `compare` against the version
   without metadata prints `=`.
1. The target registry's rule above was read before relying on metadata.

## Precedence

**Definition.** Item 11: compare major, minor, patch numerically, in that
order. With equal cores, a pre-release is lower than the normal version.
Two pre-releases compare identifier by identifier, left to right:
numeric identifiers numerically; alphanumeric identifiers in ASCII order;
numeric lower than alphanumeric; if all preceding identifiers are equal,
the larger set wins. Build metadata never counts. The spec's chain:

```text
1.0.0-alpha < 1.0.0-alpha.1 < 1.0.0-alpha.beta < 1.0.0-beta
  < 1.0.0-beta.2 < 1.0.0-beta.11 < 1.0.0-rc.1 < 1.0.0
```

**Use when.**

- Choosing the latest release from tags, sorting versions, or checking
  that a new version is higher than the last.

**Do not use when.**

- Sorting with plain string or natural sort: string sort puts
  `1.0.0-beta.11` before `1.0.0-beta.2` and `1.10.0` before `1.9.0`;
  `sort -V` puts `1.0.0` before `1.0.0-rc.1` (local run: macOS `sort`
  2.3-Apple).
- ASCII order surprises: `RC` sorts before `alpha` (uppercase first), so
  keep identifier case consistent.

**Example.**

```sh
python3 scripts/semver.py compare 1.0.0-beta.11 1.0.0-beta.2   # >
python3 scripts/semver.py sort 1.0.0 1.0.0-rc.1 1.0.0-alpha.beta
```

**Cost removed.** Releasing a "latest" that is older than the actual
latest. Instrument: `semver.py sort` output and `compare` symbols.

**Verify.**

1. `semver.py compare PREVIOUS NEXT` prints `<` before tagging NEXT.

## The v prefix is not part of the version

**Definition.** The spec FAQ: `v1.2.3` is not a semantic version; the
version is `1.2.3`. Prefixing a tag with `v` is a convention. Go module
versions require it ([Go modules][go-mod]).

**Use when.**

- Reading versions from tags, or writing manifest `version` fields.

**Do not use when.**

- Writing a Go module tag: `v` is required there.

**Example.**

```sh
python3 scripts/semver.py check v1.2.3              # FAIL, exit 1
python3 scripts/semver.py check --from-tags         # PASS  v1.2.3 (note)
```

**Cost removed.** Manifests with `version = "v1.2.3"` that a registry
rejects. Instrument: `semver.py check` on the manifest value.

**Verify.**

1. Manifest values pass `semver.py check`; tags pass `check --from-tags`.

[spec]: https://semver.org/spec/v2.0.0.html
[bnf]: https://semver.org/spec/v2.0.0.html#backusnaur-form-grammar-for-valid-semver-versions
[regex]: https://semver.org/spec/v2.0.0.html#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string
[npm-publish]: https://docs.npmjs.com/cli/v10/commands/npm-publish
[cargo-publish]: https://doc.rust-lang.org/cargo/reference/publishing.html
[cargo-version]: https://doc.rust-lang.org/cargo/reference/manifest.html#the-version-field
[cargo-req]: https://doc.rust-lang.org/cargo/reference/specifying-dependencies.html
[node-semver]: https://github.com/npm/node-semver#prerelease-tags
[crates-6518]: https://github.com/rust-lang/crates.io/pull/6518
[pep440]: https://packaging.python.org/en/latest/specifications/version-specifiers/#local-version-identifiers
[oci]: https://github.com/opencontainers/distribution-spec/blob/main/spec.md
[maven]: https://maven.apache.org/pom.html#version-order-specification
[gradle]: https://docs.gradle.org/current/userguide/dependency_versions.html
[go-mod]: https://go.dev/ref/mod#versions
