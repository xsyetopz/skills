---
name: apply-semantic-versioning
description: >-
  Applies Semantic Versioning 2.0.0: public API, next major, minor, or
  patch, 0.y.z, pre-releases, build metadata, precedence, and whether
  SemVer fits the product or ecosystem (npm, Cargo, Go, PyPI, app stores).
  Use when choosing or checking a version. Not for writing changelog
  entries.
---

# Apply Semantic Versioning

Give every release a version whose number tells its consumers what
changed, following [SemVer 2.0.0][spec] where it fits the product and the
ecosystem's own rules where they differ. The whole spec is covered:
public API, immutability, 0.y.z, increments, pre-release, build metadata,
precedence, and the FAQ.

## Workflow

1. Identify the product and its consumers: library, CLI, HTTP API, file
   format, plugin host, or end-user app; and the registry or store it
   ships to. Read the current version from the manifest and
   `git tag --list`.
1. Decide whether SemVer fits
   ([fit](references/fit-and-ecosystems.md#does-semver-fit-this-product)).
   Keep an existing scheme unless the user asks to change it; output the
   scheme and the reason.
1. Name the public API
   ([public API](references/choosing-versions.md#declaring-the-public-api)),
   then read the diff since the last release tag
   (`git diff PREV..HEAD`) and classify each public change as fix,
   compatible addition or deprecation, or breaking.
1. Choose the increment: the highest-ranked change decides; 0.y.z moves
   breaks into minor ([increments][increments],
   [0.y.z](references/choosing-versions.md#initial-development-and-100)).
1. Compute the version:
   `python3 scripts/semver.py bump PREV {major,minor,patch}`; add
   `--pre-id rc` for a pre-release train and `--build META` only when the
   user needs build provenance.
1. Map it to the ecosystem's syntax (PEP 440, Go `/vN`, container tags,
   app-store fields) with the matching card.
1. Check it: `python3 scripts/semver.py check NEW` and
   `python3 scripts/semver.py compare PREV NEW` prints `<`. For a
   repository, `python3 scripts/semver.py check --from-tags`.
1. Report the version, the change that decided it, and the check output.
   Do not tag, publish, or edit changelogs unless asked.

## Route what you see to a card

| What you see | Card |
| --- | --- |
| A version string to validate or parse | [Syntax](references/spec.md#version-syntax) |
| Someone wants to re-tag or re-publish a released version | [Immutability](references/spec.md#released-versions-are-immutable) |
| `-alpha`, `-rc.1`, testing builds | [Pre-release](references/spec.md#pre-release-versions), [trains](references/choosing-versions.md#pre-release-trains) |
| `+sha`, build numbers, or two artifacts per version | [Build metadata](references/spec.md#build-metadata), [provenance](references/choosing-versions.md#build-provenance-with-metadata) |
| Sorting tags, "which is newest", `rc.10` below `rc.9` | [Precedence](references/spec.md#precedence) |
| `v1.2.3` in a manifest or tag | [v prefix](references/spec.md#the-v-prefix-is-not-part-of-the-version) |
| No written public API; "is this breaking?" | [Public API](references/choosing-versions.md#declaring-the-public-api), [increments](references/choosing-versions.md#patch-minor-and-major-increments) |
| Version is 0.y.z, or "when do we go 1.0?" | [0.y.z and 1.0.0](references/choosing-versions.md#initial-development-and-100) |
| Removing or renaming public API | [Deprecation](references/choosing-versions.md#deprecation-before-removal) |
| Release range is mostly dependency bumps | [Dependencies](references/choosing-versions.md#dependency-updates) |
| A minor or patch release broke users | [Accidental break](references/choosing-versions.md#an-accidental-breaking-release) |
| App store, desktop app, SaaS; "should we use SemVer?" | [Fit](references/fit-and-ecosystems.md#does-semver-fit-this-product), [app stores](references/fit-and-ecosystems.md#end-user-apps-marketing-version-and-build-number) |
| Date-based versions | [CalVer](references/fit-and-ecosystems.md#calendar-versioning) |
| npm or Cargo, `^0.x` ranges | [npm and Cargo](references/fit-and-ecosystems.md#npm-and-cargo-0x-ranges-and-pre-releases) |
| Go module v2 or later | [Go modules](references/fit-and-ecosystems.md#go-modules-v-prefix-and-major-version-suffix) |
| PyPI, `pyproject.toml`, `rc1`, `.post1` | [PEP 440](references/fit-and-ecosystems.md#python-pep-440-is-not-semver) |
| Maven or Gradle artifacts, `-SNAPSHOT` | [JVM ordering](references/fit-and-ecosystems.md#maven-and-gradle-ordering) |
| Docker or OCI image tags | [Container tags](references/fit-and-ecosystems.md#container-image-tags) |

## Rules

- Judge increments by the public API diff, not commit types or
  diff size; a `fix:` that changes documented behavior is breaking.
- Never modify, re-tag, or re-publish a released version; registries
  cache it and npm and crates.io refuse the same version twice. Fix
  forward with a new version.
- Build metadata never orders or distinguishes releases: `1.0.0+a` and
  `1.0.0+b` have equal precedence, npm drops metadata, crates.io rejects
  a metadata-only difference, PyPI rejects `+local`, and OCI tags forbid
  `+`. Use it only for provenance.
- Sort by precedence (`semver.py sort`): string sort puts `rc.10` below
  `rc.9` and `1.10.0` below `1.9.0`; `sort -V` puts `1.0.0` below
  `1.0.0-rc.1`.
- In 0.y.z, npm and Cargo caret ranges treat the minor as the breaking
  component; bump minor for breaks and patch for everything else.
- `v` belongs to tags, not versions; manifests hold `1.2.3`. Go module
  tags are the exception that requires `v`.
- Do not convert a product's existing scheme (CalVer, marketing version
  plus build number) without being asked; recommend instead.
- Use the ecosystem's grammar where it differs (PEP 440 `1.0.0rc1`, Go
  `/vN`); do not validate those with the SemVer regex.
- State ecosystem rules from the linked primary sources in the cards;
  re-read the source when a tool version is newer than the card's.

## Bundled tools

- Run `scripts/semver.py` (Python 3 standard library, never prompts;
  `--help` lists every option):
  - `check VERSION... [--from-tags] [--json]`: official regex; with
    `--from-tags`, a tag's leading `v` passes with a note.
  - `compare A B`: prints `<`, `=`, or `>`; build metadata ignored.
  - `sort VERSION... [--json]`: ascending precedence, stable for
    build-only differences.
  - `bump VERSION {major,minor,patch,prerelease,release}
    [--pre-id ID] [--build META]`: spec resets; drops old metadata.
  - Exit 0 ok, 1 invalid version or a bump that would not raise
    precedence, 2 usage error. Errors go to stderr and say what was
    expected.
- Run `sh assets/examples/verify.sh` to exercise every command, including
  `--from-tags` in a throwaway Git repository; exit 0 when all pass.
- `scripts/test_semver.py` holds the grammar, precedence, and bump tests.

## References

- [Spec](references/spec.md): load for syntax, the BNF and regex,
  immutability, pre-release, build metadata, precedence, the `v` prefix.
- [Choosing versions](references/choosing-versions.md): load before
  picking an increment: public API, increments, 0.y.z and 1.0.0,
  deprecation, dependency updates, accidental breaks, pre-release
  trains, build provenance.
- [Fit and ecosystems](references/fit-and-ecosystems.md): load when the
  product is not a library, or before publishing to npm, crates.io, Go,
  PyPI, Maven, Gradle, a container registry, or an app store.

## Completion evidence

The report states the product and its consumers, the scheme and why,
the previous and new versions, the public change that decided the
increment, the ecosystem mapping if any, and the output of
`semver.py check` and `semver.py compare PREV NEW`. Ecosystem claims cite
the card's source.

## Stop and ask

- The project has no declared public API and the diff's surfaces are
  ambiguous: ask which are public before choosing major versus minor.
- The user asks to re-publish or move a released version: explain item 3
  and ask before any destructive registry or tag operation.
- The user wants build metadata to separate published artifacts: explain
  the registry's rule and ask which alternative they want.
- Changing an existing version scheme: confirm before editing manifests.
- Changelog wording and release notes belong to `$update-changelogs`.

[spec]: https://semver.org/spec/v2.0.0.html
[increments]: references/choosing-versions.md#patch-minor-and-major-increments
