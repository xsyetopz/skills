# Versions, ranges, and validation

Choosing the version, finding a release's changes, and running the
bundled checks. `assets/examples/verify.sh` exercises every command
here in a throwaway repository.

## Contents

- Release range from tags
- Drafting entries from Conventional Commits
- Verifying an entry against its commit
- SemVer increment
- Pre-1.0 versions
- Pre-release and build metadata
- Changelog audit
- SemVer syntax audit

## Release range from tags

**Definition.** A release's changes are the commits reachable from the
release point but not from the previous release tag:
`git log PREV..HEAD`.

**Use when.** Preparing an Unreleased section or a release section.

**Do not use when.** The project releases from branches with backports.
Compute the range per branch; the latest tag may not be the previous
release on this branch.

**Example.**

```sh
prev=$(git describe --tags --abbrev=0)
git log --no-merges --oneline "$prev..HEAD"
git log --merges --first-parent --format='%s' "$prev..HEAD"  # PR merges
```

**Cost removed.** Missing or duplicated entries across releases.

**Verify.**

1. The range's first and last commits are named in the report.

## Drafting entries from Conventional Commits

**Definition.** `scripts/draft_entries.py RANGE` groups Conventional
Commits ([spec][cc]): `feat` → Added, `fix` → Fixed, `perf`/`revert` →
Changed, `!` or `BREAKING CHANGE:` → Changed marked breaking. It omits
`docs`, `test`, `ci`, `build`, `chore`, `style`, `refactor`, lists other
subjects as Unclassified, and prints a suggested SemVer increment.

**Use when.** The repository uses Conventional Commits.

**Do not use when.** Never publish the draft unedited; commit subjects are
not user-facing entries.

**Example.**

```sh
python3 scripts/draft_entries.py v1.0.0..HEAD --version 1.1.0 \
  --date 2026-09-20
```

**Cost removed.** Reading every commit to sort it. Measured: a range with
`feat`, `fix`, `docs`, `refactor`, and a non-conventional subject produced
Added and Fixed sections, kept the non-conventional subject as
Unclassified, and suggested `minor`.

**Verify.**

1. `python3 scripts/test_draft_entries.py` passes.

## Verifying an entry against its commit

**Definition.** Check each entry against the diff that implements it: the
behavior, names, and flags in the text exist in the release.

**Use when.** Before finalizing any entry.

**Do not use when.** Never skip it for Removed, Changed, and Security
entries.

**Example.**

```sh
git show --stat a1b2c3d
git grep -n 'cancel' v1.1.0 -- src/api/
```

**Cost removed.** Entries describing behavior that did not ship.

**Verify.**

1. Each entry has a commit or PR reference in the review notes.

## SemVer increment

**Definition.** For a stable public API: incompatible changes → MAJOR,
backward-compatible features (including deprecations) → MINOR,
backward-compatible fixes → PATCH ([SemVer 2.0.0][semver]).

**Use when.** The project adopts SemVer and must choose the next version.

**Do not use when.** The project uses CalVer or another scheme; do not
convert it.

**Example.** Removed or breaking Changed entries → 2.0.0 from 1.4.2; any
Added or Deprecated → 1.5.0; only Fixed or Security → 1.4.3. The draft
script's suggestion follows the same order.

**Cost removed.** Breaking users with a minor release.

**Verify.**

1. The chosen increment is at least the draft script's suggestion, and the
   public API diff (`git diff PREV..HEAD -- <public paths>`) supports it.

## Pre-1.0 versions

**Definition.** Major version zero (`0.y.z`) is for initial development.
Anything may change, and the public API should not be considered stable
([SemVer][semver]).

**Use when.** The project is below 1.0.0.

**Do not use when.** Never assume a patch is safe. Follow the project's
documented pre-1.0 policy; many projects bump minor for breaking changes.

**Example.** `0.4.2` → `0.5.0` for a breaking change under a
"minor-for-breaking" policy.

**Cost removed.** Surprise breakage in `0.x` patch releases.

**Verify.**

1. The policy is quoted from the project's docs in the review notes.

## Pre-release and build metadata

**Definition.** `1.2.0-rc.1` is a pre-release with lower precedence than
`1.2.0`. Numeric identifiers compare numerically (`rc.2 < rc.10`).
`+build.5` metadata does not affect precedence. A `v` tag prefix is not
part of SemVer ([SemVer][semver]).

**Use when.** Naming release candidates or builds.

**Do not use when.** Never sort releases by tag string; `git tag` order is
not SemVer precedence.

**Example.** `1.2.0-rc.1 < 1.2.0-rc.2 < 1.2.0 < 1.2.1`

**Cost removed.** Wrong "latest version" picks.

**Verify.**

1. `python3 -I scripts/audit_semver.py 1.2.0-rc.1 1.2.0+build.5`
   accepts both; `v1.2.3` and `01.2.3` are rejected.

## Changelog audit

**Definition.** `scripts/audit_changelog.py FILE [--json]` checks the Keep
a Changelog profile: release headings and dates, duplicate or misplaced
sections, unknown or empty categories, empty releases. Exit codes: 1 for
errors, 0 for warnings alone, 2 for argument errors.

**Use when.** After every changelog edit.

**Do not use when.** The file follows another format; the audit reports
false errors.

**Example.**

```sh
python3 -I scripts/audit_changelog.py CHANGELOG.md
python3 -I scripts/audit_changelog.py CHANGELOG.md --json
```

**Cost removed.** Structural errors found by readers.

**Verify.**

1. `verify.sh`: the example exits 0; the broken file exits 1 with
   `date-format`, `invalid-category`, `unreleased-order`,
   `duplicate-version`, `empty-version`, and `empty-category` errors.

## SemVer syntax audit

**Definition.** `scripts/audit_semver.py VERSION... | --from-tags |
--from-changelog FILE` validates versions with SemVer's published regular
expression. `--from-tags` accepts a leading `v` on tags.

**Use when.** Before tagging, and when auditing existing tags or headings.

**Do not use when.** Choosing the increment; it checks syntax only.

**Example.**

```sh
python3 -I scripts/audit_semver.py --from-tags
python3 -I scripts/audit_semver.py --from-changelog CHANGELOG.md
```

**Cost removed.** Tags that tooling cannot parse.

**Verify.**

1. `python3 -I scripts/test_validators.py` passes.

[cc]: https://www.conventionalcommits.org/en/v1.0.0/
[semver]: https://semver.org/spec/v2.0.0.html
