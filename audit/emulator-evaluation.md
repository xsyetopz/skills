# Emulator skills evaluation

Evaluated 2026-09-12. Replaced the two original emulator umbrellas and ten
intermediate micro-skills with four explicit-only packages:
`operate-duckstation`, `operate-pcsx2`, and a source-compilation skill for each
emulator. Launch, debugging, captures, patches and textures share isolated
fixture ownership and guest-checkpoint evidence. Compilation has distinct
toolchain inputs and artifact validation. Runtime packages each have three
references; build packages have one.

## Source-backed corrections

Rechecked DuckStation commit `cbe7951be624a3fd69c81858647a8f84e4a1d06b` and
PCSX2 v2.8.2 parsers. Source links are preserved in the references.

- DuckStation's standalone `-exe` override does not retain autoboot. Fixed the
  helper's `--psx-exe` to emit a positional executable, matching its stated
  goal.
- PCSX2's state filename alone does not retain autoboot. The helper now permits
  state-file-plus-image and rejects state-only and empty batch requests.
- PCSX2 turbo and unlimited are distinct limiter modes; unlimited takes
  precedence when both are supplied. Corrected the inherited false equivalence
  against QtHost, VMManager and installed help output.
- DuckStation GDB binds IPv4 loopback. Settings and PCDrv sources confirm the
  configuration keys, read-only default and explicit lack of a security sandbox.
- Rechecked official texture, debugger and PNACH documentation; guest addresses,
  byte widths, patch timing and identity remain separate contracts.

Build references were checked against pinned README/CMake/dependency scripts.
DuckStation's selected revision requires Visual Studio 2026 on Windows; PCSX2's
selected release warns that native ARM64 recompilers are incomplete. Commands
remain platform-specific integration procedures. No full emulator source build
was executed, and no build success is inferred from source review.

## Installed runtime interfaces

PCSX2 `/Applications/PCSX2.app/Contents/MacOS/PCSX2` reported v2.8.2. SHA256:
`10e7cc1b3180b5a9f48923f3dfc3900019cc8c0df7e280a0ea61190b86961390`. Help and
version returned status 1 with expected output, matching early exit before
configuration initialization. An isolated `-datapath DIR -testconfig` returned 0
and generated `DIR/PCSX2/inis/PCSX2.ini` and logs. Guidance now requires
verifying the resolved layout instead of assuming `DIR/inis`. No BIOS, save,
commercial media or guest execution was involved.

Installed DuckStation executable SHA256:
`14c22c6e1f4bbff13c00c24f17424ef8cf7645ee9917f7d65b17cd3fe1dd1645`. Both help
and version terminated with signal 9 and empty output. Cause remains
undiagnosed; no signing/quarantine bypass was attempted. No working DuckStation
launch, renderer, GDB attachment or guest checkpoint is claimed. Interface
outputs are in `/tmp/emulator-interface-evidence`.

## Upstream GS regression scripts

Executed unchanged v2.8.2 scripts with an explicit stub runner returning 7 and a
placeholder dump filename, not an actual GS replay. The wrapper returned 0.
Repeating the invocation skipped the existing output directory; the child ran
only once. Documentation requires checking actual child completion and using
fresh output directories.

The comparison script was exercised with arbitrary bytes in frame-named files:
empty baseline/test and extra test-only frames returned 0; missing required
frames and differing bytes returned 1. Successful comparisons deleted their HTML
report; failed comparisons retained it. Source inspection confirms whole-file
hashing, not decoded-pixel comparison, and absolute local image/CSS/JS URLs.
Guidance now requires nonempty expected frame sets, distinguishes bytes from
pixels, and warns that reports are not standalone portable artifacts. This
validates harness behavior only, not graphics correctness.

## Independent evaluation and validation

A fresh evaluator used only helpers/references to generate quoted standalone
PS-X and PCSX2 state-plus-ISO commands, reject missing-game state-only input,
and reject a false GS regression pass with failed runner/no frames. Integration
inspected the commands. Minor evaluator prose incorrectly described a full
slash-prefixed path as dash-prefixed; only its basename began with a dash. The
generated argument boundaries were correct. Report:
`/tmp/emulator-commands-forward-result.md`.

DuckStation's seven and PCSX2's eight helper tests pass. Ruff lint/format,
official skills-ref, skill-creator validation, strict Markdown and local links
pass for the four packages. These tests prove command construction, not the
emulators' entire grammar or guest outcomes. Source builds, real GS replay,
patch execution, texture substitution and guest debugging remain unexecuted
validation surfaces; no synthetic result substitutes for those checks.
