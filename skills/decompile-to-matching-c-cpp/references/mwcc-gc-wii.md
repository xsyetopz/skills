# MWCC for GameCube and Wii

Facts read from each project's repository on 2026-10-05. Confirm flags with the installed version.

## Contents

- [Compiler Versions](#compiler-versions)
- [Flags in dtk-template](#flags-in-dtk-template)
- [Project Tooling](#project-tooling)
- [Quirks](#quirks)
- [Not Verified](#not-verified)
- [Sources](#sources)

## Compiler Versions

[dtk-template][template] maps each project's `mw_version` to a decomp.me compiler id (`COMPILER_MAP`
in `tools/project.py`):

| `mw_version` | decomp.me id |
| --- | --- |
| GC/1.0 | `mwcc_233_144` |
| GC/1.1 | `mwcc_233_159` |
| GC/1.2.5 | `mwcc_233_163` |
| GC/1.2.5n | `mwcc_233_163n` |
| GC/1.3 | `mwcc_242_53` |
| GC/1.3.2 | `mwcc_242_81` |
| GC/2.0 | `mwcc_247_92` |
| GC/2.5 | `mwcc_247_105` |
| GC/2.6 | `mwcc_247_107` |
| GC/2.7 | `mwcc_247_108` |
| GC/3.0a3 | `mwcc_41_51213` |
| Wii/1.0 | `mwcc_43_145` |
| Wii/1.1 | `mwcc_43_151` |
| Wii/1.3 | `mwcc_43_172` |
| Wii/1.5 | `mwcc_43_188` |
| Wii/1.6 | `mwcc_43_202` |
| Wii/1.7 | `mwcc_43_213` |

decomp.me also lists `mwcc_233_163e`, `mwcc_242_81r`, `mwcc_247_107`, `mwcc_41_*`, `mwcc_42_*`,
`mwcc_43_*`, and ProDG as `prodg_*`. It runs
`wibo mwcceppc.exe -pragma "msg_show_realref off" -c -proc gekko -nostdinc -stderr`.

To confirm the version for a new game, build one function with the candidate ids and compare against
the target. The report did not read a fingerprint table for MWCC, so no per-version prologue shape
is given here. Read the version the project's `configure.py` already pins, when one exists.

## Flags in dtk-template

`cflags_base` in `configure.py`:

```text
-nodefaults -proc gekko -align powerpc -enum int -fp hardware -Cpp_exceptions off -O4,p
-inline auto -pragma "cats off" -pragma "warn_notinlined off" -maxerrors 1 -nosyspath -RTTI off
-fp_contract on -str reuse -multibyte
```

- For Wii compilers, replace `-multibyte` with `-enc SJIS`.
- Debug builds add `-sym on` (Wii: `-sym dwarf-2`).
- Runtime libraries add `-use_lmw_stmw on -str reuse,pool,readonly -gccinc -common off`. REL builds
  add `-sdata 0 -sdata2 0`.
- SDK libraries use `mw_version: "GC/1.2.5n"`, and `config.linker_version` is `"GC/1.3.2"`.

These are the template's defaults, not a statement of what any one game used. The meaning of each
flag was not read.

## Project Tooling

- [decomp-toolkit][dtk] (`dtk`, v1.8.4 on 2026-09-09) is the GameCube and Wii counterpart of splat.
  - `dtk dol split config.yml target` reads `config.yml`, `splits.txt`, and `symbols.txt`.
  - Other commands: `dol diff`, `dol apply`, `dol config`, `elf disasm`, `elf2dol`, `rel`, `rso`,
    `shasum`, `disc`, `ar`, and `demangle`.
  - Build systems call it; it is not meant to be run by hand.
- [dtk-template][template]: `tools/project.py` generates `build.ninja` and `objdiff.json` with
  `"custom_make": ninja` and `"build_target": False`. It downloads pinned tools: dtk v1.8.3, objdiff
  v3.6.1, wibo 1.0.3, binutils 2.42-2, sjiswrap v1.2.2, and compilers tag `20251118`. Compilers come
  from `https://files.decomp.dev/compilers_{tag}.zip`.
- [wibo][wibo] runs `mwcceppc.exe` on Linux and macOS (default), or use wine. sjiswrap handles
  Shift-JIS source.
- objdiff reads `objdiff.json`. Set `reverse_fn_order` on a unit built with `-inline deferred`.
- decomp.dev is the progress hub, fed by objdiff reports.
- [mwccgap][mwccgap] is the MWCC counterpart of asm-processor, written for PSP. It has not been
  checked against GC. Its default `--as-march` is `allegrex`.
- [doldecomp/melee][melee] adds `-DMUST_MATCH` in `configure.py`, and its `debug.c` does
  `#ifdef MUST_MATCH` then `#pragma peephole off`. What its `NONMATCHING` define does was not read.

## Quirks

- `-inline deferred` reverses function order in the object. objdiff's `reverse_fn_order` unit option
  exists for it.
- `-str reuse` and `-str reuse,pool,readonly` change string literal handling, and the template sets
  them differently for game code and runtime libraries.
- A library compiled with a different `mw_version` from game code is normal in the template (SDK at
  GC/1.2.5n, linker at GC/1.3.2). Check each unit's version separately.

## Not Verified

- The explanation of each flag beyond the names above.
- Per-version codegen differences between MWCC releases.
- melee's own documentation of the `NONMATCHING` and `MUST_MATCH` conventions.

## Sources

- dtk-template: <https://github.com/encounter/dtk-template>
- decomp-toolkit: <https://github.com/encounter/decomp-toolkit>
- objdiff: <https://github.com/encounter/objdiff>
- wibo: <https://github.com/decompals/wibo>
- mwccgap: <https://github.com/mkst/mwccgap>
- decomp.me: <https://github.com/decompme/decomp.me>
- decomp.dev: <https://decomp.dev>
- compilers bundle: `https://files.decomp.dev/compilers_{tag}.zip`
- doldecomp/melee: read from the project's repository (no URL recorded in the research)

[template]: https://github.com/encounter/dtk-template
[dtk]: https://github.com/encounter/decomp-toolkit
[wibo]: https://github.com/decompals/wibo
[mwccgap]: https://github.com/mkst/mwccgap
[melee]: https://github.com/doldecomp/melee
