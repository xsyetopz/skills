---
name: update-changelogs
description: >-
  Adds and corrects changelog entries from verified changes in a Git range:
  Keep a Changelog sections, user-facing wording, breaking-change notes,
  SemVer bumps. Use when preparing release notes or a CHANGELOG. Not for
  publishing releases.
---

# Update Changelogs

Record what changed for users between two releases, in the project's
changelog format, with every entry traced to a commit and the version
increment justified by the changes.

## Workflow

1. Read the existing changelog, the release policy, and the tags:
   `git tag --sort=-creatordate | head`, the changelog's first sections,
   and any release documentation.
1. Determine the range: previous release tag to the release point
   ([range](references/versions-and-ranges.md#release-range-from-tags)).
1. Draft: `python3 scripts/draft_entries.py PREV..HEAD` when commits follow
   Conventional Commits; otherwise read `git log --oneline PREV..HEAD` and
   merged PR titles.
1. Rewrite each draft line as a user-visible entry under the right change
   type; decide Fixed versus Changed; mark breaking changes with migration
   steps ([format](references/changelog-format.md)).
1. Verify each entry against its commit and the release's code
   ([verification][verification]).
1. Choose the version with the project's policy (SemVer increment rules or
   pre-1.0 policy); for a release, move Unreleased into a dated section and
   update comparison links.
1. Run `python3 -I scripts/audit_changelog.py CHANGELOG.md` and, for new
   tags or headings, `scripts/audit_semver.py`.
1. Report the range, the entries with their commits, the chosen version
   and why, and the audit output.

## Route the task to a card

| Task | Card |
| --- | --- |
| New changelog or normalizing one | [Layout](references/changelog-format.md#file-layout) |
| Collecting changes before a release | [Unreleased](references/changelog-format.md#unreleased-section), [range](references/versions-and-ranges.md#release-range-from-tags), [draft](references/versions-and-ranges.md#drafting-entries-from-conventional-commits) |
| Cutting a release section | [Release heading](references/changelog-format.md#release-heading), [links](references/changelog-format.md#comparison-links) |
| Which heading does an entry go under? | [Change types](references/changelog-format.md#change-types), [Fixed vs Changed](references/changelog-format.md#fixed-versus-changed) |
| Vulnerability fix | [Security entries](references/changelog-format.md#security-entries) |
| Entry reads like a commit message | [User-visible entries](references/changelog-format.md#user-visible-entries) |
| Removing or changing public behavior | [Breaking changes](references/changelog-format.md#breaking-changes-and-migration) |
| A release was withdrawn | [Yanked](references/changelog-format.md#yanked-releases) |
| Choosing the next version | [SemVer increment](references/versions-and-ranges.md#semver-increment), [pre-1.0](references/versions-and-ranges.md#pre-10-versions), [pre-release](references/versions-and-ranges.md#pre-release-and-build-metadata) |
| Checking the file and versions | [Changelog audit](references/versions-and-ranges.md#changelog-audit), [SemVer audit](references/versions-and-ranges.md#semver-syntax-audit) |

## Rules

- Every entry comes from a change in the release range and is checked
  against its commit; nothing from memory or from outside the range.
- Entries describe user-visible behavior; internal refactors, tests, and
  CI changes are omitted unless users notice them.
- Never renumber, redate, or delete a published release; mark withdrawn
  releases `[YANKED]` so users can tell why a version disappeared.
- Do not invent versions, dates, migration paths, or replacement APIs;
  verify them in the release or leave them as open questions.
- Keep the project's format and version scheme (CalVer stays CalVer).
- Security entries follow the disclosure policy; CVE identifiers lead.
- Do not tag or publish unless asked; writing the changelog does not
  authorize either.

## Bundled tools

- `scripts/draft_entries.py RANGE [--version V --date D]`: Conventional
  Commits to a grouped draft with a suggested increment.
- `scripts/audit_changelog.py FILE [--json]`: Keep a Changelog profile
  audit; exit 1 on errors.
- `scripts/audit_semver.py VERSION... | --from-tags | --from-changelog F`:
  SemVer 2.0.0 syntax check.
- `assets/examples/`: a clean changelog, a broken one, and
  `verify.sh`, which drafts from a throwaway Git history and runs every
  audit. `assets/CHANGELOG.template.md` starts a new file.

## References

- [Changelog format](references/changelog-format.md): layout, Unreleased,
  headings, change types, Fixed versus Changed, security, user-visible
  wording, breaking changes, yanked releases, links.
- [Versions, ranges, and validation](references/versions-and-ranges.md):
  release ranges, drafting, entry verification, SemVer increments, pre-1.0
  and pre-release rules, the two audits.

## Completion evidence

The report states the range (`PREV..HEAD` with hashes), each new entry
with its commit or PR, the chosen version with the rule that decided it,
and the audit output; anything not verified (for example a migration path
not found in the code) is listed as open.

[verification]: references/versions-and-ranges.md#verifying-an-entry-against-its-commit
