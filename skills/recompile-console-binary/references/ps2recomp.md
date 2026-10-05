# PS2Recomp

Facts read on 2026-10-05 from the repository and its wiki. The project is experimental and very
active (last commit 2026-10-05), so confirm keys against the version you build.

## Contents

- [Overview](#overview)
- [Usage](#usage)
- [Config](#config)
- [Runtime Behavior](#runtime-behavior)
- [Game Overrides](#game-overrides)
- [Maturity and Legal](#maturity-and-legal)
- [Sources](#sources)

## Overview

`ran-j/PS2Recomp`, GPL-3.0, created 2025-04-12, no releases. The README title is "PS2Recomp:
PlayStation 2 Static Recompiler (Experimental)", inspired by N64Recomp. Modules:

- `ps2xAnalyzer`: scans the ELF and writes a TOML.
- `ps2xRecomp`: ELF plus TOML in, C++ out.
- `ps2xRuntime`: memory, function registration, syscall dispatch, hardware stubs.
- `ps2xIOP`: runs R3000A IRX modules with HLE fallbacks.

The repository also contains ps2xStudio, android, vita, and ps2xTest.

Build: CMake 3.20+ and C++20 ("currently tested mainly with MSVC"), on a host with SSE4 or AVX.

```sh
git clone --recurse-submodules https://github.com/ran-j/PS2Recomp.git
cmake -S . -B out/build
cmake --build out/build --config Debug
```

## Usage

- Preferred for retail or stripped games: export function boundaries from Ghidra with
  `ps2xRecomp/tools/ghidra/ExportPS2Functions.java`, then run `./ps2_recomp config.toml`.
- Fallback for ELFs with symbols: `./ps2_analyzer game.elf config.toml`.
- The wiki page "PS2Recomp-Stripped-Game-Walkthrough-For-LLMs" says the Ghidra CSV reduces bad
  function splits and missing starts. Runtime dispatch is address-based (`0xADDR` to function
  pointer), and addresses are build-specific.

## Config

`[general]` keys from the README:

- `input`, `ghidra_output`, `output`, `single_file_output`, `low_memory_mode`,
  `output_worker_threads`
- `patch_syscalls` (false recommended), `patch_cop0`, `patch_cache`
- `stubs`, `skip`, and `[patches] instructions` (raw instruction replacement by address)

Stubs take `handler@0xADDRESS` for stripped games, for example `sceCdRead@0x00123456`. Generic
handlers are `ret0`, `ret1`, and `reta0`.

## Runtime Behavior

- `SYSCALL` calls `runtime->handleSyscall(...)` with the encoded immediate. The runtime tries the
  encoded ID first, then falls back to `$v1`.
- Unresolved static `J` and `JAL` targets fall back to `runtime->lookupFunction(0x...)`.
- Extra `entry_...` wrappers are emitted for discovered internal entries.
- `ps2xAnalyzer` has `detectJumpTables` (`analysis_passes.cpp`) and writes `[jump_tables]` and
  `[[jump_tables.table]]` into the TOML. Its fallback behavior and instruction coverage were not
  checked.
- Log lines to look for: `[Syscall TODO] ...` and `function not found`.

## Game Overrides

Runtime-side C++ per build, in `ps2xRuntime/include/game_overrides.h`:

- Macro: `PS2_REGISTER_GAME_OVERRIDE(name, elfName, entry, crc32, applyFn)`.
- Helper: `ps2_game_overrides::bindAddressHandler(runtime, addr, "handler")`.
- It runs at `loadELF` and replaces EE function bindings by address.

## Maturity and Legal

- README Limitations: "Performance is very bad for VU and GS. Hardware emulation is partial and many
  paths are stubbed."
- The Ps2xRuntime wiki says to expect to implement or fix syscalls and stubs per game, that many
  syscalls and I/O behaviors are incomplete, and that complex DMA, VIF, and GS behaviors may be
  missing or simplified.
- The wiki's PS2-ELF-Files page says "legally owned" disc dump. An optional `.recomp.json` project
  descriptor for recomp.fyi is ignored by PS2Recomp itself and must never contain a game file or a
  link to one.

## Sources

- <https://github.com/ran-j/PS2Recomp> (`README.md`, `ps2xRuntime/include/game_overrides.h`,
  `analysis_passes.cpp`)
- <https://github.com/ran-j/PS2Recomp/wiki> (Stripped Game Walkthrough, Ps2xRuntime, PS2-ELF-Files)
