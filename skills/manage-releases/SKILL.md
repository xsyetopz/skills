---
name: manage-releases
description: >-
  Chooses semantic version bumps and writes changelog entries from commits and
  API changes. Use when preparing a release, a version number, or a CHANGELOG.
---

# Manage Releases

Pick the next version from the public API diff and record the release in
the project's changelog, without tagging or publishing unless asked.

## Rules

- Judge the bump by the public API diff, not commit types or diff size.
  A `fix:` that changes documented behavior is major; removing or
  renaming a public function, flag, field, or endpoint is major even when
  behavior is unchanged. If no public API is written down, ask which
  surfaces are public.
- In 0.y.z, bump minor for a breaking change and patch for everything
  else, because npm `^0.2.3` and Cargo `0.2.3` stop at the next minor.
- Never modify, re-tag, renumber, or redate a published version or its
  changelog section; registries cache it. Fix forward with a new
  version, and mark a withdrawn release `[YANKED]` in the changelog.
- Compare versions with `python3 scripts/semver.py`, not string sort or
  `sort -V`: `rc.10` sorts below `rc.9` as a string, and `1.0.0` below
  `1.0.0-rc.1` under `sort -V`.
- Build metadata (`+sha`) never orders or distinguishes releases. Do
  not use it to publish two artifacts of one version; npm, crates.io,
  and PyPI reject or drop it and OCI tags forbid `+`.
- Keep the project's existing scheme (CalVer, store marketing version
  plus build number, PEP 440, Go `/vN`). Do not validate them with the
  SemVer regex or convert them unasked; recommend instead.
- A `v` belongs to tags, not versions: manifests hold `1.2.3`. Go
  module tags require `v`.
- Write each changelog entry for users, in terms of what they see, not
  from the commit subject. Drop refactors, tests, and CI. Read the
  commit's diff before writing the line, and take nothing from outside
  the release range.
- Fixed means the old behavior was a bug; an intentional behavior
  change is Changed, even if calling it a fix avoids a bump.
- Mark breaking entries `**Breaking:**` with the replacement, and verify
  the replacement exists at the release (`git grep` at the tag). Do not
  invent migration paths, dates, or versions.
- New changes go under `## [Unreleased]`, which stays first. At release
  time rename it to `[X.Y.Z] - YYYY-MM-DD`, add a fresh empty
  Unreleased above it, and fix the comparison links. Do not add a
  release section for work that is not released.
- The bump follows the highest-ranked entry: any Removed or breaking
  Changed is major, Added or Deprecated is minor, Fixed only is patch.
  Feed the changelog entries and the version from the same diff.
- Do not commit, tag, or publish because a changelog or version was
  written.

## Workflow

1. Read the manifest version, the last final tag
   (`git describe --tags --abbrev=0 --exclude '*-*'`, reachable from
   HEAD), the changelog's first section, and any release policy.
1. Take the range `PREV..HEAD` from the last release tag and read the
   public API diff plus `git log --oneline PREV..HEAD`.
1. Choose the bump with the rules above, compute it, and check it:
   `python3 scripts/semver.py bump PREV minor` then
   `python3 scripts/semver.py compare PREV NEW`.
1. Write the entries under Unreleased, or the dated section for a
   release, then run `python3 scripts/audit_changelog.py CHANGELOG.md`.
1. Report the range, each entry with its commit, the version and the
   change that decided it, and the script output.

## Scripts

- `python3 scripts/semver.py {check,compare,sort,bump} ...` (`--help`
  lists options). `check VERSION... [--from-tags]` validates against the
  official grammar; `compare A B` prints `<`, `=`, or `>`; `sort` orders
  by precedence; `bump VERSION {major,minor,patch,prerelease,release}
  [--pre-id ID] [--build META]` applies the spec resets. Exit 0 ok, 1
  invalid version or a bump that does not raise precedence, 2 usage.
  Tests: `scripts/test_semver.py`.
- `python3 scripts/audit_changelog.py [CHANGELOG.md] [--json]` checks
  the Keep a Changelog profile (dates, categories, Unreleased order,
  duplicate or empty releases, heading versions), one finding per line.
  Exit 0 clean, 1 findings, 2 usage. Tests:
  `scripts/test_audit_changelog.py`.
- On Windows, use `py -3` for `python3`.

## References

- Read [`references/versioning.md`](references/versioning.md) when the
  version is 0.y.z, a pre-release, a dependency-only or accidental
  breaking release, a deprecation, or ships to npm, Cargo, Go, PyPI,
  Maven, Gradle, a container registry, or an app store.
- Read [`references/changelog.md`](references/changelog.md) when
  creating or normalizing a changelog, cutting a release section,
  yanking a release, or choosing between Fixed and Changed.
