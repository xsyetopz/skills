---
name: update-changelog
description: >-
  Updates CHANGELOG.md and release notes from the commits since the last tag,
  with user-facing entries, Fixed versus Changed, Breaking lines,
  a dated section under Unreleased, yanked releases, and compare links.
  Use when asked to update, write, cut, or fix a changelog or release notes.
---

# Update Changelog

Record what changed for users in the project's changelog, from the commits in the release range,
without tagging or publishing unless asked. The rules below are the mistakes agents make with
changelogs.

## Rules

- Write each entry for users, in terms of what they see, not from the commit subject. Drop
  refactors, tests, and CI. Read the commit's diff before writing the line, and take nothing from
  outside the release range.
- Fixed means the old behavior was a bug; an intentional behavior change is Changed, even if calling
  it a fix avoids a bump.
- Mark breaking entries `**Breaking:**` with the replacement, and verify the replacement exists at
  the release (`git grep` at the tag). Do not invent migration paths, dates, or versions.
- New changes go under `## [Unreleased]`, which stays first. At release time rename it to
  `[X.Y.Z] - YYYY-MM-DD`, add a fresh empty Unreleased above it, and fix the comparison links. Do
  not add a release section for work that is not released.
- Never renumber, redate, or delete a published release section; users and registries already have
  that version. Mark a withdrawn release `[YANKED]` and name the replacement.
- The version follows the highest-ranked entry: any Removed or breaking Changed is major, Added or
  Deprecated is minor, Fixed only is patch (in 0.y.z, a break is minor). Take the entries and the
  version from the same diff, and compute it with `$bump-semver`.
- Keep the file's existing format. The audit script checks Keep a Changelog only; on another format,
  follow the file and skip the audit, saying so.
- Do not commit, tag, or publish because a changelog was written.

## Workflow

1. Read the changelog's first sections, the manifest version, and the last final tag
   (`git describe --tags --abbrev=0 --exclude '*-*'`, reachable from HEAD).
1. Read `git log --oneline PREV..HEAD`, merged PR titles, and each commit's diff.
1. Write the entries under Unreleased, or cut the dated section for a release, then run
   `python3 scripts/audit_changelog.py CHANGELOG.md`.
1. Report the range, each entry with its commit, the version and the entry that decided it, and the
   script output.

## Scripts

- `python3 scripts/audit_changelog.py [CHANGELOG.md] [--json]` checks the Keep a Changelog profile
  (dates, categories, Unreleased order, duplicate or empty releases, heading versions), one finding
  per line. Exit 0 clean, 1 findings, 2 usage. Tests: `scripts/test_audit_changelog.py`.
- On Windows, use `py -3` for `python3`.

## References

- Read [`references/changelog.md`](references/changelog.md) when creating or normalizing a
  changelog, cutting a release section, yanking a release, or choosing between Fixed and Changed.
