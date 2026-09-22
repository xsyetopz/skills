# DuckStation PS1 emulator: compile and check artifacts

Pinned-source reference carried from the supplied archive; confirm the checkout
below. Build commands are project integration procedures, not evidence that a
build has run on this host.

## DuckStation source builds overview

Use a separate checkout and build directory, pin the commit and record
dependency-pack hashes. Do not replace the user's installed emulator. Upstream
dependency packs are separate from the emulator source, so a pinned source with
a moving dependency archive is not a fully reproducible build.

For Linux, the revision's README requires Clang/LLVM, CMake, Ninja, development
libraries for the window/audio/input stack and the `deps-linux-x64.tar.xz` pack
extracted under `dep/prebuilt` (matching cross packs for other architectures).
After preparing those dependencies:

```sh
git clone https://github.com/stenzek/duckstation.git duckstation-case
cd duckstation-case
git checkout cbe7951be624a3fd69c81858647a8f84e4a1d06b
cmake -S . -B build-release -G Ninja \
  -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ \
  -DCMAKE_EXE_LINKER_FLAGS_INIT=-fuse-ld=lld \
  -DCMAKE_MODULE_LINKER_FLAGS_INIT=-fuse-ld=lld \
  -DCMAKE_SHARED_LINKER_FLAGS_INIT=-fuse-ld=lld \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_INTERPROCEDURAL_OPTIMIZATION=ON
cmake --build build-release --parallel
```

The documented Linux output is `build-release/bin/duckstation-qt`. Missing
Qt/platform or system libraries are dependency failures, not evidence of a guest
regression. The Ubuntu/Debian system-library list is included below; the
selected distribution must supply equivalent development dependencies. [Pinned
build instructions][source-0-1], [dependency packs][ref-dependency-packs].

On Windows, this revision calls for Visual Studio 2026 or newer with desktop
C++, the matching Windows dependency pack under `dep/prebuilt`, and
`duckstation.sln`. Build the intended architecture/configuration; x64 output is
under `bin/x64`. On macOS, use Xcode/CMake and the universal dependency pack,
configure `build-release` with Release/LTO and build with CMake; the app is
under the build's `bin` directory. For another source revision, use its compiler
and dependency requirements.

Record compiler, dependency hashes, CMake cache/configuration, local patches and
resulting executable hash. Compilation, launch, renderer initialization and
guest checkpoint are separate verification stages. Before redistribution, check
the selected source's license and contribution terms.

[source-0-1]:
  https://github.com/stenzek/duckstation/blob/cbe7951be624a3fd69c81858647a8f84e4a1d06b/README.md

## Linux system dependency baseline

The examined README lists these Ubuntu/Debian development packages before the
dependency pack and CMake steps. Package names are distribution-specific; do not
apply this list as a command on Fedora/macOS.

```text
autoconf automake build-essential clang cmake curl extra-cmake-modules git
libasound2-dev libcurl4-openssl-dev libdbus-1-dev libdecor-0-dev libegl-dev
libevdev-dev libfontconfig-dev libfreetype-dev libgtk-3-dev libgudev-1.0-dev
libharfbuzz-dev libinput-dev libopengl-dev libpipewire-0.3-dev libpulse-dev
libssl-dev libudev-dev libwayland-dev libx11-dev libx11-xcb-dev libxcb1-dev
libxcb-composite0-dev libxcb-cursor-dev libxcb-damage0-dev libxcb-glx0-dev
libxcb-icccm4-dev libxcb-image0-dev libxcb-keysyms1-dev libxcb-present-dev
libxcb-randr0-dev libxcb-render0-dev libxcb-render-util0-dev libxcb-shape0-dev
libxcb-shm0-dev libxcb-sync-dev libxcb-util-dev libxcb-xfixes0-dev
libxcb-xinput-dev libxcb-xkb-dev libxext-dev libxkbcommon-x11-dev libxrandr-dev
libxss-dev libtool lld llvm nasm ninja-build pkg-config zlib1g-dev
```

[ref-dependency-packs]: https://github.com/duckstation/dependencies
