# PsyQ, ee-gcc, and MWCC for PS1 and PS2

Facts read from each project's repository on 2026-10-05. Confirm tool flags with the installed
version's `--help`, because these tools change often.

## Contents

- [PS1 PsyQ and Old gcc](#ps1-psyq-and-old-gcc)
- [PS2 ee-gcc](#ps2-ee-gcc)
- [MWCC for PS2 and PSP](#mwcc-for-ps2-and-psp)
- [Project Tooling](#project-tooling)
- [Quirks](#quirks)
- [Not Verified](#not-verified)
- [Sources](#sources)

## PS1 PsyQ and Old gcc

Compiler versions known to decomp.me (platform `ps1`):

- PsyQ: `psyq3.3`, `psyq3.5`, `psyq3.6`, `psyq4.0`, `psyq4.1`, `psyq4.3`, `psyq4.4`, `psyq4.5`,
  `psyq4.6`, and `psyq_263_221`.
- gcc builds: `gcc2.5.7-psx` through `gcc2.95.2-psx` (2.6.0, 2.6.3, 2.7.2, 2.8.0, 2.8.1, 2.91.66,
  2.95.2) and `gcc2.7.2-cdk`.

The decomp.me PsyQ pipeline is `cpp -P | unix2dos | wibo CC1PSX.EXE -quiet ...`, then
`wibo ASPSX.EXE -quiet ...`, then `psyq-obj-parser`. The gcc builds come from
[decompals/old-gcc][old-gcc], which has Dockerfiles for gcc 2.5.7 through 2.95.2, including the
`-psx` variants and `gcc-2.7.2-cdk`.

Projects that build with old-gcc use `maspsx` and `mipsel-linux-gnu-as` in place of ASPSX. The
sotn-decomp Makefile sets `CROSS := mipsel-linux-gnu-`, runs `maspsx.py`, and fetches prebuilt
`cc1-psx` tarballs from its own release tag `cc1-psx-26`.

To confirm the compiler for a new game, build the same small function with several versions from the
lists above and compare the prologue and the instruction order against the target. The report did
not read a fingerprint table for these compilers, so no per-version prologue shape is given here.

## PS2 ee-gcc

- Versions: 2.9-990721, 2.9-991111 variants, 2.95.2-273a and 274, 2.95.3-107, 114, and 136, 2.96,
  3.2-030926, and 3.2-040921. IOP code uses gcc 2.8.1 or 2.95.2-102.
- decomp.me compiler ids include `ee-gcc2.9-990721`, `ee-gcc2.95.2-273a`, `ee-gcc2.95.3-107`,
  `ee-gcc2.96`, `ee-gcc3.2-030926`, `ee-gcc3.2-040921`, and `iop-gcc2.8.1`. It runs
  `bin/ee-gcc -c -B bin/ee-`.
- splat uses `compiler: EEGCC` for these games.

## MWCC for PS2 and PSP

- decomp.me ids run from `mwcps2-2.3-991202` through `mwcps2-3.0.1b210-060308`, run as
  `wibo mwccps2.exe -c $COMPILER_FLAGS -nostdinc -stderr`.
- splat has `compiler: MWCCPS2` and does not generate `include_asm.h` for it.
- PSP uses `mwccpsp_3.0.1_*` and [mwccgap][mwccgap].

## Project Tooling

- splat splits PSX and PS2 binaries (`platform: psx` or `ps2`). `compiler` takes `PSYQ`, `GCC`,
  `EGCS`, `EEGCC`, or `MWCCPS2`. The `gte_macros.inc` file is PSX only. PS2 adds the segment types
  `lit4`, `lit8`, `ctor`, and `vtables`.
- [maspsx][maspsx] replaces `ASPSX.EXE` plus `psyq-obj-parser` with GNU `as`.
  - Flags: `--aspsx-version=2.78`, `--run-assembler`, `--gnu-as-path`, `--expand-div`,
    `--macro-inc`, `--use-comm-section`, `--use-comm-for-lcomm`, `--max-comm-alignment`, `-G8`,
    `--dont-force-G0`, and `--passthrough`.
  - Its README lists behavior differences between ASPSX versions 1.05 and 2.86. The
    `--aspsx-version` flag is marked experimental.
  - `-gcoff` gives line numbers in asm-differ.
  - Listed users: sotn-decomp, open-ribbon, esa, croc, soul-re, silent-hill-decomp,
    rayman-ps1-decomp, spyro-1, and medievil-decomp.
- [asm-processor][asm-processor] gives `GLOBAL_ASM` and `INCLUDE_ASM` to IDO and similar builds. See
  [`ido-kmc.md`](ido-kmc.md).
- [mwccgap][mwccgap] is the MWCC counterpart: `mwccgap input.c output.o [mwcc flags]`. It replaces
  each `INCLUDE_ASM` function with nops, then fills in the assembly. Options include `--mwcc-path`
  (default `mwccpsp.exe`), `--use-wibo`, `--as-march` (default `allegrex`), and `--as-flags`
  (default `-G0`). The defaults point to PSP; its use with PS2 MWCC is not confirmed here.
- [wibo][wibo] runs 32-bit Windows command-line tools such as `CC1PSX.EXE` and `mwccps2.exe` on
  Linux and macOS: `wibo [options] <program.exe> [args...]`.
- [decomp-permuter][permuter]: sotn-decomp has `tools/sotn_permuter/permuter_settings.us.toml`, so
  it uses the permuter. Its `include_asm.h` guards the macro with `#if !defined(PERMUTER)`.

## Quirks

- A non-zero `-G` can make gcc place functions after data, which breaks the `INCLUDE_ASM` macro.
  maspsx works around it by wrapping each `__asm__` in a function named `__maspsx_include_asm_hack*`
  with `# maspsx-keep` lines. splat generates a compatible macro with
  `include_asm_macro_style: maspsx_hack`.
- GNU `as` needs `-G0`. The ASPSX version changes how macros expand, so a wrong ASPSX version in the
  maspsx options changes the bytes. Check the maspsx table before steering the C.
- The SN PS2 compilers have a "short loop bug" that inserts extra nops. splat's
  `align_on_branch_labels` option is the workaround.
- sotn-decomp's `INCLUDE_ASM` also emits a symbol `NAME.NON_MATCHING` in the assembly, so an
  unmatched function shows in the object.

## Not Verified

- PS2 project repositories that document ee-gcc codegen quirks were not searched for.
- Per-version prologue shapes and flag meanings for PsyQ and ee-gcc were not read.
- The decomp.me preset list was not enumerated, because Cloudflare blocked the live API.

## Sources

- decomp.me compilers: <https://github.com/decompme/decomp.me> (`cromper/cromper/compilers.py`)
- old-gcc: <https://github.com/decompals/old-gcc>
- maspsx: <https://github.com/mkst/maspsx>
- mwccgap: <https://github.com/mkst/mwccgap>
- asm-processor: <https://github.com/simonlindholm/asm-processor>
- wibo: <https://github.com/decompals/wibo>
- splat: <https://github.com/ethteck/splat>
- decomp-permuter: <https://github.com/simonlindholm/decomp-permuter>
- sotn-decomp Makefile and `include_asm.h`: read from the project's repository (no URL recorded in
  the research)

[old-gcc]: https://github.com/decompals/old-gcc
[maspsx]: https://github.com/mkst/maspsx
[mwccgap]: https://github.com/mkst/mwccgap
[asm-processor]: https://github.com/simonlindholm/asm-processor
[wibo]: https://github.com/decompals/wibo
[permuter]: https://github.com/simonlindholm/decomp-permuter
