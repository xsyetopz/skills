# Fit per product and ecosystem mappings

Cards for deciding whether [SemVer 2.0.0][spec] suits a product, what to
use when it does not, and where each ecosystem's version rules differ
from the spec. Each ecosystem fact links its primary source; recheck the
source before relying on a rule for a new tool version.

## Contents

- Does SemVer fit this product
- End-user apps: marketing version and build number
- Calendar versioning
- npm and Cargo: 0.x ranges and pre-releases
- Go modules: v prefix and major version suffix
- Python: PEP 440 is not SemVer
- Maven and Gradle ordering
- Container image tags

## Does SemVer fit this product

**Definition.** SemVer's numbers promise compatibility to consumers of a
declared public API. It fits when something depends on the product
programmatically and resolves versions by range. When no code consumes
the product, the number carries no compatibility signal and another
scheme may serve the user better.

| Product | Fit |
| --- | --- |
| Library, SDK, framework, plugin API | SemVer |
| CLI used in scripts | SemVer over flags, exit codes, machine output |
| HTTP API | SemVer or a major in the URL or header; minor and patch are often internal |
| Mobile or desktop app | Marketing version plus build number |
| Web SaaS deployed continuously | Often none, CalVer, or commit SHA |
| OS, distribution, large suite on a schedule | Often CalVer |

**Use when.**

- The user asks which scheme to use, or asks for SemVer on a product with
  no programmatic consumers.

**Do not use when.**

- The project already has a scheme: never convert an existing scheme
  (CalVer, marketing versions) without being asked; recommend at most.

**Example.**

```text
Q: SemVer for our iOS app?
A: The App Store shows CFBundleShortVersionString; nothing resolves it
   by range. Keep MAJOR.MINOR.PATCH there if you like the shape, and
   increment CFBundleVersion for every upload. No change to the scheme
   unless you ask.
```

**Cost removed.** Time spent judging "breaking" for a product nobody
consumes by range. Instrument: name the consumers before choosing.

**Verify.**

1. The report names the product's consumers and the scheme's reason.

## End-user apps: marketing version and build number

**Definition.** App stores separate the version users see from the
number that orders uploads:

- Apple: `CFBundleShortVersionString` is the release version, "three
  period-separated integers"; `CFBundleVersion` is the build version
  that "identifies an iteration (released or unreleased)"
  ([Info.plist keys][apple], archived reference).
- Android: `versionName` is "the version number shown to users";
  `versionCode` is "a positive integer used as an internal version
  number", must increase, and Google Play allows at most 2100000000
  ([versioning][android]).

Apple's fields and Android's `versionCode` hold only integers (and
periods for Apple), so SemVer pre-release and build suffixes do not fit
there; `versionName` is free text.

**Use when.**

- Versioning an iOS, macOS, or Android app.

**Do not use when.**

- The same code also ships as a library; version the library with
  SemVer separately.

**Example.**

```kotlin
android {
    defaultConfig {
        versionName = "4.2.0"   // shown to users
        versionCode = 40200     // must increase every upload
    }
}
```

**Cost removed.** Uploads rejected for a reused or lower build number,
and `-beta` suffixes in fields that accept only integers. Instrument:
the store's upload validation.

**Verify.**

1. The build number is higher than the last uploaded one.

## Calendar versioning

**Definition.** [CalVer][calver] builds versions from dates using tokens
such as `YYYY`, `YY`, `0Y`, `MM`, `0M`, `WW`, `DD`, `0D`, often with a
counter (`YYYY.MM.MICRO`). It signals age, not compatibility.
Zero-padded tokens (`0M`, `0D`) make a version that SemVer tools reject:
`2026.09.1` has a leading zero.

**Use when.**

- Releases are time-based and consumers do not pin by compatibility
  range, or the project already uses CalVer.

**Do not use when.**

- Consumers resolve by caret or tilde ranges; CalVer never signals a
  break.

**Example.**

```sh
python3 scripts/semver.py check 2026.9.1    # valid SemVer shape
python3 scripts/semver.py check 2026.09.1   # FAIL: leading zero
```

**Cost removed.** CalVer tags that break SemVer-based tooling.
Instrument: `semver.py check` on the chosen format.

**Verify.**

1. If tooling parses the version as SemVer, the format has no padded
   tokens.

## npm and Cargo: 0.x ranges and pre-releases

**Definition.** Both resolvers treat the left-most non-zero component as
the compatibility boundary: npm `^0.2.3` is `>=0.2.3 <0.3.0-0` and
`^0.0.3` is `>=0.0.3 <0.0.4-0` ([node-semver][node-semver]); Cargo `0.2.3`
is `>=0.2.3, <0.3.0` ([Cargo][cargo-req]). npm matches a pre-release only
when a comparator with the same `[major, minor, patch]` has one; Cargo
requirements exclude pre-releases unless asked. npm keeps a published
name and version unique forever ([npm publish][npm-publish]).

**Use when.**

- Choosing a 0.x increment for an npm package or crate.

**Do not use when.**

- Reasoning about other resolvers; Go, Python, and Maven differ.

**Example.**

```sh
bun -e 'const s = require("semver");
console.log(s.satisfies("0.3.0", "^0.2.3"),
  s.satisfies("1.3.0-beta.1", "^1.2.0"))'
# false false  (local run: Bun, semver 7.8.5)
```

