# Xenon and Cell PowerPC

Facts read from each project's repository on 2026-10-05.

## Contents

- [Xbox 360](#xbox-360)
- [PS3](#ps3)
- [Original Xbox](#original-xbox)
- [Not Verified](#not-verified)
- [Sources](#sources)

## Xbox 360

The Xbox 360 matching project is dc3-decomp (`rjkiv/dc3-decomp`), a decompilation of Dance Central 3
(build Sep 16 2012). It uses ninja, runs under wine-crossover on macOS, uses objdiff, and is tracked
on decomp.dev.

- The decomp-toolkit fork for Xbox 360 executables (xex) is `ChimpsAtSea/jeff`, last pushed
  2026-01-15. Its template is `rjkiv/jeff-template` (`jeff-template`).
- decomp.me has the platform `xbox360` with the compilers `msvc_ppc_14.00.2110` and
  `msvc_ppc_16.00.11886.00`.
- objdiff supports PowerPC for the Xbox 360.
- The research did not read dc3-decomp's compiler or flag setup. Read the project's own build files
  for the compiler version and flags before the first build.
- hedge-dev/XenonRecomp is a static recompiler, not a matching decompilation. Use
  `$recompile-console-binary` for it.

## PS3

No PS3 matching project and no decomp.me PS3 platform were found. This does not prove that none
exist. objdiff lists PS3 under PowerPC support, and the research did not look at PS3 compilers (GCC
or SNC) or their codegen.

## Original Xbox

The original Xbox has no true matching project, because halo-re does not match bytes. See
[`msvc-x86.md`](msvc-x86.md).

## Not Verified

- Whether other Xbox 360 or PS3 matching projects exist.
- Xbox 360 and PS3 codegen quirks, and the MSVC PPC flags that dc3-decomp uses.
- The decomp.me live compiler list for `xbox360`, beyond the two ids above.

## Sources

- dc3-decomp: <https://github.com/rjkiv/dc3-decomp>
- jeff: <https://github.com/ChimpsAtSea/jeff>
- jeff-template: <https://github.com/rjkiv/jeff-template>
- XenonRecomp: <https://github.com/hedge-dev/XenonRecomp>
- halo-re/halo: <https://github.com/halo-re/halo>
- objdiff: <https://github.com/encounter/objdiff>
- decomp.me compilers: <https://github.com/decompme/decomp.me> (`cromper/cromper/compilers.py`)
