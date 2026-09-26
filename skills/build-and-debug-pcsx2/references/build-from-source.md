# Build PCSX2 from source

Cards for the upstream policy, a pinned checkout, dependency bootstrap per
platform, CMake configuration, ccache, and the GS runner target. Source
facts come from PCSX2 commit `2c804670` (tag `v2.9.84`, 2026-09-25) and the
pcsx2.net documentation repository at `3e9fea9e`; see
[sources](sources.md). Local runs used a shared 10-core arm64 Mac, macOS 27,
CMake 4.4.3, Ninja, Xcode 26.6 without the Metal Toolchain, no `nasm`, no
`ccache`, and no Homebrew Qt.

## Contents

- Licence and AI-assistant policy
- Pinned source checkout
- Linux dependency script
- macOS dependency script
- Windows dependency pack
- CMake configure and build types
- ccache compiler launcher
- Unit tests target
- GS runner target

## Licence and AI-assistant policy

**Definition.** PCSX2 is licensed GPL-3.0-or-later (`COPYING.GPLv3`;
source files carry `SPDX-License-Identifier: GPL-3.0+`). The repository's
[`AGENTS.md`][agents] (also loaded by `CLAUDE.md` and `GEMINI.md`) places no
limit on building, packaging, or running. It restricts contributions:

- Contributors must declare LLM use.
- New contributors must not use LLMs for any content in a contribution.
- Long-time contributors may use LLMs for completion, boilerplate, or
  partial generation, never for full code generation.
- Agents must not open or update PRs, issues, discussions, or comments
  through GitHub, its API, the CLI, or web automation.
- AI-written PR descriptions, commit messages, review replies, and issue
  text must not be published.
- Before code changes, the agent verifies that the human understands the
  problem. It guides rather than hands over a solution, and confirms that
  the human can explain the change.

**Use when.**

- The task edits PCSX2 source, drafts a patch for upstream, or mentions a
  PR, issue, or commit message for `PCSX2/pcsx2`.

**Do not use when.**

- The task only builds, runs, logs, or debugs PCSX2 locally, or writes
  `.pnach` files for personal use. The policy does not restrict these.
  Applying it there refuses legitimate work.

**Example.** A user asks: "fix the crash in GSTextureCache and open a PR".

```text
Upstream AGENTS.md forbids agents from opening PRs or posting to GitHub,
and new contributors may not submit LLM-generated code. Are you a new or
long-time PCSX2 contributor? I can point you to GSTextureCache.cpp, the
crash backtrace, and the relevant test, then review your own fix. You
open the PR and write its description yourself.
```

**Cost removed.** Contributions that upstream refuses and that can lead to
a participation ban. Count: `gh` commands that write to
`PCSX2/pcsx2` in the session transcript (target 0).

**Verify.**

1. `curl -sL https://raw.githubusercontent.com/PCSX2/pcsx2/master/AGENTS.md
   | grep -n 'must not'` shows the current rules. Re-read them when the
   pinned commit changes.
1. `grep -c 'gh pr create\|gh issue create' transcript.txt` prints `0`.

## Pinned source checkout

**Definition.** A shallow checkout of one exact commit, so build files,
dependency scripts, and docs all match the binary under test.
At `2c804670`, `.gitmodules` is empty and no gitlinks exist
(`git ls-files -s | awk '$1==160000'` prints nothing). All third-party code
is vendored in `3rdparty/`.

**Use when.**

- Building, bisecting, or reading source to explain the behaviour of a
  specific release or nightly build (`v2.8.2`, `v2.9.84`).

**Do not use when.**

- Only running an official release. Use the release asset and its sha256
  digest; a checkout adds 150 MB for nothing.

**Example.** Executed here.

```sh
git init -q pcsx2 && cd pcsx2
git remote add origin https://github.com/PCSX2/pcsx2.git
git fetch -q --depth 1 origin 2c804670c5f2c99d6a6b842904dd222de89aa493
git checkout -q FETCH_HEAD
git log -1 --format='%H %s'
```

For a tag, fetch `refs/tags/v2.8.2` instead of the SHA. A guard in the
top-level `CMakeLists.txt` refuses in-source builds.

**Cost removed.** Commands from one revision applied to another: for
example, `-gamecfg` exists at `v2.9.84` but not in `v2.8.2`'s `QtHost.cpp`.
Observable: `git rev-parse HEAD` equals the pinned SHA.

**Verify.**

1. `git rev-parse HEAD` prints the pinned SHA.
1. `git status --porcelain` is empty before configuring.

## Linux dependency script

