# Licence, official releases, and release-level regressions

Cards for choosing which DuckStation binary to run and what an agent must
not do with the DuckStation source. Observations below come from release
`v0.1-11826` (version string `0.1-11826-gfe2306b1f`) on macOS 27 arm64.

## Contents

- Licence and AI-assistant policy
- Pinned official release
- Regression comparison across official releases

## Licence and AI-assistant policy

**Definition.** DuckStation is licensed CC-BY-NC-ND-4.0. Its build-system
files add a packaging restriction. At commit `0d8dda34` the header of
[`CMakeLists.txt`][cmakelists] reads "CC-BY-NC-ND-4.0 + Packaging
Restriction" and says "you may not use this file to create packages or
build recipes without explicit permission from the copyright holder";
other build-system files carry the same terms. The repository root has a
[`CLAUDE.md`][claude-md] that tells AI coding assistants not to read,
search, edit, build, or run anything in the repository. The
[README][readme] permits redistribution of "unmodified releases and code"
and says "pre-configured settings and packages are considered
modifications".

**Use when.**

- A task mentions a DuckStation checkout, CMake, dependencies, compiling,
  a patch to emulator source, or packaging (Homebrew formula, Flatpak,
  AUR, a zipped app with settings).
- Before opening any file in a directory that contains the DuckStation
  `CLAUDE.md` described above.

**Do not use when.**

- The task only runs an official release binary as an end user, edits
  its user directory, or reads the README, wiki, or release notes. The
  rest of this skill covers those.

**Example.** The rule an agent follows, and the response it gives:

```text
Rule
- Do not write, suggest, or run build recipes for DuckStation (clone +
  cmake, dependency scripts, CI build files, package recipes).
- Do not read, modify, or build files in a DuckStation source checkout.
- Do not redistribute a release with bundled settings, BIOS, or games.
- Run official release binaries; point users to the project's own
  README "Building" section and releases page.

Response to "build DuckStation from source for me"
  DuckStation's licence (CC-BY-NC-ND-4.0 plus a packaging restriction on
  its build files) and its repository CLAUDE.md ask AI assistants not
  to build or modify it. I can run and debug an official release
  instead: https://github.com/stenzek/duckstation/releases
  Build instructions: README.md, section "Building", in the upstream
  repository.
```

**Cost removed.** Licence violations and rework on a path that ends in a
refusal. Observable count: build commands (`cmake`, `ninja`,
`git clone .../duckstation`) in the agent transcript; the target is 0.

**Verify.**

1. `grep -nE 'cmake|ninja|git clone' <transcript-or-diff>` returns no
   line that targets DuckStation.
1. The deliverable names an official release tag or asset URL as the
   binary under test.

## Pinned official release

**Definition.** A GitHub release of `stenzek/duckstation` with prebuilt
assets: Windows zip/installer
(x64, x64-SSE2, arm64), Linux AppImages (x64, x64-SSE2, arm64, armhf), and
one universal macOS zip. Rolling tags `latest` and `preview` move;
numbered tags such as `v0.1-11826` do not. The [README][readme] says the
releases page keeps the last 30 releases and older ones are at
[duckstation/old-releases][old-releases]. GitHub reports a SHA-256 digest
for every asset.

**Use when.**

- Any run, bug report, or comparison: record the numbered tag, asset
  name, digest, and the version string the binary prints.

**Do not use when.**

- You would identify the build under test by `latest` or `preview`: the
  tag moves, so a later reader cannot get the same binary.
- The host is below the README minimums (macOS 13.3; Windows 10 1809; a
  distribution equivalent to Ubuntu 22.04 for AppImages): the binary does
  not start, and that is not a DuckStation regression.

**Example.**

```sh
TAG=v0.1-11826
gh release view "$TAG" -R stenzek/duckstation \
  --json assets --jq '.assets[] | "\(.name) \(.digest)"'
gh release download "$TAG" -R stenzek/duckstation \
  -p duckstation-mac-release.zip -D ./ds-"$TAG"
shasum -a 256 ./ds-"$TAG"/duckstation-mac-release.zip
ditto -x -k ./ds-"$TAG"/duckstation-mac-release.zip ./ds-"$TAG"/app
./ds-"$TAG"/app/DuckStation.app/Contents/MacOS/DuckStation -version
```

Observed for `v0.1-11826`: digest
`1870ef7c34f619861cf9bedfe73772cb2106061058ce6e40a7b41dc328835a96`,
a universal (x86_64 + arm64) Mach-O with an ad-hoc signature, and
`-version` printing `DuckStation Version 0.1-11826-gfe2306b1f (dev)` to
stderr with exit status 1. Runnable: `assets/examples/verify.sh release`.

**Cost removed.** Unreproducible reports ("latest" changes under the
reader). Observable: the report contains a numbered tag and a digest that
`shasum -a 256` reproduces.

**Verify.**

1. `shasum -a 256` of the downloaded asset equals the GitHub `digest`.
1. `DuckStation -version 2>&1` prints the tag's number (`0.1-11826`).

## Regression comparison across official releases

**Definition.** Find the first official release that shows a behavior by
running the same input and settings on numbered release binaries, halving
the tag range each time. Each GitHub release's notes list the commits it
adds, which narrows a regression to a commit range without building
anything.

**Use when.**

- A behavior works in one official release and fails in a later one.
- You need a commit range to cite in an upstream issue.

**Do not use when.**

- The comparison needs a build of an intermediate commit: that is a
  build recipe (see the licence card). Report the release range.
- Inputs differ between runs (BIOS, disc image revision, per-game
  settings, save state): the range then measures the input change.
- You would start each run from one save state across releases; see
  [save states](guest-vs-emulator.md#save-states-are-not-a-regression-oracle).

**Example.**

```sh
gh release list -R stenzek/duckstation -L 40 \
  --json tagName,publishedAt --jq '.[] | "\(.tagName) \(.publishedAt)"'
# Pick GOOD and BAD numbered tags, then test the midpoint tag in its own
# portable copy with the same copied settings.ini and input.
gh release view v0.1-11752 -R stenzek/duckstation --json body \
  --jq .body | grep -i 'GDBServer'
```

Observed: the last command listed 25 `GDBServer:` commits added in
`v0.1-11752` (for example "Expand watchpoint ranges", "Expose GTE
registers").

**Cost removed.** Builds: zero compilations. Runs: about log2(number of
releases in range). Observable: the report names the last good tag, the
first bad tag, and the commits between them.

**Verify.**

1. Each tested binary's `-version` output is recorded next to its result.
1. Re-run the first-bad and last-good tags with fresh portable copies; both
   results repeat.
1. Tier here: download, digest, and `-help` of one tag were Executed;
   guest comparisons are Not runnable here (no BIOS may be used).

[cmakelists]:
https://github.com/stenzek/duckstation/blob/0d8dda34d3785d8a5c9e910b9ef50caa85fcde0c/CMakeLists.txt
[claude-md]:
https://github.com/stenzek/duckstation/blob/0d8dda34d3785d8a5c9e910b9ef50caa85fcde0c/CLAUDE.md
[readme]: https://github.com/stenzek/duckstation/blob/master/README.md
[old-releases]: https://github.com/duckstation/old-releases/releases
