# Source builds and reproducible artifacts

Research: 2026-09-09. Baseline: **PCSX2 v2.8.2**. The current website contains
older platform/toolchain examples; the pinned release's CMake and CI take
precedence for that release's implementation requirements.

## Linux build

Use a separate checkout and out-of-source build directory. The release supports
Clang/MSVC; GCC is not a supported compiler. Prepare distribution development
libraries for Qt's platform stack, audio/input, graphics and capture, then build
the release's dependency set:

```sh
git clone --recursive https://github.com/PCSX2/pcsx2.git pcsx2-case
cd pcsx2-case
git checkout v2.8.2
git submodule update --init --recursive
.github/workflows/scripts/linux/build-dependencies-qt.sh deps
cmake -S . -B build -G Ninja \
  -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ \
  -DCMAKE_EXE_LINKER_FLAGS_INIT=-fuse-ld=lld \
  -DCMAKE_MODULE_LINKER_FLAGS_INIT=-fuse-ld=lld \
  -DCMAKE_SHARED_LINKER_FLAGS_INIT=-fuse-ld=lld \
  -DCMAKE_PREFIX_PATH="$PWD/deps" \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_INTERPROCEDURAL_OPTIMIZATION=ON
cmake --build build --parallel
```

The Linux executable is `build/bin/pcsx2-qt`. The dependency script performs
downloads/builds and can take substantial resources; inspect its pinned inputs
and retain hashes for repeatability. A separate dependency prefix avoids
changing the normal emulator. CMake rejects an in-source build. Use a new build
directory when switching incompatible toolchains or architectures. [Build
guide][ref-1], [pinned CMake][ref-2].

`Release` optimizes execution, `Devel` adds detailed tracing, and `Debug`
prioritizes debugging over speed. Record the actual compiler flags/symbol
configuration; a debug build is not a fair performance comparison with a release
binary. LTO can alter build cost and runtime performance. Keep
compiler/cache/dependency configuration fixed when testing a code change.

## Windows and macOS differences

For Windows, prepare the Qt dependency pack under `deps` or run the selected
revision's `.github/workflows/scripts/windows/build-dependencies.bat`. Open
`PCSX2_qt.sln` in a compatible Visual Studio desktop-C++ environment and build
the intended x64 configuration. The v2.8.2 workflow uses a Visual Studio 2026
runner and configures clang-cl; the website's older v142 list is not a
sufficient statement of this release's CI toolchain. Match architecture and SIMD
configuration to the destination CPU. [Pinned Windows workflow][ref-3].

For macOS, use Xcode and the pinned
`.github/workflows/scripts/macos/build-dependencies.sh deps` script, then
configure CMake with that prefix and Release. The examined release warns that
native ARM64 recompilers are incomplete; use `-DCMAKE_OSX_ARCHITECTURES=x86_64`
and Intel dependencies for the supported Rosetta path on Apple Silicon. Do not
combine Homebrew ARM libraries with an x86_64 target. `-DUSE_LINKED_FFMPEG=ON`
is the documented video-capture build option; `-DSKIP_POSTPROCESS_BUNDLE=ON`
skips bundle dependency postprocessing for local development and changes
distribution readiness. [macOS instructions][ref-1], [release architecture
warning][ref-2].

For another source revision, resolve compiler, dependencies, and flags from that
revision.

## GS runner and packaged resources

Add `-DENABLE_GSRUNNER=ON` to the configured build when graphics replay is
required, then build the `pcsx2-gsrunner` target or the full configured build.
On Windows, the output basename may include architecture/SIMD. Use the exact
resulting path in the upstream comparison scripts described in
[debugging and evidence](debugging-and-evidence.md). [Runner build
guidance][ref-4].

Shipping builds include resources such as patches that a plain local build may
not contain. The build guide describes placing the patch archive, unextracted,
in `bin/resources`; record the archive revision/hash if it is needed to
reproduce shipping behavior. Match packaged resources when comparing local and
shipping builds.

Retain source/tag resolution, local diff, submodule revisions, dependency
hashes, compiler version, CMake cache, resource hashes and executable hash.
Verification stages are configuration, compilation, process launch, renderer
initialization and guest oracle. Report the first failed stage and its
diagnostic. Keep build outputs in the case directory.

### Ubuntu system dependencies

The build guide examined on the research date lists the following packages
before the pinned dependency-build script. Use a matching supported Ubuntu
environment; other distributions need equivalent development libraries.

```text
build-essential clang cmake curl extra-cmake-modules git libasound2-dev
libaio-dev libavcodec-dev libavformat-dev libavutil-dev libcurl4-openssl-dev
libdbus-1-dev libdecor-0-dev libegl-dev libevdev-dev libfontconfig-dev
libfreetype-dev libgtk-3-dev libgudev-1.0-dev libharfbuzz-dev libinput-dev
libopengl-dev libpcap-dev libpipewire-0.3-dev libpulse-dev libssl-dev
libswresample-dev libswscale-dev libudev-dev libwayland-dev libx11-dev
libx11-xcb-dev libxcb1-dev libxcb-composite0-dev libxcb-cursor-dev
libxcb-damage0-dev libxcb-glx0-dev libxcb-icccm4-dev libxcb-image0-dev
libxcb-keysyms1-dev libxcb-present-dev libxcb-randr0-dev libxcb-render0-dev
libxcb-render-util0-dev libxcb-shape0-dev libxcb-shm0-dev libxcb-sync-dev
libxcb-util-dev libxcb-xfixes0-dev libxcb-xinput-dev libxcb-xkb-dev libxext-dev
libxkbcommon-x11-dev libxrandr-dev lld llvm ninja-build pkg-config zlib1g-dev
```

[ref-1]: https://pcsx2.net/docs/advanced/building/
[ref-2]: https://github.com/PCSX2/pcsx2/blob/v2.8.2/CMakeLists.txt
[ref-3]:
  https://github.com/PCSX2/pcsx2/blob/v2.8.2/.github/workflows/windows_build_qt.yml
[ref-4]: https://pcsx2.net/docs/advanced/gsdumprunner/
