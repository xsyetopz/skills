# Versions, ranges, and validation

Finding a release's changes, verifying entries, and auditing the
changelog. `assets/examples/verify.sh` exercises every command
here in a throwaway repository.

## Contents

- Release range from tags
- Drafting entries from Conventional Commits
- Verifying an entry against its commit
- Changelog audit

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

## Changelog audit

**Definition.** `scripts/audit_changelog.py FILE [--json]` checks the Keep
a Changelog profile: release headings and dates, duplicate or misplaced
sections, unknown or empty categories, empty releases, and release
versions that are not [SemVer 2.0.0][semver] (`semver-format`). Exit
codes: 1 for errors, 0 for warnings alone, 2 for argument errors.

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

[cc]: https://www.conventionalcommits.org/en/v1.0.0/
[semver]: https://semver.org/spec/v2.0.0.html
