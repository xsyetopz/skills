# MSVC x86 for Win32 and the Original Xbox

Facts read from each project's repository on 2026-10-05.

## Contents

- [Compiler Versions](#compiler-versions)
- [Project Tooling](#project-tooling)
- [Original Xbox](#original-xbox)
- [Not Verified](#not-verified)
- [Sources](#sources)

## Compiler Versions

- decomp.me lists `msvc4.0` through `msvc8.0p` for `win32`. It runs
  `wibo Bin/CL.EXE /c /nologo /I"Z:..." ... /Fd"Z:/tmp/" /Bk"Z:/tmp/" /Fo"Z:..."`. The Xbox build
  uses `CL_XBOX`.
- [reccmp][reccmp] covers "C++ compiled to 32-bit x86 with old versions of MSVC (like 4.20)". Newer
  MSVC support is "in progress", and other compilers and architectures are "not supported".
- The LEGO Island repository ([isle][isle]) is the one reccmp cites for building with old MSVC.

The research found no per-version MSVC flag set for matching and no compiler fingerprint table.
Compare candidate `msvc*` ids from decomp.me against the target.

## Project Tooling

[reccmp][reccmp] (`pip install reccmp`) is the LEGO Island toolchain, pushed 2026-10-05.

- Commands: `reccmp-project create|detect`, `reccmp-reccmp --target <T>`, `reccmp-decomplint`,
  `reccmp-stackcmp`, `reccmp-datacmp`, `reccmp-vtable`, `reccmp-aggregate`, `reccmp-roadmap`, and
  `reccmp-verexp`.
- It matches functions by source annotations such as `// FUNCTION: LEGO1 0x100b12c0`.
- A PDB is required for comparing.
- [wibo][wibo] runs `CL.EXE` on Linux and macOS: `wibo [options] <program.exe> [args...]`.
- objdiff supports x86 and x86-64 and demangles MSVC names. [asm-differ][asmdiffer] supports x86 "to
  a limited extent".

For counting progress, MSVC `_emit` bytes do not count as reconstructed code. See
[`inputs-and-comparison.md`](inputs-and-comparison.md).

## Original Xbox

The original Xbox has no true matching project that the research found. halo-re/halo is a
"Decompilation Research Project" that patches reimplemented functions into the original executable.
It builds with Visual Studio or Clang and does not match bytes. Its last push was 2023-10-09, so it
is stale. For the Xbox 360, see [`xenon-cell.md`](xenon-cell.md).

## Not Verified

- Version-specific MSVC flags for matching.
- Whether other original-Xbox projects exist beyond the search done.
- How reccmp handles MSVC newer than 4.20 ("in progress" per its README).

## Sources

- reccmp: <https://github.com/isledecomp/reccmp>
- isle: <https://github.com/isledecomp/isle>
- halo-re/halo: <https://github.com/halo-re/halo>
- wibo: <https://github.com/decompals/wibo>
- asm-differ: <https://github.com/simonlindholm/asm-differ>
- decomp.me compilers: <https://github.com/decompme/decomp.me> (`cromper/cromper/compilers.py`)

[reccmp]: https://github.com/isledecomp/reccmp
[isle]: https://github.com/isledecomp/isle
[wibo]: https://github.com/decompals/wibo
[asmdiffer]: https://github.com/simonlindholm/asm-differ
