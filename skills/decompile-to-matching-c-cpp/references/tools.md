# Matching Tools

Facts read from each tool's repository on 2026-10-05. Confirm flags with the installed version's
`--help`, because these tools change often and some have no releases.

## Contents

- [splat](#splat)
- [decomp-toolkit](#decomp-toolkit)
- [objdiff](#objdiff)
- [m2c](#m2c)
- [decomp-permuter](#decomp-permuter)
- [asm-differ](#asm-differ)
- [decomp.me](#decompme)
- [Sources](#sources)

## splat

Splits N64, PSX, PS2, and PSP binaries into assembly, data, and C stubs, and writes a linker script.
GameCube and Wii are not supported; use decomp-toolkit.

- Install: `python3 -m pip install -U 'splat64[mips]'` (the `mips` extra is required for all four
  platforms). Pin it, for example `splat64[mips]>=0.50.0,<1.0.0`.
- Commands: `splat split <config>.yaml` and `splat create_config <binary>`.
- `options` keys: `platform` (`n64`, `psx`, `ps2`, `psp`), `compiler` (`GCC`, `SN64`, `IDO`, `KMC`,
  `EGCS`, `PSYQ`, `MWCCPS2`, `EEGCC`; default `IDO`), `basename` (required), `target_path`,
  `asm_path` (`asm`), `src_path` (`src`), `ld_script_path`, `symbol_addrs_path`,
  `migrate_rodata_to_functions` (default true), `include_asm_macro_style` (`default` or
  `maspsx_hack`).
- `symbol_addrs.txt` lines: `osInitialize = 0x801378C0; // type:func size:0x40`. No spaces inside a
  `key:value` pair. Since 0.50.0, an overlay symbol needs `segment:` or `rom:`, and a symbol in no
  segment needs `absolute:True`. Do not pass this file to the linker; pass the generated
  `undefined_syms_*.txt` instead.
- Segment types include `asm`, `hasm` (like `asm`, but never overwrites an existing file), `c`,
  `data`, `rodata`, `bss` (needs `bss_size`), and `bin`. Types starting with a dot are link-only.
- A `c` segment creates the `.c` file when it is missing. Otherwise splat reads the existing file to
  decide which functions still need assembly, and writes each one to `nonmatchings/`.
- splat writes the include header for GCC-style projects, not for IDO or MWCCPS2.

## decomp-toolkit

`dtk` is the GameCube and Wii counterpart of splat: `dtk dol split config.yml target`, with
`config.yml`, `splits.txt`, and `symbols.txt`. Build systems call it; start from
[dtk-template][dtk-template], whose `configure.py` generates `build.ninja` and `objdiff.json` and
downloads pinned tool and compiler versions.

## objdiff

Diffs relocatable objects function by function. Architectures: ARM, ARM64, MIPS, PowerPC, SuperH,
x86, and x86-64.

- Install the prebuilt `objdiff-cli` from the releases page, or
  `cargo install --locked --git https://github.com/encounter/objdiff.git objdiff-cli`.
- `objdiff.json` sits at the project root and is usually generated and ignored by Git. Schema:
  `https://raw.githubusercontent.com/encounter/objdiff/main/config.schema.json`.
  - Top level: `custom_make` (default `make`), `custom_args`, `build_target` (default false),
    `build_base` (default true), `units`, `progress_categories`. `objects` is deprecated.
  - Unit: `name`, `target_path` (the reference object), `base_path` (your build; omit it while no
    source exists), `metadata` (`complete`, `source_path`, `progress_categories`), and
    `scratch` (`platform`, `compiler`, `c_flags`, `ctx_path`).
  - `reverse_fn_order` supports MWCC's `-inline deferred`, which emits functions in reverse order.
- `objdiff-cli diff -p <dir> -u <unit> <symbol>` is interactive. Add `-o -` (stdout) or `-o file`
  with `--format json` for one-shot output an agent can read. Objects can be given directly with
  `-1 <target.o> -2 <base.o>`.
- `objdiff-cli report generate -p . -o report.json` writes a progress report.
  `objdiff-cli report changes <prev> <curr>` compares two reports.
- Exit status: 1 on any error (`Failed: ...` on stderr), 0 otherwise.

## m2c

Turns GNU `as` assembly (from spimdisasm, for example) into C as a first draft.

- Run from a clone: `python3 m2c.py -t <arch>-<compiler>-<lang> --context ctx.h -f Func file.s`.
  Arch: `mips`, `mipsel`, `mipsee`, `ppc`, `arm`, `gba`, `sh2`. Compiler: `ido`, `gcc`, `mwcc`.
  Lang: `c`, `c++`.
- `--context` can repeat. A struct named `_m2c_stack_<fn>` sets the stack layout, and its size must
  equal the frame size.
- `--valid-syntax` aims for output that compiles without edits, as permuter input. `--no-andor`,
  `--no-switches`, and `--gotos-only` change the control-flow shape when the default is wrong.
- Loops are often not in the original shape. It cannot infer structs with bitfields or unnamed
  unions.

## decomp-permuter

Randomly rewrites a function and keeps changes that lower the diff score. Targets MIPS (IDO,
possibly GCC), PowerPC, and ARM32.

- Prerequisites: `python3 -m pip install toml Levenshtein` (`pynacl` only for permuter@home).
- `./import.py <file.c> <file.s>` creates a working directory with `base.c`, `target.o`,
  `compile.sh`, and `settings.toml`. It reads the project makefile; Ninja projects set
  `build_system = "ninja"` in `permuter_settings.toml`.
- `./permuter.py <dir>/ -j 8`. Use `--debug` first to check that the base compiles. `--stop-on-zero`
  ends at the first full match. Stack positions are ignored unless `--stack-diffs`.
- Macros narrow the search: `PERM_GENERAL(a, b)`, `PERM_VAR`, `PERM_LINESWAP`, `PERM_INT(lo, hi)`,
  `PERM_FORCE_SAMELINE` (IDO codegen depends on which statements share a line), and
  `PERM_RANDOMIZE(code)`. Any multi-choice macro turns off random rewriting outside
  `PERM_RANDOMIZE`.
- The README calls the scorer "far from a perfect system", weak on stack differences, and good near
  the end when mostly register allocation differs. A matching result is not necessarily the
  original source.

## asm-differ

`diff.py` from the directory holding `diff_settings.py`; the README recommends `-mwo` (make, watch,
diff objects). `-3` and `-b` show three-way diffs and need `-w`. It exits 1 on failure. Its README
now points to objdiff as the modern alternative.

## decomp.me

A public site of per-function scratches. Scratches have no privacy setting, and anonymous ones can
be claimed later. Platform IDs include `n64`, `ps1`, `ps2`, `psp`, `gc_wii`, `win32`, and
`xbox360`; there is no PS3 platform. A scratch's `compiler` and `compiler_flags` record the setup
that matched, so copy them into the project's build when a user shares a matching scratch.

## Sources

- splat: <https://github.com/ethteck/splat> (0.50.0; `docs/Configuration.md`,
  `docs/Segments.md`, `docs/Adding-Symbols.md`, wiki General Workflow)
- decomp-toolkit: <https://github.com/encounter/decomp-toolkit> (v1.8.4)
- objdiff: <https://github.com/encounter/objdiff> (v3.8.2; README, `config.schema.json`,
  `objdiff-cli/src`)
- m2c: <https://github.com/matt-kempster/m2c> (branch `master`)
- decomp-permuter: <https://github.com/simonlindholm/decomp-permuter>
- asm-differ: <https://github.com/simonlindholm/asm-differ>
- decomp.me: <https://github.com/decompme/decomp.me> (`backend/coreapp/models/scratch.py`,
  `cromper/cromper/platforms.py`)

[dtk-template]: https://github.com/encounter/dtk-template
