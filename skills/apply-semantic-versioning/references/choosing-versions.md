# Choosing the next version

Cards for deciding what a release's number must be (items 1 and 4-8 of
[SemVer 2.0.0][spec] and its FAQ): what the public API is, which change
forces which increment, how 0.y.z differs, and how pre-release trains and
build provenance fit. `scripts/semver.py bump` computes each result and
`assets/examples/verify.sh` runs the examples.

## Contents

- Declaring the public API
- Patch, minor, and major increments
- Initial development and 1.0.0
- Deprecation before removal
- Dependency updates
- An accidental breaking release
- Pre-release trains
- Build provenance with metadata

## Declaring the public API

**Definition.** Item 1: software using SemVer "MUST declare a public
API", in code or documentation; every increment is judged against it.
What counts as public depends on how consumers depend on the product:

| Product | Public API usually includes |
| --- | --- |
| Library or SDK | Exported names, signatures, types, thrown errors, documented behavior, supported runtime versions |
| CLI | Command and flag names, exit codes, machine-readable output (`--json`), config file keys, environment variables |
| HTTP API | Paths, methods, request and response fields, status codes, auth, pagination and rate-limit semantics |
| File format or protocol | Fields, encodings, and what readers accept; say whether old readers must read new files |
| Plugin host | Extension points, hook signatures, manifest schema, lifecycle order |

Human-readable output, internal modules, and undocumented behavior are
private unless the project says otherwise.

**Use when.**

- Choosing any increment, or the project has no written statement of
  what is public.

**Do not use when.**

