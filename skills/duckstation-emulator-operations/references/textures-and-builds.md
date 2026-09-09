# Texture replacement, patches and source builds

Research: 2026-09-09. Build baseline:
**cbe7951be624a3fd69c81858647a8f84e4a1d06b**. The texture workflow below follows
the official wiki examined on this date (page edited 2024-11-27); refresh
configuration keys for a different implementation rather than assuming all
rolling releases are identical.

## Dump and replace textures

1. In the isolated profile, enable the texture cache under **Graphics Settings →
   Texture Replacements**, then enable texture dumping.
2. Run the target scene and move through the relevant content. Stop the VM
   before reviewing the dump.
3. Open the data directory and inspect `textures/SERIAL/dumps`. Keep the game's
   exact serial/revision with the fixture.
4. Copy selected files into `textures/SERIAL/replacements`, preserving generated
   identities, then edit/resize those copies. PNG, JPG and WebP are documented
   replacement formats.
5. Disable dumping for comparison, enable replacements and repeat the scene.
   Confirm both correct substitution and absence of unintended replacements.

The PS1's VRAM uploads do not map cleanly to modern immutable texture assets.
Filenames encode texture-data hash, palette hash where applicable, upload size,
subrectangle and palette range. Do not rename them to descriptive filenames
without an alias mapping. Wrong palette/subrectangle matching can replace
unrelated content or create many duplicates. Source: [texture
replacement][ref-1].

A game-local `textures/SERIAL/config.yaml` is created when dumping starts.
Adjust one relevant option and redump when it changes identity:

- **Upload tracking cannot identify useful textures** Relevant option and
  tradeoff: `DumpTexturePages` uses drawn page subrectangles; often creates
  duplicates and less reliable matching. `DumpFullTexturePages` captures whole
  pages and is usually less useful.

- **Direct-color content is missing** Relevant option and tradeoff:
  `DumpC16Textures` includes it, but may also dump FMV/postprocessing noise.

- **Unused palette entries cause duplicate identities** Relevant option and
  tradeoff: `ReducePaletteRange` hashes used entries; can improve reliability
  with some CPU overhead.

- **Animated content is assembled through VRAM copies** Relevant option and
  tradeoff: `ConvertCopiesToWrites` tracks those copies, at the cost of
  additional duplicates.

- **Partially overwritten uploads disappear** Relevant option and tradeoff:
  `MaxVRAMWriteSplits` controls tracking splits.

- **Logs repeatedly show one-line uploads** Relevant option and tradeoff:
  `MaxVRAMWriteCoalesceWidth` / `MaxVRAMWriteCoalesceHeight` allow appropriate
  neighboring uploads to combine.

- **Tiny irrelevant dumps dominate** Relevant option and tradeoff:
  Texture/upload width and height thresholds filter them; too high omits useful
  content.

- **Texture packs exhaust memory or stall** Relevant option and tradeoff: Keep
  hash/replacement cache budgets within target RAM/VRAM; increasing them is not
  a universal fix.

Map a dumped identity to a replacement filename in `Aliases`. Replace the key
below with that exact identity:

```yaml
Aliases:
  GENERATED-TEXTURE-IDENTITY: shared-wall.png
```

Keep native-scale, no-replacement and replacement captures at the same
checkpoint. Preloading/cache behavior and replacement resolution affect memory
and timing; disclose them in performance comparisons. Check replacement behavior
in each affected scene.

## Patches and cheats

The examined README distinguishes built-in compatibility/enhancement data, cheat
databases and automatic PPF disc patches. Use the game's properties/cheat
interface to inspect active entries and keep experimental changes in the
isolated data tree. Record the active mechanism: cheats write guest state, PPF
patches alter disc reads, and renderer enhancements change presentation. For an
existing PPF, preserve the original image and match its exact intended disc
revision before enabling it. Do not infer compatibility from title alone.
[Feature and patch documentation][ref-2].

## Build the examined source

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
build instructions][ref-2], [dependency packs][ref-3].

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

### Linux system dependency baseline

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

[ref-1]: https://github.com/stenzek/duckstation/wiki/Texture-Replacement
[ref-2]:
  https://github.com/stenzek/duckstation/blob/cbe7951be624a3fd69c81858647a8f84e4a1d06b/README.md
[ref-3]: https://github.com/duckstation/dependencies
