# Changelog format

Keep a Changelog layout and entries. The valid example,
[`CHANGELOG.example.md`](../assets/examples/CHANGELOG.example.md), audits
clean; `CHANGELOG.broken.txt` next to it produces six audit errors.
Format rules are from [Keep a Changelog 2.0.0][kac].

## Contents

- File layout
- Unreleased section
- Release heading
- Change types
- Fixed versus Changed
- Security entries
- User-visible entries
- Breaking changes and migration
- Yanked releases
- Comparison links

## File layout

**Definition.** A title, a short statement of the format and versioning
scheme, `## [Unreleased]`, then releases newest first, each with `###`
change-type sections, and link definitions at the end.

**Use when.** Creating a changelog or normalizing one on request.

**Do not use when.** The project requires another format (generated
release notes, a docs site). Follow it and do not run the Keep a Changelog
audit on it.

**Example.** See `CHANGELOG.example.md`:

```markdown
## [Unreleased]

## [1.1.0] - 2026-09-20

### Added

- Cancel a running export with `POST /exports/{id}/cancel`; the previous
  export at the destination is kept.
```

**Cost removed.** Readers hunting for where a change is recorded.

**Verify.**

1. `python3 -I scripts/audit_changelog.py CHANGELOG.md` exits 0.

## Unreleased section

**Definition.** `## [Unreleased]` comes first and collects changes merged
since the last release. It may be empty right after a release.

**Use when.** Recording changes before a version is decided.

**Do not use when.** Never present unreleased changes as shipped.

**Example.** At release time, rename `[Unreleased]` to `[1.2.0] -
YYYY-MM-DD`, add a new empty `## [Unreleased]` above it, and update the
links.

**Cost removed.** Reconstructing a release from history at the last
minute.

**Verify.**

1. The audit reports `unreleased-order` if Unreleased is not first.

## Release heading

**Definition.** `## [X.Y.Z] - YYYY-MM-DD`, newest first, with the version
as a link reference to its comparison or tag.

**Use when.** Cutting a release.

**Do not use when.** The date or version would be a guess. Use the actual
publication date and the version the release policy chose.

**Example.** `## [1.1.0] - 2026-09-20`

**Cost removed.** Ambiguous dates (`9/10/2026`) and unordered history.

**Verify.**

1. The audit reports `date-format` for non-ISO dates and
   `duplicate-version` for repeated versions.

## Change types

**Definition.** Six headings: Added (new features), Changed (changes in
existing functionality), Deprecated (soon-to-be removed features), Removed
(now removed features), Fixed (bug fixes), Security (vulnerabilities).
Omit empty ones ([Keep a Changelog][kac]).

**Use when.** Grouping every entry.

**Do not use when.** Never invent headings such as "Improvements" or
"Misc"; the audit rejects them.

**Example.** `### Added`, `### Fixed`

**Cost removed.** Readers scanning several invented headings for one kind
of change.

**Verify.**

1. The audit reports `invalid-category` and `empty-category`.

## Fixed versus Changed

**Definition.** Fixed: the old behavior was wrong and is now correct.
Changed: the old behavior was intended and now works differently. When
unsure, ask whether the old behavior was a bug ([Keep a
Changelog][kac]).

**Use when.** A change alters behavior users relied on.

**Do not use when.** Never label an intentional behavior change a fix to
avoid a version bump.

**Example.** "Exports no longer leave `.tmp` files behind when validation
fails" is Fixed; "Exports now default to UTF-8 instead of the system
encoding" is Changed.

**Cost removed.** Users missing a behavior change hidden under Fixed.

**Verify.**

1. For each Fixed entry, point to the bug report or failing behavior it
   corrects.

## Security entries

**Definition.** Security lists vulnerability fixes. When a CVE exists,
the entry starts with the identifier ([Keep a Changelog][kac]).

**Use when.** A release fixes a vulnerability that is disclosed or ready
to disclose under the project's policy.

**Do not use when.** The vulnerability is under embargo; follow the
disclosure policy and do not publish exploit detail.

**Example.** `- CVE-2026-00001: path traversal in export destinations.`

**Cost removed.** Security tools and readers that cannot match the fix to
the advisory.

**Verify.**

1. `rg -n '^- CVE-' CHANGELOG.md` finds each CVE at the start of its
   entry.

## User-visible entries

**Definition.** Each entry states what changed for the software's users
(behavior, API, CLI, configuration), not the internal work.

**Use when.** Writing every entry.

**Do not use when.** Never copy commit subjects verbatim; the draft
script's output is raw material.

**Example.** "Preserve empty search filters when reopening saved searches"
instead of "Refactor filter deserialization".

**Cost removed.** Changelogs that cannot inform an upgrade decision.

**Verify.**

1. Each entry names a user-facing object (endpoint, command, option,
   screen, file) or states why it has none.

## Breaking changes and migration

**Definition.** An incompatible change is marked breaking and says what
users must do (the replacement API, the new flag, the data migration).
The release's code or docs confirm it.

**Use when.** Removing or changing public behavior.

**Do not use when.** Never invent a migration path; if none exists, say
so.

**Example.**

```markdown
### Removed

- **Breaking:** `GET /v1/exports` is removed. Use `GET /v2/exports`,
  which returns the same fields plus `status`.
```

**Cost removed.** Upgrades that fail without explanation.

**Verify.**

1. The replacement named in the entry exists in the release
   (`git grep` at the release tag).

## Yanked releases

**Definition.** A withdrawn release keeps its section, with `[YANKED]`
after the date and a space between them. Never delete or renumber it.

**Use when.** A published release is withdrawn (broken build, incomplete
security fix).

**Do not use when.** The release was never published, so it was never a
release.

**Example.** `## [1.0.1] - 2026-08-02 [YANKED]`

**Cost removed.** Users who cannot tell why a version disappeared.

**Verify.**

1. The audit accepts the heading; the entry explains the replacement
   version.

## Comparison links

**Definition.** Link definitions at the end map each version heading to a
comparison between tags (`v1.0.1...v1.1.0`), and Unreleased to
`v<latest>...HEAD`.

**Use when.** The project's host has a comparison URL scheme.

**Do not use when.** Links would point to tags that do not exist.

**Example.**

```markdown
[Unreleased]: https://example.invalid/compare/v1.1.0...HEAD
[1.1.0]: https://example.invalid/compare/v1.0.1...v1.1.0
```

**Cost removed.** Readers reconstructing the range by hand.

**Verify.**

1. Each tag in the links exists: `git tag -l 'v1.1.0' 'v1.0.1'`.

[kac]: https://keepachangelog.com/en/2.0.0/