- The product has no programmatic consumers; see
  [fit and ecosystems](fit-and-ecosystems.md#does-semver-fit-this-product).

**Example.**

```markdown
## Public API

Stable: the `slugify` package exports, the `slugify` CLI flags and exit
codes, and `--json` output. Not covered: human-readable messages and
anything under `slugify._internal`.
```

**Cost removed.** Arguments about whether a change is breaking.
Instrument: every change in the diff maps to a listed surface or to
"private".

**Verify.**

1. The README or docs name the public surfaces; the report cites them.

## Patch, minor, and major increments

**Definition.** Against the public API (items 6-8):

- Patch `Z`: backward-compatible bug fixes only.
- Minor `Y`: new backward-compatible functionality, or any public API
  marked deprecated; may also include private improvements and fixes.
  Resets patch to 0.
- Major `X`: any backward-incompatible change; may include minor and
  patch changes. Resets minor and patch to 0.

The highest-ranked change decides. A bug fix that changes documented
behavior consumers rely on is breaking.

**Use when.**

- Picking the next version for a release of 1.0.0 or later.

**Do not use when.**

- The version is 0.y.z; see the next card.
- Commit types alone decide it: a `fix:` can break and a `refactor:` can
  change public behavior, so read the public API diff.

**Example.**

```sh
git diff --stat v1.4.7..HEAD -- src/ docs/   # then read the public parts
python3 scripts/semver.py bump 1.4.7 minor    # 1.5.0: added --json flag
python3 scripts/semver.py bump 1.4.7 major    # 2.0.0: removed --legacy
```

**Cost removed.** Consumers on `^1.4.7` receiving a break, or skipping a
fix because it was labelled major. Instrument: each change is listed with
its surface and rank in the report.

**Verify.**

1. `semver.py compare PREVIOUS NEXT` prints `<`.
1. The report names the change that set the increment.

## Initial development and 1.0.0

**Definition.** Item 4: major version zero is for initial development;
"Anything MAY change at any time" and the API should not be considered
stable. Item 5: 1.0.0 defines the public API. The FAQ: start at 0.1.0,
increment minor per release, and "If your software is being used in
production, it should probably already be 1.0.0"; likewise if users
depend on a stable API or you worry about backward compatibility.
Resolvers treat 0.x specially: npm `^0.2.3` is `>=0.2.3 <0.3.0-0`
([node-semver][node-semver]) and Cargo `0.2.3` is `>=0.2.3, <0.3.0`
([Cargo][cargo-req]), so in practice 0.y minor is the breaking slot.

**Use when.**

- The version is 0.y.z, or the user asks when to go 1.0.0.

**Do not use when.**

- Staying on 0.y.z to avoid committing to compatibility while production
  users already depend on the API; the FAQ says that is the signal for
  1.0.0.

**Example.**

```sh
python3 scripts/semver.py bump 0.9.3 minor   # 0.10.0: breaking in 0.x
python3 scripts/semver.py bump 0.9.3 patch   # 0.9.4: compatible fix
python3 scripts/semver.py bump 0.9.3 major   # 1.0.0: API declared
```

**Cost removed.** `^0.9.3` users picking up a break published as 0.9.4.
Instrument: `bun -e 'console.log(require("semver").satisfies("0.10.0",
"^0.9.3"))'` prints `false`.

**Verify.**

1. For 0.x, breaking changes bump minor and the report says so.

## Deprecation before removal

**Definition.** Item 7 and the FAQ: marking public API deprecated is a
minor release; update the documentation, then remove it in a later major
release with at least one minor in between that carries the
deprecation.

**Use when.**

- Planning to remove or rename a public function, flag, field, or
  endpoint.

**Do not use when.**

- A security fix requires immediate removal; ship a major and say why.

**Example.**

```text
1.5.0  add --output; deprecate --out (warning, docs point to --output)
1.6.0  more features; --out still works
2.0.0  remove --out
```

**Cost removed.** Users who meet the removal with no warning or
migration path. Instrument: the deprecation appears in a minor release's
notes before the major.

**Verify.**

1. The removed item was marked deprecated in an earlier release.

## Dependency updates

**Definition.** The FAQ: updating a dependency without changing the
public API is compatible; it is patch when done to fix a bug and minor
when done to introduce functionality. It is breaking when it changes the
public API: a re-exported type, a raised runtime minimum, a peer
dependency's major.

**Use when.**

- The release range is mostly dependency bumps.

**Do not use when.**

- The dependency's types or errors are part of your public API; judge
  the change as if you made it.

**Example.**

```text
lodash 4.17.20 -> 4.17.21, internal only        -> patch
engines.node ">=18" -> ">=20"                    -> major
re-exported `Schema` type from zod 3 -> zod 4     -> major
```

**Cost removed.** Breaks hidden inside "chore(deps)" commits. Instrument:
the diff of manifest fields that consumers see (`engines`,
`peerDependencies`, `requires-python`, `rust-version`).

**Verify.**

1. Each dependency change is listed as private or with its public effect.

## An accidental breaking release

**Definition.** The FAQ: once a breaking change ships as minor or patch,
do not modify or delete the release; release a new minor that restores
backward compatibility, then document the offending version so users
know. Registries can mark it without deleting it: [`npm
deprecate`][npm-deprecate], [`cargo yank`][cargo-publish], and PyPI
[yanked files][pypi-yank].

**Use when.**

- A released non-major version breaks consumers.

**Do not use when.**

- The break was intended; then 2.0.0 is the answer and the bad release
  is still documented.

**Example.**

```text
1.4.0  accidentally removed Client.close()           (published, kept)
1.5.0  restores Client.close(); notes name 1.4.0 as breaking
npm deprecate pkg@1.4.0 "Removes Client.close(); use 1.5.0"
```

**Cost removed.** Re-published versions that differ by cache. Instrument:
the registry still lists 1.4.0 with its original checksum.

**Verify.**

1. No tag was moved; the fix version compares `>` the bad one.

## Pre-release trains

**Definition.** A train is a sequence of pre-releases of one target
version, ending in the final release: `2.0.0-alpha.1`, `-beta.1`,
`-rc.1`, `-rc.2`, `2.0.0`. Use a numeric last identifier so it sorts
numerically (`rc.11 > rc.2`; `rc11 < rc2` in ASCII).

**Use when.**

- Consumers should try a version before it is final.

**Do not use when.**

- Publishing to an ecosystem whose resolvers pick pre-releases by
  default for a dist-tag you did not set; publish npm pre-releases with
  `--tag next` so `latest` stays on the stable version
  ([npm publish][npm-publish]: `--tag` defaults to `latest`).

**Example.**

```sh
python3 scripts/semver.py bump 1.4.7 major --pre-id alpha  # 2.0.0-alpha.1
python3 scripts/semver.py bump 2.0.0-alpha.1 prerelease --pre-id rc
python3 scripts/semver.py bump 2.0.0-rc.1 prerelease       # 2.0.0-rc.2
python3 scripts/semver.py bump 2.0.0-rc.2 release          # 2.0.0
```

`bump ... prerelease --pre-id alpha` from `rc` fails with exit 1:
`alpha.1` would sort below `rc.2`.

**Cost removed.** Trains that sort out of order or skip the final
version. Instrument: `semver.py sort` of the train's tags.

**Verify.**

1. `semver.py sort` of all train versions returns them in release order.

## Build provenance with metadata

**Definition.** Build metadata carries information about the build, not
the release: `2.0.0+sha.0a1b2c3`, `2.0.0+ci.4812`, `2.0.0+20260928`. It
never changes precedence ([spec card](spec.md#build-metadata)).

**Use when.**

- The user needs to trace a binary, `--version` output, or an internal
  artifact back to its commit or CI run.

**Do not use when.**

- The metadata would be the only difference between two published
  artifacts; registries treat them as one version.

**Example.**

```sh
sha=$(git rev-parse --short HEAD)
python3 scripts/semver.py bump 2.0.0-rc.2 release --build "sha.$sha"
```

**Cost removed.** Asking "which commit is this binary?" Instrument:
`--version` output contains the SHA.

**Verify.**

1. `semver.py check` accepts the result; the registry's manifest version
   has no `+` where the registry strips or rejects it.

[spec]: https://semver.org/spec/v2.0.0.html
[node-semver]: https://github.com/npm/node-semver#caret-ranges-123-025-004
[cargo-req]: https://doc.rust-lang.org/cargo/reference/specifying-dependencies.html#default-requirements
[npm-publish]: https://docs.npmjs.com/cli/v10/commands/npm-publish
[npm-deprecate]: https://docs.npmjs.com/cli/v10/commands/npm-deprecate
[cargo-publish]: https://doc.rust-lang.org/cargo/reference/publishing.html
[pypi-yank]: https://packaging.python.org/en/latest/specifications/simple-repository-api/
