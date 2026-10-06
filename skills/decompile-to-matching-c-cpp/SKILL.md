---
name: decompile-to-matching-c-cpp
description: >-
  Rewrites disassembled functions as C or C++ that compiles byte-identical,
  with splat, objdiff, m2c, decomp-permuter, PsyQ, IDO, MWCC, and MSVC.
  Use when a function is a few instructions off, registers swap,
  progress numbers look wrong, or a matching decomp is set up.
  Not for static recompilation.
---

# Decompile to Matching C or C++

A matching decompilation is source that the original compiler, linker, and flags turn into the same
bytes as a reference binary. Functional equivalence is not enough. Without this skill, agents accept
a compare that cannot fail, count included assembly as progress, and fix original bugs.

## Rules

- Pin the inputs before the first function: the reference binary's SHA-256
  (`shasum -a 256 orig/GAME.EXE`; PowerShell `Get-FileHash orig/GAME.EXE`), the path, version, and
  hash of each compiler and linker executable, and every flag in build-file order. A different input
  gives different bytes, so an unpinned match cannot be reproduced.
- Keep the reference binary, extracted sections, and disassembly dumps out of Git
  (`git check-ignore -v orig/GAME.EXE`). Commit the hash instead. They are copyrighted, and a
  committed copy lets a build copy bytes instead of compiling them.
- Compare the whole function at its exact layout, relocations included. A compare over `min(len)`
  bytes passes a truncated function, and one that masks calls, branches, or immediates passes the
  wrong callee or constant. Check sizes first, and treat a missing file, unreadable section, size
  difference, or tool error as a failure, not a skip.
- Resolve every relocation through a reviewed symbol manifest mapping reference addresses to names.
  Fail on an unknown symbol. Guessing a name from a nearby address turns a wrong call into a match.
- Run a negative control before trusting any verifier and after changing it: delete the last
  instruction, retarget one call, or change one immediate in a disposable copy, and confirm a
  non-zero exit. A verifier that never failed has not shown that it can.
- Count as matched only code compiled from reconstructed source. `_emit`, `.byte`, `incbin`,
  `INCLUDE_ASM`, `GLOBAL_ASM`, copied bytes, and linked dependencies give identical bytes without
  decompiling. A byte-identical image that is half included assembly is a correct build and 50%
  decompiled, so report both. Measure bytes, not functions. Check with
  `rg -n '_emit|\.byte|incbin|INCLUDE_(ASM|RODATA)|GLOBAL_ASM' src/`.
- Keep original behavior exactly, including bugs, odd constants, and undefined behavior the compiler
  resolved one way. Put fixes in a separate non-matching build or patch layer. If only a behavior
  change matches, the reading of the target is wrong, so go back to the disassembly.
- Change one thing per attempt. Log the change, the source and toolchain hashes, the result, and the
  differing byte count, so a regression traces to one edit. Log failed attempts too.
- Review every permuter result before keeping it. decomp-permuter scores any change that lowers the
  diff, including no-op statements that fix register allocation by accident. Keep a change only if
  it reads like code a person wrote, and mark one you keep anyway with the project's fakematch
  comment, because it can break when a neighboring field or function changes.
- Ask before creating a decomp.me scratch. Scratches are public, so the target assembly and your
  source are published.
- Keep a near-match under the project's own guard (`#ifdef NON_MATCHING`, `NONMATCH`, or similar)
  with the included assembly as the default build, and a comment naming the remaining difference.
  Read the guard name from the project's headers, because each project picks its own.
- Check ABI boundaries (exports, imports, callbacks, virtual calls) for calling convention, struct
  offsets, symbol decoration, and vtable slot order. A matching body does not show that callers
  still work. Steer bodies, not signatures.
- Accept only with fresh evidence: rebuild from clean, recompute hashes, and run the full compare
  plus the negative controls. Do not reuse hashes from an earlier run.

## Workflow

1. Split the binary. splat handles N64, PSX, PS2, and PSP (`splat split <config>.yaml`, with
   `platform`, `compiler`, `basename`, and `target_path` set). decomp-toolkit (`dtk`) handles
   GameCube and Wii. Each function not matched yet lands in a `nonmatchings` file that C includes
   with `INCLUDE_ASM` (GCC) or `GLOBAL_ASM` (IDO, through asm-processor).
1. Draft one function with m2c: `m2c.py -t mips-ido-c --context ctx.h -f Func asm/Func.s`. Treat the
   output as a starting point, since its loops are often not the original shape.
1. Diff one function with objdiff: `objdiff-cli diff -p . -u main/player Player_Update`. The
   reference object goes at the unit's `target_path` and your build at its `base_path` in
   `objdiff.json`. Do not turn on options that ignore relocations.
1. Name the first difference (swapped register, load in a different place, inverted branch,
   different stack offset). Read [compiler steering](references/compiler-steering.md), make one
   change for that kind of difference, rebuild, and diff again. Revert a change that made the diff
   worse, unless it fixed an earlier difference, and log the revert.
1. When only register allocation differs, try decomp-permuter: `./import.py src/x.c asm/Func.s`,
   then `./permuter.py <dir>/ -j 8` on the directory it created. Fix reordering and logic by hand.
1. Finish with the whole image: `cmp orig/GAME.EXE build/GAME.EXE`. It exits 0 when identical and 1
   otherwise, and it reports `EOF` when one file is a prefix of the other, so a short build does not
   pass. (PowerShell: `fc.exe /b orig\GAME.EXE build\GAME.EXE`, which exits 1 on any byte or length
   difference and lists the offsets.)

For the meaning of a function, its calls, and its types, use `$reverse-engineer-binary`. This skill
starts when the behavior is understood and the bytes must match. To run a console game natively
without matching bytes, use `$recompile-console-binary`. Use `$write-behavior-tests` for boundaries
you rewrite, because behavior tests do not prove a match and a match does not replace them.

## References

- Read [`references/tools.md`](references/tools.md) for splat, objdiff, m2c, decomp-permuter,
  asm-differ, and decomp.me options, config keys, and exit codes.
- Read [`references/inputs-and-comparison.md`](references/inputs-and-comparison.md) when writing or
  reviewing a verifier, setting up the symbol manifest, choosing negative controls, or counting
  progress.
- Read [`references/compiler-steering.md`](references/compiler-steering.md) when a function is close
  but registers, load order, branch shape, or stack layout differ from the target.
- Read the compiler reference for the target before the first build:

  | Target | Reference |
  | --- | --- |
  | PS1 PsyQ, PS2 ee-gcc, MWCC PS2 | [`references/psyq-ee-gcc-mwcc-ps2.md`][psx] |
  | N64 IDO 5.3/7.1, KMC gcc | [`references/ido-kmc.md`](references/ido-kmc.md) |
  | GameCube and Wii MWCC | [`references/mwcc-gc-wii.md`](references/mwcc-gc-wii.md) |
  | Win32 and Xbox MSVC x86 | [`references/msvc-x86.md`](references/msvc-x86.md) |
  | Xbox 360 Xenon, PS3 Cell | [`references/xenon-cell.md`](references/xenon-cell.md) |

[psx]: references/psyq-ee-gcc-mwcc-ps2.md