**Definition.** `.github/workflows/scripts/linux/build-dependencies-qt.sh
DIR` downloads pinned, checksummed sources and builds PCSX2's third-party
libraries into `DIR`. The official build guide and the Linux CI both use
it. It needs the distribution packages listed in the
[build guide][building], for example `clang lld llvm cmake ninja-build
extra-cmake-modules libasound2-dev libpulse-dev libwayland-dev` on Ubuntu.
GCC is unsupported; CMake prints `UNSUPPORTED CONFIGURATION` for it.

**Use when.**

- Building on Linux x86-64 and matching CI's library versions.

**Do not use when.**

- An Arch or Nix environment already provides Qt 6, SDL3, shaderc and the
  other libraries. The guide lists package sets for those.

**Example.** Not runnable here (macOS host). Upstream command:

```sh
.github/workflows/scripts/linux/build-dependencies-qt.sh deps
cmake -B build -G Ninja -DCMAKE_C_COMPILER=clang \
  -DCMAKE_CXX_COMPILER=clang++ \
  -DCMAKE_EXE_LINKER_FLAGS_INIT=-fuse-ld=lld \
  -DCMAKE_MODULE_LINKER_FLAGS_INIT=-fuse-ld=lld \
  -DCMAKE_SHARED_LINKER_FLAGS_INIT=-fuse-ld=lld \
  -DCMAKE_PREFIX_PATH="$PWD/deps"
ninja -C build && build/bin/pcsx2-qt -version
```

The guide prints `-DCMAKE_MODULE_LINKER_FLAGS_INIT="-fuse-ld"` with no
value, while `AGENTS.md` and `CMakePresets.json` use `-fuse-ld=lld`. Use
the latter.

**Cost removed.** Version drift between distribution libraries and CI.
Observable: `grep -E '^(QT|SDL)=' build-dependencies-qt.sh` shows the
same versions that `cmake` reports finding.

**Verify.**

1. `build/bin/pcsx2-qt -version` prints `PCSX2 v…`. It exits 1 by design.
1. `ldd build/bin/pcsx2-qt | grep deps/lib` shows the libraries resolved
   from the prefix.

## macOS dependency script

**Definition.** `.github/workflows/scripts/macos/build-dependencies.sh
DIR` builds the dependencies for x86-64: SDL3, FFmpeg, zstd, LZ4, libpng,
libjpeg-turbo, WebP, FreeType, HarfBuzz, MoltenVK, Qt 6.11.2, shaderc,
KDDockWidgets, PlutoVG, PlutoSVG and RapidYAML. It sets
`CMAKE_OSX_ARCHITECTURES=x86_64`, so on Apple Silicon the result runs under
Rosetta. The [guide][building] calls ARM builds unsupported, and at
`2c804670` CMake still warns of "no EE/VU/IOP recompilers" for arm64.
`BUILD_FFMPEG=0` skips FFmpeg. The script needs Xcode, and CI also installs
`nasm` and `ccache` with Homebrew.

**Use when.**

- Building on macOS, Intel or Apple Silicon.

**Do not use when.**

- You want arm64 libraries from Homebrew. The guide says "Dependencies
  from Homebrew will not work", and the run below shows why.

**Example.** Executed here with `SDKROOT` set to `MacOSX26.5.sdk`. The
default SDK linker fails with
`tapi error ... unknown architecture arm64e.x1-macos`, a problem specific
to this machine.

```sh
SDKROOT=/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk \
  .github/workflows/scripts/macos/build-dependencies.sh "$PWD/deps"
```

Observed stages, in order:

1. With the default SDK, CMake's compiler check failed on the `tapi`
   error after 28 s.
1. With `SDKROOT` set, SDL3 built, then FFmpeg stopped at
   `nasm not found or too old`.
1. With `BUILD_FFMPEG=0`, everything through Qt built in 16 min 55 s wall
   time. KDDockWidgets then failed to link:
   `"spdlog::logger::err_handler_..." ... symbol(s) not found for
   architecture x86_64`. It had found the arm64 `spdlog` in
   `/opt/homebrew`.
1. A local copy of the script added `-DCMAKE_IGNORE_PREFIX_PATH=/opt/homebrew`
   and FFmpeg `--disable-x86asm` (both not upstream). The remaining
   libraries then built in 2 min 31 s; the prefix is 142 MB.

**Cost removed.** Mixed-architecture link failures. Observable:
`file deps/lib/libSDL3.dylib` reports `x86_64`, and no library in the
prefix reports `arm64`.

**Verify.**

1. `for f in deps/lib/*.dylib; do lipo -archs "$f"; done | sort -u`
   prints only `x86_64`.
