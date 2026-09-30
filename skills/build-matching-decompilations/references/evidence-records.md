# Evidence records

## Contents

- [Why keep records](#why-keep-records)
- [iterations.json](#iterationsjson)
- [acceptance.json](#acceptancejson)
- [ABI checks at boundaries](#abi-checks-at-boundaries)
- [Checking the records](#checking-the-records)
- [Sources](#sources)

## Why keep records

A failed attempt is evidence: it shows which source shapes the pinned
compiler does not accept, so nobody repeats them, and a regression can be
traced to the change that caused it. An acceptance claim without fresh
hashes cannot be told apart from one copied from an older build. Keep both
records in a tracked directory such as `evidence/`, next to a short
human-readable log if the project wants one.

The schemas below are the ones `scripts/check_match_evidence.py` reads.
Add fields when the project needs them; the checker ignores unknown
fields.

## iterations.json

One entry per build-and-compare attempt, appended in order, never
rewritten.

```json
{
  "schema_version": 1,
  "attempts": [
    {
      "id": 1,
      "function": "Player_Update",
      "source_sha256": "<64 hex digits of src/player.c>",
      "toolchain_sha256": "<64 hex digits of the compiler executable>",
      "change": "first translation from the decompiler output",
      "result": "nonmatching",
      "differing_bytes": 6,
      "diff_summary": "ESI and EDI swapped for p and count"
    },
    {
      "id": 2,
      "function": "Player_Update",
      "source_sha256": "<64 hex digits>",
      "toolchain_sha256": "<64 hex digits>",
      "change": "declare count before p",
      "result": "match",
      "differing_bytes": 0,
      "diff_summary": "identical, relocations resolved"
    }
  ]
}
```

| Field | Meaning |
| --- | --- |
| `id` | Integer, strictly increasing across the file. |
| `function` | Symbol name from the symbol manifest. |
| `source_sha256` | SHA-256 of the source file compiled in this attempt. |
| `toolchain_sha256` | SHA-256 of the compiler executable, or of a toolchain manifest that lists every tool hash. |
| `change` | The one change made since the previous attempt. |
| `result` | `match`, `nonmatching`, or `build-failed`. |
| `differing_bytes` | `0` for `match`, a positive count for `nonmatching`, `null` for `build-failed`. |
| `diff_summary` | The first or main difference, in words. |

The source hash identifies the exact text tried; keep the text too, in
version control history or as a saved copy under `evidence/attempts/`,
when a failed shape is worth showing later.

## acceptance.json

The current claim, rewritten on each acceptance run from fresh data.
Paths are relative to the project root.

```json
{
  "schema_version": 1,
  "reference": {"path": "orig/GAME.EXE", "sha256": "<64 hex>"},
  "toolchain": [
    {
      "role": "compiler",
      "path": "tools/cc/bin/cc.exe",
      "sha256": "<64 hex>",
      "version": "<exact version string the tool prints>",
      "flags": ["<every flag, in build order>"]
    },
    {
      "role": "linker",
      "path": "tools/cc/bin/link.exe",
      "sha256": "<64 hex>",
      "version": "<exact version string>",
      "flags": []
    }
  ],
  "sources": [{"path": "src/player.c", "sha256": "<64 hex>"}],
  "build": {
    "command": "just build",
    "output": {"path": "build/GAME.EXE", "sha256": "<64 hex>"}
  },
  "compare": {
    "scope": "full-function",
    "masks": [],
    "unresolved_relocations": 0,
    "symbol_manifest": {"path": "symbols.txt", "sha256": "<64 hex>"}
  },
  "functions": [
    {
      "symbol": "Player_Update",
      "address": "0x401000",
      "size": 212,
      "origin": "reconstructed",
      "status": "matched"
    },
    {
      "symbol": "Crt_Start",
      "address": "0x4010e0",
      "size": 96,
      "origin": "dependency",
      "status": "nonmatching"
    }
  ],
  "coverage": {"matched_bytes": 212, "total_bytes": 308},
  "negative_controls": [
    {"variant": "last instruction of Player_Update removed",
     "verifier_exit": 1},
    {"variant": "call in Player_Update pointed at Player_Draw",
     "verifier_exit": 1}
  ],
  "abi_checks": [
    {"boundary": "Player_Update", "convention": "thiscall",
     "result": "pass"}
  ]
}
```

Rules the checker enforces:

- Every `path` exists under the root and its recomputed SHA-256 equals
  the recorded one. A missing file or an old hash is a defect, so the
  record must be written after the final build.
- The reference path is not tracked by Git.
- The toolchain has a `compiler` entry, and every entry has a `version`
  and a `flags` list.
- `compare.scope` is `full-function` or `full-image`, `compare.masks` is
  empty, and `compare.unresolved_relocations` is `0`.
- `origin` is one of `reconstructed`, `included-asm`, `emitted-bytes`,
  `copied-bytes`, `dependency`; only `reconstructed` may be `matched`.
- `coverage` equals the sum of `size` over reconstructed matched
  functions, and over all listed functions.
- At least one negative control, each with a non-zero `verifier_exit`.
- At least one ABI check, each with `result` `pass`.
- With `--iterations`, every function accepted as `matched` has a latest
  attempt whose result is `match`.

Acceptance run, in order: clean the build directory, build with the
pinned toolchain, run the full compare, run each negative control in a
disposable copy, run the ABI checks, recompute every hash, write
`acceptance.json`, run the checker.

## ABI checks at boundaries

Where reconstructed code meets code it does not own (exports, imports,
callbacks, virtual calls, the runtime), a match inside the function is not
enough: the boundary must follow the original calling convention and data
layout, or callers break when a boundary function is rebuilt or replaced.

Check at each boundary:

- calling convention: which registers and stack slots carry arguments and
  `this`, who removes arguments from the stack, which registers the callee
  must preserve, where the return value goes;
- structure layout: field offsets, sizes, and alignment of every type
  passed across, compared with the offsets the target uses;
- symbol names and decoration for exports and imports;
- for C++, vtable slot order and the class layout the target assumes.

Record each boundary with its convention and the result. Where a
boundary can run, add behavior tests with `$write-behavior-tests` in the
consuming project; a byte match of the function body does not exercise
the caller's side.

## Checking the records

```sh
python3 scripts/check_match_evidence.py \
  --acceptance evidence/acceptance.json \
  --iterations evidence/iterations.json --root .
```

Exit 0 clean, 1 defects (one `DEFECT` line each), 2 unreadable input.
`--json` prints `defects`, `matched_bytes`, `total_bytes`, and `attempts`.
The checker validates the records and recomputes hashes; it does not
compare bytes. The compare and the negative controls stay the project's
own verifier.

## Sources

- System V x86-64 psABI: <https://gitlab.com/x86-psABIs/x86-64-ABI>
- Microsoft x64 calling convention:
  <https://learn.microsoft.com/en-us/cpp/build/x64-calling-convention>
- Microsoft x86 argument passing and naming conventions (`__cdecl`,
  `__stdcall`, `__fastcall`, `__thiscall`): [Microsoft Learn][ms-x86]
- AAPCS64:
  <https://github.com/ARM-software/abi-aa/blob/main/aapcs64/aapcs64.rst>
- Itanium C++ ABI, virtual tables:
  <https://itanium-cxx-abi.github.io/cxx-abi/abi.html#vtable>

[ms-x86]: https://learn.microsoft.com/en-us/cpp/cpp/argument-passing-and-naming-conventions
