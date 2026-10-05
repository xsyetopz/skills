# Inputs and Comparison

Commands are POSIX sh; on Windows run them in Git Bash or WSL, or use the PowerShell forms given.
`rg` (ripgrep) is required for the source check.

## Contents

- [Pin the Inputs](#pin-the-inputs)
- [Keep the Reference out of Git](#keep-the-reference-out-of-git)
- [Compare Fully and Fail Closed](#compare-fully-and-fail-closed)
- [Fail-Closed Rules](#fail-closed-rules)
- [Relocations and the Symbol Manifest](#relocations-and-the-symbol-manifest)
- [Negative Controls](#negative-controls)
- [Count Only Reconstructed Code](#count-only-reconstructed-code)
- [Prior Art](#prior-art)
- [Sources](#sources)

## Pin the Inputs

A match is a statement about four inputs: the reference binary, the compiler, the linker (or
assembler and archiver), and the flags. Change any one and the same source produces different bytes,
so a match that does not name all four cannot be reproduced.

Record, before the first function:

- the SHA-256 of the reference binary, and of each extracted section or object if the project
  compares at that level;
- the path, version string, and SHA-256 of each toolchain executable, and of any runtime library or
  header set the build links against;
- every compiler and linker flag, in order, from the build file rather than from memory; a flag that
  controls frame pointers, inlining, alignment, or the optimization level changes every function;
- the build command that produces the linked output.

```sh
shasum -a 256 orig/GAME.EXE tools/cc/bin/cc.exe tools/cc/bin/link.exe
```

`sha256sum` prints the same digest on Linux; PowerShell `Get-FileHash` prints SHA-256 by default.
Store the digests in the project contract file, and have the build refuse to run when the reference
digest differs: a different release or a patched copy of the binary makes every later result
meaningless.

Wrong: "built with the vendor compiler, `-O2`". Which build of the compiler, which service pack,
which other flags? Nobody can tell whether a later mismatch comes from the source or from the
toolchain.

Verify: rebuild from a clean checkout with only the recorded inputs and compare the output digest
with the recorded one.

## Keep the Reference out of Git

The reference binary, extracted sections, and disassembly or decompiler dumps stay in one ignored
directory, for example `orig/` or `reference/`. They are usually someone else's copyrighted work,
they are large, and a tracked copy makes it easy for a build step to copy bytes instead of compiling
them. The repository holds the digest and the instructions to obtain the file.

```sh
git check-ignore -v orig/GAME.EXE     # prints the matching ignore rule
git ls-files orig/                    # prints nothing when nothing is tracked
```

## Compare Fully and Fail Closed

Compare the whole function body at the exact address layout the original has, together with its
relocations. Two granularities work:

- Per object or per function: compile each unit to a relocatable object and compare it with the
  matching slice of the reference, symbol by symbol, including each relocation's type, offset, and
  target. This is what objdiff does; it gives a per-function diff while you iterate.
- Whole image: link the full binary and compare it byte for byte with the reference. This is the
  final proof, because it also checks layout, padding, section order, and data.

For a whole-image compare, `cmp` is enough and already fails closed:

```sh
cmp orig/GAME.EXE build/GAME.EXE   # exit 0 identical, 1 different
cmp -l orig/GAME.EXE build/GAME.EXE | head   # 1-based offsets, octal bytes
# PowerShell: fc.exe /b orig\GAME.EXE build\GAME.EXE
```

`cmp` exits 1 on the first difference and reports `EOF on <file>` when one file is a prefix of the
other, so a short build does not pass.

## Fail-Closed Rules

Each of these lets a verifier report a match that is not one:

- **Truncation.** Comparing `min(len(reference), len(candidate))` bytes passes a candidate that is a
  prefix of the target, or a target that is a prefix of the candidate. Check the sizes first; a size
  difference is a mismatch.
- **Masking.** Replacing call targets, branch displacements, absolute addresses, or immediates with
  wildcards passes code that calls the wrong function, jumps to the wrong block, or loads the wrong
  constant. Relocated fields are compared through the symbol manifest instead; nothing is masked.
- **Skipping.** A function missing from the build, a section that cannot be read, or a tool that
  exits non-zero is a failure, not "not checked".
- **Stale input.** Comparing an old build output after editing the source. Rebuild inside the
  verifier or check the output's timestamp and digest against the build.

Wrong:

```python
n = min(len(ref), len(cand))
ok = all(r == c or r == 0xE8 for r, c in zip(ref[:n], cand[:n]))
```

Right: sizes equal, every byte equal, relocations equal after resolving their targets through the
manifest.

## Relocations and the Symbol Manifest

In a relocatable object, a call or an address load is a placeholder plus a relocation that names a
symbol. To compare it with the reference, resolve the reference's address to a symbol name. Do that
through a reviewed symbol manifest, a checked-in file that maps each reference address to a name
(and for data, a size), written and reviewed by a person.

- A relocation whose target has no manifest entry fails the compare. Do not fall back to "any symbol
  at a nearby address" or to the name the candidate happens to use; that turns a wrong call into a
  match.
- Record the manifest's digest with the build inputs so a later edit to the manifest is visible.
- Two names for one address, or one name for two addresses, is a manifest defect; fix the manifest
  before comparing.

## Negative Controls

A negative control is a known-wrong variant that the verifier must reject. Run at least one per
fault class the verifier claims to catch, after writing the verifier and after every change to it:

| Variant | Catches |
| --- | --- |
| Delete the last instruction of a matched function | Truncation |
| Point one call at a different function | Masked call targets |
| Change one immediate constant by one | Masked immediates |
| Swap two independent stores | Order-insensitive compare |
| Remove one symbol from the manifest | Unknown-symbol fallback |

Each control must make the verifier exit non-zero. Record the variant and the exit status in the
project notes. Build the variants in a disposable copy or a scratch branch, never in the matching
tree.

## Count Only Reconstructed Code

Progress is the share of the reference that compiles from reconstructed source and matches. These
produce matching bytes without being decompiled, so they never count:

- inline byte emission such as MSVC `_emit` or `.byte` directives;
- included assembly: `incbin`, splat's `INCLUDE_ASM` and `INCLUDE_RODATA` (GCC) or `GLOBAL_ASM`
  (IDO) for functions not matched yet;
- instruction bytes copied from the reference in any form;
- library or runtime code linked from a dependency rather than written in the project.

A whole-image match with half the functions still in included assembly is a correct build, and 50%
decompiled. Report both numbers.

Give each function an `origin` in the progress data (`reconstructed`, `included-asm`,
`emitted-bytes`, `copied-bytes`, `dependency`) and count matched bytes only where the origin is
`reconstructed` and the status is `matched`. Measure bytes, not functions: a hundred small leaf
functions are not a hundred times a large one.

Verify: `rg -n '_emit|\.byte|incbin|INCLUDE_(ASM|RODATA)|GLOBAL_ASM' src/` and check that every hit
belongs to a function whose origin is not `reconstructed`.

## Prior Art

- [objdiff][objdiff] (Apache-2.0) compares relocatable `.o` files, a target and a base, configured
  through `objdiff.json`. It diffs functions and data and demangles symbol names.
- [decomp.me][decompme] (MIT) is a collaborative site where each "scratch" holds one function's
  target assembly, a compiler preset, and candidate source; creating a scratch publishes the target
  assembly.
- [splat][splat] splits a binary into assembly and data files. Functions not matched yet live in
  `asm/nonmatchings/<file>/<function>.s` and are included from C with `INCLUDE_ASM` or
  `INCLUDE_RODATA` (GCC) or `GLOBAL_ASM` (IDO) until source replaces them.

## Sources

- objdiff: <https://github.com/encounter/objdiff>
- decomp.me: <https://github.com/decompme/decomp.me>
- splat general workflow: <https://github.com/ethteck/splat/wiki/General-Workflow>
- MSVC `_emit` pseudoinstruction: [Microsoft Learn][emit]
- `cmp` behavior on a prefix and on a difference: local run, macOS `cmp` (BSD), 2026-09-30.

[objdiff]: https://github.com/encounter/objdiff
[decompme]: https://decomp.me/
[splat]: https://github.com/ethteck/splat/wiki/General-Workflow
[emit]: https://learn.microsoft.com/en-us/cpp/assembler/inline/emit-pseudoinstruction