1. `cmake ... -DCMAKE_OSX_ARCHITECTURES=x86_64` prints `Building for
   x86-64.` and `Configuring done`.

## Windows dependency pack

**Definition.** Prebuilt dependencies from
[`pcsx2-windows-dependencies` releases][windeps], extracted to `deps\` in
the repository root; then open `PCSX2_qt.slnx` (`.slnx` replaced `.sln`). This
needs Visual Studio 2022 17.10 or later with
"Desktop development with C++". In 17.10 to 17.12, enable **Tools >
Options > Environment > Preview Features > Use Solution File Persistence
Model**. CI can also build the dependencies with
`.github/workflows/scripts/windows/build-dependencies.bat`.

**Use when.**

- Building on Windows x64 with Visual Studio.

**Do not use when.**

- Visual Studio is older than 17.10, which cannot open `.slnx`.

**Example.** Not runnable here (no Windows host). The CI's CMake variant:

```bat
cmake . -B build "-DCMAKE_PREFIX_PATH=%cd%\deps" -DQT_BUILD=ON ^
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_INTERPROCEDURAL_OPTIMIZATION=ON ^
  -DDISABLE_ADVANCE_SIMD=ON -G Ninja
cmake --build build --config Release
cmake --build build --config Release --target unittests
```

**Cost removed.** Building Qt locally, which took 17 min on the Mac above.
Observable: the build starts without compiling any dependency.

**Verify.**

1. `bin\pcsx2-qtx64-avx2.exe -version` (the name the guide uses) prints
   the version.
1. The `unittests` target reports `100% tests passed`.

## CMake configure and build types

**Definition.** `CMAKE_BUILD_TYPE` selects the build type. When it is
unset, `cmake/BuildParameters.cmake` picks `Devel`, which reuses the
`RelWithDebInfo` flags. Per the guide, `Release` is fastest with no crash
information, `Devel` adds trace logging, and `Debug` has no optimization.
`CMakePresets.json` defines `clang-debug`, `clang-devel`, and
`clang-release`; the last adds `CMAKE_INTERPROCEDURAL_OPTIMIZATION=ON`.
Other options: `ENABLE_TESTS` (ON), `ENABLE_QT_UI` (ON), `ENABLE_GSRUNNER`
(OFF), `USE_VULKAN`, `USE_OPENGL` (not on Apple), `USE_LINKED_FFMPEG`,
`SKIP_POSTPROCESS_BUNDLE`, `USE_ASAN`, and `DISABLE_ADVANCE_SIMD`.

**Use when.**

- `Debug` or `Devel`: stepping through the emulator in lldb or gdb, or
  collecting trace logs.
- `Release` with LTO: timing or comparing against official builds.

**Do not use when.**

- Comparing the performance of a `Debug` build with a release binary: the
  optimisation level differs, so the result says nothing about the code
  change.

**Example.** Configure executed here, with the two dependency changes from
the macOS card:

```sh
cmake -S . -B build -G Ninja -DCMAKE_PREFIX_PATH="$PWD/deps" \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_OSX_ARCHITECTURES=x86_64 \
  -DUSE_LINKED_FFMPEG=ON
ninja -k 0 -C build
```

Configure took 8 s. `ninja -k 0` ran 904 of 1006 steps in 65 s. All 24
failures were `.metal.air` shader steps: `cannot execute tool 'metal' due
to missing Metal Toolchain`. On Apple, the metallib custom command in
`pcsx2/CMakeLists.txt` always runs `xcrun metal`. The fix,
`xcodebuild -downloadComponent MetalToolchain`, installs a system component
and was not run here. `-DSKIP_POSTPROCESS_BUNDLE=ON` skips bundle fix-up
on incremental macOS builds.

**Cost removed.** Comparisons across mismatched build types. Observable:
`grep CMAKE_BUILD_TYPE build/CMakeCache.txt` shows the recorded type.

**Verify.**

1. `grep -E 'CMAKE_BUILD_TYPE|CMAKE_OSX_ARCHITECTURES' build/CMakeCache.txt`
   shows the intended values.
1. On macOS, `find build -name PCSX2.app` finds the bundle at
   `build/pcsx2-qt/PCSX2.app`, the path the macOS CI moves.

## ccache compiler launcher

**Definition.** `-DCMAKE_C_COMPILER_LAUNCHER=ccache
-DCMAKE_CXX_COMPILER_LAUNCHER=ccache` runs every compile through ccache,
which returns cached objects for unchanged inputs. The Linux and macOS CI
jobs set `CCACHE_BASEDIR`, `CCACHE_DIR`, `CCACHE_COMPRESS=true`, and
`CCACHE_MAXSIZE=100M`. The macOS job also passes
`-DCMAKE_DISABLE_PRECOMPILE_HEADERS=ON`.

**Use when.**

- Rebuilding repeatedly: bisecting, switching branches, or cleaning build
  directories.

**Do not use when.**

- Only one build is needed: the first build only fills the cache.
- ccache is not installed: configure succeeds and every compile fails.
  Executed here with a one-file C project: configure exited 0, then the
  compile printed `FAILED: [code=127]` and `/bin/sh: ccache:
  command not found`.

**Example.** Not runnable here: `ccache` is not installed, and a Homebrew
install changes the system. The upstream command:

```sh
export CCACHE_DIR="$PWD/.ccache" CCACHE_BASEDIR="$PWD"
cmake -B build -G Ninja -DCMAKE_PREFIX_PATH="$PWD/deps" \
  -DCMAKE_C_COMPILER_LAUNCHER=ccache \
  -DCMAKE_CXX_COMPILER_LAUNCHER=ccache
