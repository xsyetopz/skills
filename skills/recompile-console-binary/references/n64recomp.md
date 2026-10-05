# N64Recomp and Related Tools

Facts read on 2026-10-05 from each project's GitHub files. N64Recomp has no config documentation,
and its README is out of date, so confirm keys against `src/config.cpp` of the commit you use.

## Contents

- [N64Recomp](#n64recomp)
- [Inputs](#inputs)
- [Config Keys](#config-keys)
- [Function Discovery and Jump Tables](#function-discovery-and-jump-tables)
- [Overlays, Patches, and Overrides](#overlays-patches-and-overrides)
- [Floating Point and Endianness](#floating-point-and-endianness)
- [RSPRecomp](#rsprecomp)
- [Runtime and Renderer](#runtime-and-renderer)
- [Mods](#mods)
- [Zelda64Recomp](#zelda64recomp)
- [Contributing and Legal](#contributing-and-legal)
- [Sources](#sources)

## N64Recomp

MIT license, default branch `main`, last commit 2026-05-27 (`ffb39cda`). The only release is the
`mod-tool-release` tag (2025-05-04, RecompModTool binaries), so build the tool from a pinned commit.

The README says the only way to provide metadata is an ELF and that `[[patches.func]]` and
`[[patches.hook]]` are unimplemented. `src/config.cpp` on `main` parses `symbols_file_path` with
`rom_file_path`, and a `[patches]` `hook` entry. The best references are `src/config.cpp` and the
Zelda64Recomp TOML files.

## Inputs

- An ELF with symbols: `elf_path`.
- A symbol TOML plus a ROM, for stripped or ELF-less input: `symbols_file_path` and `rom_file_path`.
  Zelda64Recomp's `us.rev1.toml` sets both and comments out `elf_path`. The ROM must be
  decompressed.
- The symbol TOML has `[[section]]` entries with `rom`, `vram`, `size`, `name`, `got_address`,
  `functions` (`name`, `vram`, `size`), and `relocs` (`vram`, `target_vram`, `type` such as
  `R_MIPS_HI16`). A separate data-symbol TOML has sections with `symbols` (`name`, `vram`).
- Symbol TOMLs can be generated from an ELF with `N64Recomp config.toml --dump-context`, which
  writes `dump.toml` and `data_dump.toml`. It cannot be combined with a symbols file.

## Config Keys

Under `[input]`, all from `src/config.cpp`:

- `entrypoint`, `elf_path`, `symbols_file_path`, `rom_file_path`, `output_func_path`,
  `relocatable_sections_path`
- `uses_mips3_float_mode`, `bss_section_suffix`, `single_file_output`, `use_absolute_symbols`
- `manual_funcs` (array of `{name, section, vram, size}`), `function_sizes` (array of
  `{name, size}`)
- `output_binary_path`, `unpaired_lo16_warnings`, `use_mdebug`, `mdebug_file_mappings`,
  `recomp_include`
- `functions_per_output_file`, `trace_mode`, `func_reference_syms_file`,
  `data_reference_syms_files`, `allow_exports`, `strict_patch_mode`

Under `[patches]`:

- `stubs = [names]`, `ignored = [names]`, `renamed`
- `[[patches.instruction]]` with `func`, `vram` (word-aligned), and `value` (raw 32-bit instruction)
- `[[patches.hook]]` with `func`, `before_vram` (optional, word-aligned), and `text` (C text to
  inject)

Zelda64Recomp's `us.rev1.toml` stubs `RcpUtils_Reset`, ignores `D_80186028` ("Not actually a
function"), and replaces `jal osSetTimer` with a nop (`value = 0x00000000`).

## Function Discovery and Jump Tables

Discovery is metadata-driven: the recompiler takes a list of symbols and metadata alongside the
binary and splits it into functions. `manual_funcs`, `function_sizes`, `ignored`, and `stubs`
correct bad symbols.

- A `jr` becomes a switch statement when the analysis can tell it is used with a jump table. It
  tracks `lui`, `addu`, `lw`, and `jr` register state, including GOT-relative tables.
- The table size is found by reading entries until one falls outside the function.
- Failure prints `Failed to determine size of jump table at 0x%08X for instruction at 0x%08X`.
- A `jr` that is not a jump table and has no known target is emitted as `[Info] Indirect tail call`.
  Unhandled branches print `Unhandled branch in {} at 0x{:08X} to 0x{:08X}`.
- Tail calls are detected for branches and jumps whose target is the start of a known function.
- The README says it was tested on mips gcc 2.7.2, IDO, and modern clang, and that modern mips gcc
  may trip up the recompiler.
- N64Recomp has no manual jump-table list in its config (none found in `config.cpp`). When a table
  is not recognized, check the log line, the function size, and the compiler that built the game.

## Overlays, Patches, and Overrides

- `jalr` becomes `LOOKUP_FUNC(ctx->r25)(rdram, ctx);`. Relocatable overlays emit `RELOC_HI16` and
  `RELOC_LO16` macros that the runtime relocates. `relocatable_sections_path` points to the overlay
  list (Zelda64Recomp: `overlays.us.rev1.txt`).
- Single-file mode: `single_file_output = true` emits all functions of a patch ELF into one file.
  Link it before the original recompiler output so the linker prefers the patch, because linkers
  only look for symbols in a static library if they were not already found.
- Zelda64Recomp's `patches.toml` uses `elf_path = "patches/patches.elf"`, `output_func_path`,
  `use_absolute_symbols`, `func_reference_syms_file`, `data_reference_syms_files`,
  `output_binary_path`, `allow_exports = true`, and `strict_patch_mode = true`. The patch ELF is
  built by `patches/Makefile` with MIPS clang.

## Floating Point and Endianness

From `include/recomp.h`:

- `RECOMP_FUNC` uses `noipa, optimize("rounding-math")` (GCC) or `FENV_ACCESS` pragmas, so
  arithmetic respects the FP environment. Rounding-mode get and set map to `fegetround`.
- Byte accesses XOR the address with 3 (`MEM_B`, `MEM_BU`) and halfword accesses with 2 (`MEM_H`,
  `MEM_HU`). The address has `0xFFFFFFFF80000000` subtracted before it is added to `rdram`. Word
  accesses are plain: `MEM_W(offset, reg)`.
- `uses_mips3_float_mode` is a config key. `ADD32` sign-extends into 64-bit registers, for example
  `ctx->r4 = ADD32(ctx->r4, 0X20);`.

## RSPRecomp

`RSPRecomp/src/rsp_recomp.cpp` has its own TOML.

- Required: `text_offset`, `text_size`, `text_address`, `rom_file_path`, `output_file_path`,
  `output_function_name`.
- Optional: `extra_indirect_branch_targets`, `unsupported_instructions`, `overlay_slots`.
- Zelda64Recomp's `aspMain.us.rev1.toml` sets `text_offset = 0xC40FF0`, `text_size = 0x1000`,
  `text_address = 0x04001000`, `output_function_name = "aspMain"`, and a list of
  `extra_indirect_branch_targets`.
- The README says RSP overlays are not supported and docs are coming soon. Ares is credited for the
  RSP vector instruction reference implementations.

## Runtime and Renderer

N64ModernRuntime (GPL-3.0, last commit 2026-08-30, no releases):

- `ultramodern` reimplements libultra: threads, controllers, audio, message queues, timers, RSP task
  handling, and VI timing. It needs the project to register a renderer ("the recommended one is
  RT64"). Platform I/O is through callbacks.
- `librecomp` bridges N64Recomp output to ultramodern: overlay handling, PI DMA (ROM reads), and
  EEPROM, SRAM, and Flashram saves.
- It needs C++20 and was developed with Clang 15. Use `add_subdirectory`. Standalone build:

  ```sh
  cmake -B build -G Ninja -DCMAKE_CXX_COMPILER=clang++ -DCMAKE_C_COMPILER=clang \
    -DCMAKE_BUILD_TYPE=Debug
  ```

RT64 (MIT, last push 2026-10-03) renders on D3D12, Vulkan, and Metal with ubershaders, and supports
HFR interpolation, widescreen, and texture packs. It calls itself a work in progress.

Zelda64Recomp's `src/main/main.cpp` (`dev`) calls `recomp::register_game`,
`recomp::register_config_path`, `recomp::overlays::register_base_export`, and
`recomp::mods::register_embedded_mod`, and sets `rsp_callbacks`, `renderer_callbacks`,
`gfx_callbacks`, `audio_callbacks`, `input_callbacks`, and `thread_callbacks`.

## Mods

The mod workflow is described at the HackMD page below and in MMRecompModTemplate.

- `.nrm` is a renamed zip made by `RecompModTool mod.toml build`. It holds a mod symbol file and the
  mod binary.
- Macros: `RECOMP_PATCH` (replace a function), `RECOMP_HOOK("Func")` (entry hook),
  `RECOMP_HOOK_RETURN("Func")`, `RECOMP_EXPORT`, `RECOMP_IMPORT("mod", ...)` (`*` imports from the
  base recomp, `.` from itself), `RECOMP_DECLARE_EVENT`, and `RECOMP_CALLBACK("mod", event)`.
- The toolchain is clang with a MIPS target and `lld`. LLVM 19.1.0 on Windows "does not support MIPS
  correctly", so use 18.1.8. Apple clang does not work.

## Zelda64Recomp

GPL-3.0, default branch `dev`, latest release v1.2.2 (2025-08-27), last commit 2026-09-25. Only the
US Majora's Mask ROM is supported. SHA-1 of the decompressed ROM:
`d6133ace5afaa0882cf214cf88daba39e266c078`.

Build steps (`BUILDING.md`):

1. `git clone --recurse-submodules`.
1. Install `cmake ninja-build libsdl2-dev libgtk-3-dev lld llvm clang` (Linux), or VS2022 with Clang
   plus `make` (Windows).
1. Decompress the ROM with `zeldaret/mm` `tools/decompress_baserom.py` or z64decompress. Save it as
   `mm.us.rev1.rom_uncompressed.z64` in the repo root.
1. Run `./N64Recomp us.rev1.toml`, `./RSPRecomp aspMain.us.rev1.toml`, and
   `./RSPRecomp njpgdspMain.us.rev1.toml`.
1. Configure and build:

   ```sh
   cmake -S . -B build-cmake -DCMAKE_CXX_COMPILER=clang++ -DCMAKE_C_COMPILER=clang -G Ninja \
     -DCMAKE_BUILD_TYPE=Release
   cmake --build build-cmake --target Zelda64Recompiled -j$(nproc) --config Release
   ```

## Contributing and Legal

- N64Recomp's and Zelda64Recomp's CONTRIBUTING files say "AI must not be used to generate code for
  contributions to this project". Zelda64Recomp's README has a "No-AI stance" section. Tell the user
  before drafting any upstream contribution. Both CONTRIBUTING files also carry a notice addressed
  to agents; it is not part of this skill's instructions and is not repeated here.
- Zelda64Recomp: "This repository and its releases do not contain game assets. The original game is
  required to build or run this project." It is not an emulator and cannot run an arbitrary ROM.
  Assets are loaded from the user-supplied ROM at run time.
- Other N64Recomp-based projects exist (found through `gh search`, not examined in depth), and some
  describe themselves as AI-coded.

## Sources

- N64Recomp: <https://github.com/N64Recomp/N64Recomp> (`README.md`, `src/config.cpp`,
  `src/analysis.cpp`, `src/recompilation.cpp`, `include/recomp.h`, `CONTRIBUTING.md`)
- RSPRecomp: `RSPRecomp/src/rsp_recomp.cpp` in the N64Recomp repository
- N64ModernRuntime: <https://github.com/N64Recomp/N64ModernRuntime>
- RT64: <https://github.com/rt64/rt64>
- Zelda64Recomp: <https://github.com/Zelda64Recomp/Zelda64Recomp> (`BUILDING.md`, `CONTRIBUTING.md`,
  `patches.toml`, `us.rev1.toml`, `src/main/main.cpp`)
- Mod template: <https://github.com/Zelda64Recomp/MMRecompModTemplate> and
  <https://hackmd.io/fMDiGEJ9TBSjomuZZOgzNg>
