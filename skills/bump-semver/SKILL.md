---
name: bump-semver
description: >-
  Decides major, minor, or patch from the public API diff, computes and
  compares SemVer versions and tags (rc.10 vs rc.9, 0.y.z, +build), and
  removes deprecated shims due at a major bump. Use when asked for the next
  version, whether a change breaks, or which tag is newest. Not for changelog
  text.
when_to_use: >-
  What should the next version be? Is renaming this keyword argument a
  breaking change? We're at 0.9.3 and changed a signature. Sort these tags by
  precedence. Cut 3.0 and drop the deprecated aliases.
---

# Bump SemVer

Pick the next version from the public API diff and set it where the project keeps it, without
tagging or publishing unless asked. The rules below are the mistakes agents make with versions.

## Rules

- Judge the bump by the public API diff, not commit types or diff size. A `fix:` that changes
  documented behavior is major; removing or renaming a public function, flag, field, or endpoint is
  major even when behavior is unchanged. If no public API is written down, ask which surfaces are
  public.
- The highest-ranked change decides: any removal or incompatible change is major, new compatible
  functionality or a deprecation is minor, compatible fixes only are patch.
- In 0.y.z, bump minor for a breaking change and patch for everything else, because npm `^0.2.3` and
  Cargo `0.2.3` stop at the next minor. Recommend 1.0.0 when users depend on the API; do not bump to
  it unasked.
- Never modify, re-tag, or renumber a published version; registries cache it. Fix forward with a new
  version.
- Compare versions with `python3 scripts/semver.py`, not string sort or `sort -V`: `rc.10` sorts
  below `rc.9` as a string, and `1.0.0` below `1.0.0-rc.1` under `sort -V`.
- Build metadata (`+sha`) never orders or distinguishes releases. Do not use it to publish two
  artifacts of one version; npm, crates.io, and PyPI reject or drop it and OCI tags forbid `+`.
- Keep the project's existing scheme (CalVer, store marketing version plus build number, PEP 440, Go
  `/vN`). Do not validate them with the SemVer regex or convert them unasked; recommend instead.
- A `v` belongs to tags, not versions: manifests hold `1.2.3`. Go module tags require `v`.
- Do not commit, tag, or publish because a version was written.

### Major Bumps and Shims

- A major bump is when deprecated API is removed. List every deprecated alias, forwarding wrapper,
  `@deprecated`, `#[deprecated]`, `[Obsolete]`, or `DeprecationWarning` path, and each version
  branch below a raised minimum. Remove the ones whose deprecation shipped in an earlier release and
  whose policy ends at this major; ask about the rest.
- Never remove a shim in a minor or patch: the removal is the breaking change.
- Do not add an alias or fallback to dodge a major. Either the change breaks (major), or the old
  name keeps working with a deprecation warning (minor).
- Readers for stored data (old config keys, file formats, queue messages) stay while that data
  exists, whatever the API major.
- Trace each removal's consumers (imports, strings, docs, manifests, `exports`) before deleting, and
  name each removal with its replacement in the changelog's Removed section.

## Workflow

1. Read the manifest version, the last final tag (`git describe --tags --abbrev=0 --exclude '*-*'`,
   reachable from HEAD), and any release or deprecation policy.
1. Read the public API diff `PREV..HEAD` and name the change that decides the bump.
1. For a major, list the shims due for removal with the rules above.
1. Compute and check the version: `python3 scripts/semver.py bump PREV minor`, then
   `python3 scripts/semver.py compare PREV NEW`. Set it in every manifest that holds it.
1. Report the range, the deciding change, the version, each shim removed or kept with the reason,
   and the script output.

Leave changelog entries to `$update-changelog` and tags to `$commit-and-rewrite-git`.

## Scripts

- `python3 scripts/semver.py {check,compare,sort,bump} ...` (`--help` lists options).
  `check VERSION... [--from-tags]` validates against the official grammar; `compare A B` prints `<`,
  `=`, or `>`; `sort` orders by precedence;
  `bump VERSION {major,minor,patch,prerelease,release} [--pre-id ID] [--build META]` applies the
  spec resets. Exit 0 ok, 1 invalid version or a bump that does not raise precedence, 2 usage.
  Tests: `scripts/test_semver.py`.
- On Windows, use `py -3` for `python3`.

## References

- Read [`references/versioning.md`](references/versioning.md) when the version is 0.y.z, a
  pre-release, a dependency-only or accidental breaking release, a deprecation, or ships to npm,
  Cargo, Go, PyPI, Maven, Gradle, a container registry, or an app store.
