---
name: build-matching-decompilations
description: >-
  Builds and verifies matching decompilations, source that compiles to the
  same bytes as a reference binary: pinned reference hash and toolchain,
  fail-closed full-function compares with relocations, honest coverage,
  negative controls, compiler steering, and an attempt log with
  machine-readable acceptance evidence. Use when a project must be
  "matching", "byte-identical", or "match the original", or pins a reference
  hash. Not for understanding what a function does, or for behavior tests.
---

# Build Matching Decompilations

A matching decompilation is source that the original compiler, linker, and
flags turn into the same bytes as a reference binary. Byte identity is the
whole contract. Functional equivalence is not enough: code that behaves the
same but compiles differently does not match, and changing original
behavior to fix or improve it breaks the contract. Every claim of a match
must survive a comparison that cannot pass by accident.

Public prior art: [objdiff][objdiff] compares relocatable objects per
function and data section; [decomp.me][decompme] shares scratches of one
function against its target; [splat][splat] splits a binary and keeps
functions that do not match yet as included assembly.

## Workflow

1. Pin the inputs before writing code
   ([pinning](references/inputs-and-comparison.md#pin-the-inputs)): record
   the reference binary's SHA-256
   (`shasum -a 256 orig/GAME.EXE` or `sha256sum`), the exact compiler and
   linker builds with their hashes, and every flag. Keep the reference
   binary, extracted sections, and disassembly dumps in a Git-ignored
   directory; check with `git check-ignore -v orig/GAME.EXE`.
1. Build the comparison first and prove it can fail
   ([comparison][compare]):
   the full function body at its exact address layout, relocations
   resolved through a reviewed symbol manifest, no masks. Run a
   [negative control](references/inputs-and-comparison.md#negative-controls)
   before trusting a pass.
1. Pick one function. For its meaning, calls, and types, use
   `$reverse-engineer-functions`; this skill starts when the behavior is
   understood and the bytes must match.
1. Write the source, build with the pinned toolchain, and compare. On a
   difference, read the diff and change one thing at a time with the
   [steering techniques](references/compiler-steering.md). Keep behavior
   identical to the original, including its bugs.
1. Record every attempt you built and compared, failed or not, in
   `iterations.json`
   ([attempt log](references/evidence-records.md#iterationsjson)).
1. Count coverage from reconstructed source only
   ([coverage][coverage]).
1. Accept with fresh evidence
   ([acceptance](references/evidence-records.md#acceptancejson)): rebuild
   from clean, recompute every hash, run the full compare and the negative
   controls, check ABI boundaries
   ([ABI checks](references/evidence-records.md#abi-checks-at-boundaries)),
   write `acceptance.json`, then run the checker from the project root:

   ```sh
   python3 scripts/check_match_evidence.py --root . \
     --acceptance evidence/acceptance.json \
     --iterations evidence/iterations.json
   ```

## Route the task to a card

| Task or symptom | Card |
| --- | --- |
| New project, or hashes and flags not written down | [Pin the inputs](references/inputs-and-comparison.md#pin-the-inputs) |
| Reference binary or dumps staged or committed | [Keep references out of Git](references/inputs-and-comparison.md#keep-the-reference-out-of-git) |
| Writing or reviewing the verifier | [Compare fully](references/inputs-and-comparison.md#compare-fully-and-fail-closed) |
| Verifier compares `min(len)` bytes, masks calls or immediates | [Fail-closed rules](references/inputs-and-comparison.md#fail-closed-rules) |
| Relocations, call targets, symbol names | [Symbol manifest](references/inputs-and-comparison.md#relocations-and-the-symbol-manifest) |
| Verifier has never failed | [Negative controls](references/inputs-and-comparison.md#negative-controls) |
| Progress percentage, `INCLUDE_ASM`, `incbin`, `_emit` | [Coverage](references/inputs-and-comparison.md#count-only-reconstructed-code) |
| Registers swapped, operands reassociated | [Split expressions and temporaries](references/compiler-steering.md#split-expressions-add-temporaries) |
| Loads or stores in a different order | [Reorder reads and writes](references/compiler-steering.md#reorder-reads-and-writes) |
| Branch inverted, blocks in a different order, jump table | [Branch shape](references/compiler-steering.md#change-the-branch-shape) |
| Different stack layout or register choice | [Declarations](references/compiler-steering.md#declaration-order-and-types) |
| Temptation to "fix" an original bug | [Keep original behavior](references/compiler-steering.md#keep-original-behavior) |
| Logging an attempt | [iterations.json](references/evidence-records.md#iterationsjson) |
| Declaring a function or the project matched | [acceptance.json](references/evidence-records.md#acceptancejson) |
| Calling convention, struct layout, exports | [ABI checks](references/evidence-records.md#abi-checks-at-boundaries) |

## Rules

- Never commit the reference binary, its sections, or disassembly dumps.
  They are usually copyrighted and large, and a committed copy lets a
  build copy bytes instead of compiling them. Commit the hash instead.
- Compare the whole function at its exact layout, including relocations.
  A compare that stops at the shorter body passes a truncated function;
  a compare that masks addresses, calls, branches, or immediates passes
  code that calls the wrong function or uses the wrong constant.
- Resolve every relocation through a reviewed symbol manifest, and fail
  on an unknown symbol. Guessing a name from the target address makes
  a wrong call look right.
- Fail closed. A missing file, an unreadable section, a size difference,
  or a tool error is a failure, not a skip.
- Count as matched only code compiled from reconstructed source.
  `_emit`, inline byte directives, `incbin`, `INCLUDE_ASM`, copied
  instruction bytes, and linked dependencies produce identical bytes
  without any decompilation, so counting them inflates progress.
- Run a negative control for every new verifier and after every change to
  it: a known-wrong variant must fail. A verifier that has never failed
  has not shown it can.
- Keep original behavior exactly, including bugs, undefined behavior the
  compiler resolved one way, and odd constants. Put fixes in a separate,
  non-matching build or a patch layer, never in the matching source.
- Change one thing per attempt and log it with the source and toolchain
  hashes, so a later regression can be traced to a change.
- Accept only with fresh evidence: hashes recomputed after the final
  build, not copied from an earlier run.
- Behavior tests do not prove a match, and a match does not replace
  behavior tests at boundaries you rewrite; use `$write-behavior-tests`
  for those.

## Bundled tools

- `scripts/check_match_evidence.py [--acceptance FILE] [--iterations FILE]
  [--root DIR] [--json]`: stdlib only. Recomputes every SHA-256 in
  `acceptance.json` and fails on a stale hash or a missing file; fails when
  the reference binary is tracked by Git, when the compare is not full or
  masks anything, when relocations are unresolved, when coverage counts
  non-reconstructed code or disagrees with the function list, when a
  negative control passed, or when ABI checks are missing or failed.
  Checks `iterations.json` ids, hashes, and results, and that each
  function accepted as matched has a latest attempt of `match`. Exit 0
  clean, 1 defects, 2 bad input. It checks records; it does not compare
  bytes, so run the real compare first.

## References

- [Inputs and comparison](references/inputs-and-comparison.md): pinning,
  ignored reference directory, full fail-closed compare, symbol manifest,
  negative controls, coverage, objdiff, decomp.me, splat.
- [Compiler steering](references/compiler-steering.md): expression
  splitting, temporaries, statement order, branch shape, declarations,
  and keeping original behavior.
- [Evidence records](references/evidence-records.md): `iterations.json`
  and `acceptance.json` schemas, ABI boundary checks, sources.

## Completion evidence

The report states: the reference SHA-256 and the toolchain entries with
versions, hashes, and flags; the compare command and its exit status; each
negative control and the verifier's exit status on it; matched bytes over
total bytes with the origins excluded; the ABI checks run; the
`check_match_evidence.py` output; and every function still nonmatching
with its latest diff summary.

[compare]: references/inputs-and-comparison.md#compare-fully-and-fail-closed
[coverage]: references/inputs-and-comparison.md#count-only-reconstructed-code
[objdiff]: https://github.com/encounter/objdiff
[decompme]: https://decomp.me/
[splat]: https://github.com/ethteck/splat/wiki/General-Workflow
