---
name: maintain-changelog
description: >-
  Write, normalize, audit, or validate changelogs, release notes, and
  Semantic Versioning decisions. Use when CHANGELOG entries, release-history
  structure, or SemVer impact is the requested outcome; not for publishing
  releases, local Git tags, or unrelated documentation.
---

# Maintain Changelog

Apply this workflow when changelog, release-note, or Semantic Versioning work is
requested. Implicit activation selects guidance only; it does not authorize
tagging, publication, or other mutations beyond the user's request.

Derive release facts and public API impact from source, manifests, commits,
issues, and tags. Read
[changelog and SemVer guidance](references/changelog-and-semver.md).

Read the [validator contracts](references/validator-contracts.md) before running
the [changelog validator](scripts/audit_changelog.py) for changed changelogs and
the [SemVer validator](scripts/audit_semver.py) for candidate versions. Direct
inputs must be SemVer without a `v`; `--from-tags` recognizes `v` only as a
Git-tag wrapper. The changelog checker applies a documented Keep a Changelog +
SemVer profile; do not impose it on unrelated release-note formats.

Preserve published version numbers, dates, and useful history. Verify comparison
links, release facts, migration notes, and the declared public API impact.