**Cost removed.** A 0.x break published as patch reaching every
`^0.y.z` user. Instrument: `semver.satisfies` or `cargo update --dry-run`.

**Verify.**

1. For 0.x, breaking changes bump the left-most non-zero component.

## Go modules: v prefix and major version suffix

**Definition.** A Go module version is `v` plus a semantic version. From
major version 2, "module paths must have a major version suffix like
`/v2` that matches the major version"; suffixes are not allowed at v0 or
v1. Build metadata "is ignored for the purpose of comparing versions";
`+incompatible` marks pre-module v2+ releases ([Go modules][go-mod]).

**Use when.**

- Releasing v2 or later of a Go module.

**Do not use when.**

- The module is v0 or v1; adding `/v1` is an error.

**Example.**

```sh
go mod edit -module example.com/mod/v2
# update internal imports to example.com/mod/v2/...
git tag v2.0.0
```

**Cost removed.** A `v2.0.0` tag that the go command rejects, or
resolves only as `+incompatible` when the repository has no `go.mod`.
Instrument: `go list -m example.com/mod/v2@v2.0.0`.

**Verify.**

1. `go.mod` module path ends in `/vN` matching the tag's major.

## Python: PEP 440 is not SemVer

**Definition.** Python versions follow `[N!]N(.N)*[{a|b|rc}N][.postN]
[.devN]` ([version specifiers][pep440]). `1.0.0-rc.1` is accepted but
normalized to `1.0.0rc1`; `.postN` and `.devN` have no SemVer
equivalent; `+label` is a local version that PyPI "MUST NOT allow".

**Use when.**

- Publishing to PyPI or writing `pyproject.toml` versions.

**Do not use when.**

- Validating with the SemVer regex; `1.0.0rc1` fails it and is correct.

**Example.**

```text
SemVer intent      PEP 440 on PyPI
2.0.0-alpha.1      2.0.0a1
2.0.0-rc.2         2.0.0rc2
2.0.0+sha.abc      2.0.0 (keep the SHA in build logs, not the version)
```

**Cost removed.** Uploads rejected for a local version, or versions
renamed on upload. Instrument: `python3 -c "from packaging.version
import Version; print(Version('1.0.0-rc.1'))"` prints `1.0.0rc1`
(local run: `packaging` 26.3 through `uv run --with packaging`).

**Verify.**

1. The published version is in PEP 440 normal form without `+`.

## Maven and Gradle ordering

**Definition.** Maven's order is not SemVer 2.0.0: "Maven does not
special case the plus sign or consider build identifiers", and
qualifiers order `alpha < beta < milestone < rc = cr < snapshot < "" =
final = ga = release < sp` ([POM][maven]). Gradle splits on `. - _ +`,
ranks numeric parts above non-numeric, and ranks `rc`, `snapshot`,
`final`, `ga`, `release`, `sp` above other strings ([Gradle][gradle]).

**Use when.**

- Publishing JVM artifacts with pre-release or build suffixes.

**Do not use when.**

- Using `+` for build metadata in a JVM version; both tools order it as
  part of the version.

**Example.**

```text
2.0.0-alpha.1 < 2.0.0-beta.1 < 2.0.0-rc.1 < 2.0.0   (Maven, SemVer agree)
2.0.0-SNAPSHOT: Maven development build, not a SemVer pre-release
```

**Cost removed.** Resolvers picking a different "latest" than SemVer
would. Instrument: `mvn versions:display-dependency-updates` or Gradle's
dependency insight report.

**Verify.**

1. Pre-release names stay within the qualifiers both tools rank.

## Container image tags

**Definition.** An OCI tag matches `[a-zA-Z0-9_][a-zA-Z0-9._-]{0,127}`
([distribution spec][oci]); `+` is not allowed.

**Use when.**

- Tagging an image with a SemVer version.

**Do not use when.**

- Copying a version with build metadata into a tag unchanged.

**Example.**

```sh
v=2.0.0+sha.0a1b2c3
tag=$(printf '%s' "$v" | tr + _)   # 2.0.0_sha.0a1b2c3, or drop metadata
docker tag app:build "app:$tag"
```

**Cost removed.** `docker tag` failing on an invalid reference.
Instrument: the tag matches the regex above.

**Verify.**

1. `printf '%s' "$tag" | grep -Eqx '[a-zA-Z0-9_][a-zA-Z0-9._-]{0,127}'`.

[spec]: https://semver.org/spec/v2.0.0.html
[apple]: https://developer.apple.com/library/archive/documentation/General/Reference/InfoPlistKeyReference/Articles/CoreFoundationKeys.html
[android]: https://developer.android.com/studio/publish/versioning
[calver]: https://calver.org/
[node-semver]: https://github.com/npm/node-semver#caret-ranges-123-025-004
[cargo-req]: https://doc.rust-lang.org/cargo/reference/specifying-dependencies.html
[npm-publish]: https://docs.npmjs.com/cli/v10/commands/npm-publish
[go-mod]: https://go.dev/ref/mod#major-version-suffixes
[pep440]: https://packaging.python.org/en/latest/specifications/version-specifiers/
[maven]: https://maven.apache.org/pom.html#version-order-specification
[gradle]: https://docs.gradle.org/current/userguide/dependency_versions.html
[oci]: https://github.com/opencontainers/distribution-spec/blob/main/spec.md