ccache -z && ninja -C build && ccache -s
```

**Cost removed.** Compile time of unchanged translation units on rebuilds.
Observable: `ccache -s` "Hits" rises on the second build of the same tree.

**Verify.**

1. `grep COMPILER_LAUNCHER build/CMakeCache.txt` shows `ccache`.
1. After `ninja -C build -t clean && ccache -z && ninja -C build`,
   `ccache -s` reports cache hits greater than 0.

## Unit tests target

**Definition.** `ENABLE_TESTS=ON` (the default) adds the `unittests`
custom target, which builds `common_test` and `core_test` (GoogleTest) and
runs `ctest --output-on-failure`. `core_test` includes `patch_tests.cpp`,
which defines 60 `Patch.*` tests of PNACH write semantics.

**Use when.**

- Checking a source change in `common/` or in core code the tests cover,
  such as the patch engine.
- A full build is blocked (for example by Metal) but compiled core code
  still needs checking.

**Do not use when.**

- The claim is about guest behaviour or rendering: the tests do not boot a
  VM.

**Example.** Executed here (x86-64 under Rosetta):

```sh
ninja -C build unittests
build/tests/ctest/core/core_test --gtest_filter='Patch.*'
```

Result: `100% tests passed out of 2` (common 0.36 s, core 8.84 s), and
`[  PASSED  ] 60 tests.` for the patch filter.

**Cost removed.** Needing a BIOS and a game to catch core regressions.
Observable: the ctest pass count.

**Verify.**

1. `ninja -C build unittests` exits 0 and prints `100% tests passed`.
1. Break one expectation in a scratch copy of
   `tests/ctest/core/patch_tests.cpp`; the same command then reports a
   failure.

## GS runner target

**Definition.** `pcsx2-gsrunner` replays GS dumps without the Qt UI. It is
excluded from `all` unless `-DENABLE_GSRUNNER=ON`, but
`ninja pcsx2-gsrunner` still builds it. Its options include `-renderer
auto|dx11|dx12|gl|vulkan|metal|sw`, `-dumpdir`, `-logfile`, `-loop`,
`-surfaceless`, and `-noshadercache`. Apple builds accept `metal`
(`pcsx2-gsrunner/Main.cpp`), although the guide omits it.

**Use when.**

- Comparing renderer output between two builds on the same GS dumps.

**Do not use when.**

- The bug depends on EE or IOP execution, input, or disc timing: a dump
  replays only GS traffic.

**Example.** Not runnable here: macOS runner linking needs the Metal
shaders above, and no GS dumps are bundled. The upstream command:

```sh
cmake -S . -B build -DENABLE_GSRUNNER=ON -DCMAKE_PREFIX_PATH="$PWD/deps" \
  -G Ninja
cmake --build build --target pcsx2-gsrunner
```

**Cost removed.** Booting a game to reproduce a draw. Observable:
one `emulog.txt` and `*_frameN.png` set per dump. See
[GS dump replay comparison](debug-and-render.md#gs-dump-replay-comparison).

**Verify.**

1. `build/pcsx2-gsrunner/pcsx2-gsrunner -help` lists `-renderer`.
1. `-renderer bogus` logs `Unknown renderer 'bogus'` and exits non-zero.

[agents]: https://github.com/PCSX2/pcsx2/blob/2c804670c5f2c99d6a6b842904dd222de89aa493/AGENTS.md
[building]: https://pcsx2.net/docs/advanced/building/
[windeps]: https://github.com/PCSX2/pcsx2-windows-dependencies/releases/
