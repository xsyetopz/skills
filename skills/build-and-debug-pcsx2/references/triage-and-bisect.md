# Triage the failing layer and bisect regressions

Cards for classifying a failure by layer before changing anything, and
for bisecting a regression over release builds or source commits.

## Contents

- Build failure versus guest behaviour
- Bisecting over release builds
- Bisecting source commits with git bisect

## Build failure versus guest behaviour

**Definition.** Every symptom belongs to the first layer whose evidence
fails:

1. Configure: a CMake error.
1. Compile or link: a `FAILED:` line from ninja.
1. Package: a missing `.app` or resources.
1. Process start: an exit before `DataRoot Directory`.
1. Setup: the wizard, or a missing BIOS (`Startup Error`).
1. Guest boot.
1. Guest behaviour.
1. Renderer output.
1. Host crash.

Evidence from one layer proves nothing about a later one.

**Use when.**

- Before any fix, and when writing the final report.

**Do not use when.**

- Nothing has failed yet, for example while writing a new patch: go
  straight to the construct's card.

**Example.** Layers observed in this session, with their evidence:

| Layer | Command | Evidence | Result |
| --- | --- | --- | --- |
| deps | macOS script, default SDK | `tapi error … arm64e.x1-macos` | host SDK |
| deps | macOS script, SDK 26.5 | `nasm not found or too old` | missing tool |
| deps | `BUILD_FFMPEG=0` | KDDockWidgets `symbol(s) not found … x86_64` | Homebrew arm64 spdlog |
| configure | `cmake … x86_64` | `Configuring done (7.4s)` | pass |
| compile | `ninja -k 0` | 24 × `missing Metal Toolchain` | host tool |
| tests | `ninja unittests` | `100% tests passed out of 2` | pass |
| setup | `-batch -nogui` fresh root | killed at 40 s, no boot lines | wizard |
| setup | wizard off, no BIOS | exit 0, `Startup Error: … BIOS` | no BIOS |

```sh
grep -m1 -E 'CMake Error|FAILED:|Startup Error|Error Parsing' \
  cfg.log build.log emu.log
```

**Cost removed.** Code changes aimed at the wrong layer. Count: report
claims without a named layer and matching evidence line (target 0).

**Verify.**

1. Each claim in the report names its layer and quotes the line that
   proves it.
1. No claim about a later layer rests on evidence from an earlier one:
   neither a green build nor exit 0 is a boot.

## Bisecting over release builds

**Definition.** Binary search over published builds, testing the midpoint
between known-good and known-bad each step. PCSX2 publishes a pre-release
per nightly tag, for example `v2.9.84` with
`pcsx2-v2.9.84-macos-Qt.tar.xz`. The [reporting guide][identify]
describes this method.

**Use when.**

- The regression lies between two releases and building from source is
  blocked or slow (here, Metal blocked it).

**Do not use when.**

- Adjacent tags span several commits and you need the exact one: continue
  with git bisect.

**Example.** List candidate tags, then run each with its own portable
root and the same oracle:

```sh
gh api 'repos/PCSX2/pcsx2/releases?per_page=100' \
  --jq '.[].tag_name' > tags.txt
T=v2.9.84
gh release download "$T" -R PCSX2/pcsx2 -p '*macos-Qt.tar.xz' -D "b/$T"
tar -xf "b/$T"/*.tar.xz -C "b/$T"
printf 'data\n' > "b/$T/portable.txt"
```

Record `tag good|bad` per step. Reusing a save state across steps is safe
only when no `[SAVEVERSION+]` commit lies between them; see
[save-state version caveats][states].

**Cost removed.** Testing every build: `ceil(log2(N))` runs instead of N.
Count: the number of steps recorded.

**Verify.**

1. The final pair is adjacent in `tags.txt`, and both results reproduce
   on a second run.
1. Every step used a fresh portable root, and the oracle quotes a log line
   or an artifact, not an exit status.

## Bisecting source commits with git bisect

**Definition.** `git bisect start BAD GOOD`, then `git bisect run
SCRIPT`. The script builds and tests each commit and exits 0 for good,
1 to 124 for bad, and 125 to skip.

**Use when.**

- Adjacent release tags still span several commits.
- The oracle runs without a GUI, for example `ninja unittests`,
  `core_test --gtest_filter=…`, or a GS runner comparison.

**Do not use when.**

- The oracle needs a booted game and a person watching: test by hand with
  `git bisect good` or `git bisect bad`.
- Some commits in the range do not build: exit 125 for those, or the
  bisect blames a build break.

**Example.** Not run here: bisecting needs a full clone, and the clone
here is shallow.

```sh
git bisect start v2.9.84 v2.8.2
git bisect run sh -c '
  cmake --build build --target unittests >/dev/null 2>&1 || exit 125
  build/tests/ctest/core/core_test --gtest_filter="Patch.*"'
git bisect log > bisect.log
```

**Cost removed.** Rebuilding every commit: with ccache, unchanged
translation units compile once. Count: steps in `bisect.log`.

**Verify.**

1. `git bisect log` ends with `first bad commit`, and the oracle fails on
   that commit and passes on its parent when both are re-run by hand.
1. List the `skip` lines: no step was skipped for a reason that could hide
   the regression.

[identify]: https://pcsx2.net/docs/troubleshooting/identify/
[states]: patches-textures-states.md#save-state-version-caveats
