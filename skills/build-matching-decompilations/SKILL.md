---
name: build-matching-decompilations
description: >-
  Rewrites decompiled functions as source that compiles back to identical
  bytes, with compiler flags, objdiff, and matching workflows. Use for
  matching decompilation projects.
---

# Build Matching Decompilations

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
- Check ABI boundaries (exports, imports, callbacks, virtual calls) for calling convention, struct
  offsets, symbol decoration, and vtable slot order. A matching body does not show that callers
  still work. Steer bodies, not signatures.
- Accept only with fresh evidence: rebuild from clean, recompute hashes, and run the full compare
  plus the negative controls. Do not reuse hashes from an earlier run.

## Workflow

1. Build objects with the pinned toolchain. Put the reference object (extracted with splat or
   similar) at each unit's `target_path` and your build at its `base_path` in `objdiff.json`, one
   unit per source file.
1. Diff one function. The [objdiff][objdiff] CLI takes the project, the unit, and a symbol, for
   example `objdiff-cli diff -p . -u main/player Player_Update`. Confirm flags with
   `objdiff-cli diff --help`, since they belong to the installed version. objdiff diffs relocations
   too, so do not turn on options that ignore them.
1. Name the first difference (swapped register, load in a different place, inverted branch,
   different stack offset). Read [compiler steering](references/compiler-steering.md), make one
   change that addresses that kind of difference, rebuild, and diff again.
1. Revert a change that made the diff worse, unless it fixed an earlier difference, and log the
   revert.
1. Finish with the whole image: `cmp orig/GAME.EXE build/GAME.EXE`. It exits 0 when identical and 1
   otherwise, and it reports `EOF` when one file is a prefix of the other, so a short build does not
   pass. (PowerShell: `fc.exe /b orig\GAME.EXE build\GAME.EXE`, which exits 1 on any byte or length
   difference and lists the offsets.)

For the meaning of a function, its calls, and its types, use `$reverse-engineer-binaries`. This
skill starts when the behavior is understood and the bytes must match. Use `$write-behavior-tests`
for boundaries you rewrite, because behavior tests do not prove a match and a match does not replace
them.

## References

- Read [`references/inputs-and-comparison.md`](references/inputs-and-comparison.md) when writing or
  reviewing a verifier, setting up the symbol manifest, choosing negative controls, or counting
  progress.
- Read [`references/compiler-steering.md`](references/compiler-steering.md) when a function is close
  but registers, load order, branch shape, or stack layout differ from the target.

[objdiff]: https://github.com/encounter/objdiff
