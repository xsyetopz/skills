# IDO and KMC gcc for N64

Facts read from each project's repository on 2026-10-05. Confirm flags with the installed version.

## Contents

- [Compilers and Where They Come From](#compilers-and-where-they-come-from)
- [Flags in Known Projects](#flags-in-known-projects)
- [Project Tooling](#project-tooling)
- [Quirks](#quirks)
- [Not Verified](#not-verified)
- [Sources](#sources)

## Compilers and Where They Come From

- IDO 5.3 and 7.1 (N64 and IRIX). [ido-static-recomp][ido] builds both as native tools, last pushed
  2025-07-05.
  - 5.3 provides `cc`, `acpp`, `as0`, `as1`, `cfe`, `copt`, `ugen`, `ujoin`, `uld`, `umerge`,
    `uopt`, `usplit`, `ld`, `strip`, and `upas`. 7.1 has the same set minus `copt`, `ld`, and
    `strip`.
  - Build: `make setup`, then `make VERSION=5.3` and `make VERSION=7.1`. Output goes to
    `build/{5.3|7.1}/out`. Add `RELEASE=1` for optimized builds and `TARGET=universal` for macOS fat
    builds. Linux and macOS (with Homebrew make) are listed.
- KMC gcc: decomp.me `gcc2.7.2kmc`, built from [decompals/mips-gcc-2.7.2][kmc], last pushed
  2025-11-21. splat uses `compiler: KMC`, and its docs advise KMC rather than GCC for non-IDO N64
  games.
- Other N64 ids on decomp.me: `ido5.2`, `ido5.3`, `ido5.3_c++`, `ido6.0`, `ido7.1`, `mips_pro_744`,
  `gcc2.8.1pm`, `gcc2.7.2sn*`, and `egcs_1.1.2-4`. Some OoT overlays are built with EGCS.

decomp.me compile commands:

- IDO 7.1:
  `cc -c -Xcpluscomm -G0 -non_shared -Wab,-r4300_mul -woff 649,838,712 -32 ${COMPILER_FLAGS}`
- KMC: `gcc -c -G0 -mgp32 -mfp32 ${COMPILER_FLAGS}`

## Flags in Known Projects

sm64 (Makefile):

- The `ido` compiler is the default. `OPT_FLAGS` is `-g` for US and JP and `-O2` for EU, SH, and CN.
  `MIPSISET := -mips2`.
- Shared flags: `-G 0 -non_shared -Wab,-r4300_mul -Xcpluscomm -Xfullwarn -signed -32`.
- Some files override to `-g`, and libultra uses no optimization flag.
- It runs `tools/ido-static-recomp/build/out` or qemu-irix. `COMPILER=gcc` gives a non-matching
  build.

OoT (Makefile):

- IDO 7.1 is the main compiler and 5.3 is `CC_OLD`.
- Debug builds use `-O2`; non-debug builds use `-O2 -g3`. `ASOPTFLAGS := -O1`.
- CFLAGS:
  `-G 0 -non_shared -fullwarn -verbose -Xcpluscomm -Wab,-r4300_mul -woff 516,609,649,838,712,807`.
  `MIPS_VERSION := -mips2`, and some files override it.

To find the version and flags of a new game, start from these sets. Libraries often differ from game
code, so check each file's optimization level separately.

## Project Tooling

- splat: `platform: n64`, `compiler: IDO` (the default) or `KMC`. The test config
  `test/basic_app/splat.yaml` uses `compiler: KMC`.
- IDO projects use `GLOBAL_ASM(...)` or `#pragma GLOBAL_ASM("file.s")` through
  [asm-processor][asmproc]. splat does not generate `include_asm.h` for IDO.
  - Usage: `build.py $CC -- $AS $ASFLAGS -- $CFLAGS -o out.o in.c`.
  - It treats `INCLUDE_ASM("folder", fn)` and `INCLUDE_RODATA` as equivalent.
  - It does not support `-O3`, because of function reordering. It supports the IDO flags `-g`,
    `-g3`, `-O1`, `-O2`, `-framepointer`, `-mips1`, and `-mips2`.
  - A Rust build exists at `tools/asm-processor/rust/Cargo.toml`.
- [m2c][m2c] targets IDO with `-t mips-ido-c`.
- [decomp-permuter][permuter] supports "MIPS (compiled by IDO, possibly GCC)".
- GCC-style projects use `INCLUDE_ASM` and `INCLUDE_RODATA`; IDO projects use `GLOBAL_ASM`.

## Quirks

- Same-lineness affects IDO codegen: whether statements sit on one source line changes the output.
  decomp-permuter provides `PERM_FORCE_SAMELINE(code)` for this.
- asm-processor does not support `-O3`, so `GLOBAL_ASM` cannot stand in for unmatched functions in a
  file built with it.
- sm64 and OoT both pass `-Wab,-r4300_mul` and `-G 0` in their shared flags.

## Not Verified

- Per-version IDO prologue fingerprints and how to tell 5.3 from 7.1 from the target alone were not
  read.
- Which KMC flags known projects use was not read beyond the decomp.me command.

## Sources

- ido-static-recomp: <https://github.com/decompals/ido-static-recomp>
- mips-gcc-2.7.2: <https://github.com/decompals/mips-gcc-2.7.2>
- asm-processor: <https://github.com/simonlindholm/asm-processor>
- sm64 and OoT Makefiles: read from the projects' repositories (no URL recorded in the research)
- splat: <https://github.com/ethteck/splat>
- decomp-permuter: <https://github.com/simonlindholm/decomp-permuter>
- m2c: <https://github.com/matt-kempster/m2c>
- decomp.me compilers: <https://github.com/decompme/decomp.me> (`cromper/cromper/compilers.py`)

[ido]: https://github.com/decompals/ido-static-recomp
[kmc]: https://github.com/decompals/mips-gcc-2.7.2
[asmproc]: https://github.com/simonlindholm/asm-processor
[m2c]: https://github.com/matt-kempster/m2c
[permuter]: https://github.com/simonlindholm/decomp-permuter
