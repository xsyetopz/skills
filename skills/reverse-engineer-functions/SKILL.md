---
name: reverse-engineer-functions
description: >-
  Reverses a binary function from Ghidra, IDA, Binary Ninja, or radare2
  output, recovering call conventions, structs, vtables, and names. Use to
  decode a function. Not for byte-matching or DRM bypass.
---

# Reverse Engineer Functions

Explain what one function in a compiled binary does from evidence that
the user can check. The method is the same in every tool; only the views
differ (disassembly, decompiler output, xrefs, data types).

## Scope

Analyze only binaries that the user may analyze: their own programs,
interoperability, preservation, security research they are allowed to do,
and matching-decompilation projects. Refuse, and say why, when the goal is
to bypass a licence check, DRM, or anti-cheat, or to analyze the coding
agent's own binary. The method is the same in every case; the purpose
decides.

Route adjacent work:

| Need | Use |
| --- | --- |
| Run Ghidra headless, export, decompile, list xrefs from an agent | `$analyze-binaries-with-ghidra` |
| Write source that compiles to the same bytes as the binary | `$build-matching-decompilations` |
| Find why a program with source crashes, hangs, or regresses | `$debug-software-failures` |

## Workflow

1. Confirm the scope above. Record the binary (file name and a hash if the
   user has one), architecture, format, image base, and the tool and
   version in use.
1. Fix the target: one function, by address. Record its entry address and
   the name the tool shows. If the user gave a runtime address, convert it
   to the tool's address space first (runtime address minus load base plus
   image base).
1. Read the disassembly before the decompiler output. The decompiler is a
   reconstruction; the instructions are the evidence.
1. Settle the [calling convention](#calling-conventions): which registers
   and stack slots carry arguments, the return value, and who removes stack
   arguments. Fix the prototype in the tool only after this step.
1. Strip [compiler idioms](#compiler-idioms): stack cookies, exception
   frames, inlined copies, jump tables, tail calls. What remains is the
   function's own logic.
1. Recover [types](#types-vtables-and-rtti) from accesses: field offsets,
   sizes, and vtable slots. Record the address of each access that
   supports a field.
1. Follow xrefs in both directions: callers show how arguments are built;
   callees show what the function relies on. Check each type against every
   xref, not just one.
1. Apply the [stop rule](#stop-rule) at the first callee or data item whose
   meaning the answer depends on and that is not yet resolved.
1. [Report](#report) the answer, evidence, types, and open questions.

## Evidence

Every claim about behavior cites the instruction or decompiler line that
shows it, by address. Anything else is labeled as inference.

- Treat auto-generated names and types (`FUN_...`, `sub_...`, `param_1`,
  `undefined4`, `int` guessed for a pointer) as hypotheses. The tool made
  them up from patterns; it did not read them from the binary.
- A symbol, export name, debug record, RTTI name, or string in the binary
  is evidence. Cite where it was found.
- When the decompiler and the disassembly disagree, the disassembly wins.
  Note the disagreement; it often marks a wrong prototype or type.
- One call site shows one use: write "at `0x...` it is called with ...",
  not "it always ...".

Claim format and examples:
[evidence and report](references/evidence-and-report.md).

## Calling conventions

Decide from the code, not from the tool's default. Check three things:

1. Which registers are read before they are written at the entry (they are
   arguments or preserved registers).
1. How callers set up the call: pushes, register loads, and stack space
   reserved before the `call`.
1. How the function returns: `ret` with an immediate means the callee
   removes that many bytes of stack arguments; plain `ret` means the caller
   does (or there were none).

| Platform | First arguments | Return | Stack cleanup |
| --- | --- | --- | --- |
| x86 `__cdecl` | stack, right to left | `EAX` (`EDX:EAX` for 8 bytes) | caller |
| x86 `__stdcall` | stack, right to left | `EAX` | callee (`ret N`) |
| x86 `__fastcall` (MSVC) | `ECX`, `EDX`, then stack | `EAX` | callee |
| x86 `__thiscall` (MSVC) | `this` in `ECX`, rest on stack | `EAX` | callee |
| SysV x86-64 | `RDI`, `RSI`, `RDX`, `RCX`, `R8`, `R9`; `XMM0`-`XMM7` | `RAX`/`RDX`, `XMM0`/`XMM1` | caller |
| Win64 | `RCX`, `RDX`, `R8`, `R9` or `XMM0`-`XMM3` by position | `RAX` or `XMM0` | caller |
| AArch64 AAPCS64 | `x0`-`x7`; `v0`-`v7` | `x0`/`v0`; `x8` holds the result address | caller |

Large return values go through a hidden pointer on every platform; that
pointer shifts the visible arguments by one. Details, preserved registers,
varargs, and sources:
[calling conventions](references/calling-conventions.md).

## Compiler idioms

Recognize these and name them in the report instead of describing their
instructions as the function's logic:

- Stack cookie: a value loaded at entry, stored near the return address,
  and checked by a helper call before return (MSVC `/GS`, GCC
  `-fstack-protector`).
- Exception frames: Win64 uses tables (`.pdata`, `UNWIND_INFO`), not code.
- Inlined library calls: a byte loop or wide copy where the source had
  `memcpy` or `strlen`.
- Switch jump tables: an index bounds check, then an indirect jump through
  a table of addresses.
- Tail calls: a `jmp` to another function where a `call` and `ret` would
  be.
- Reordered and split blocks: cold paths moved to the end or to another
  section.

Shapes vary by compiler, version, and flags. When a shape is uncertain,
compile a small known sample with the suspected compiler and flags and
compare. Details: [compiler idioms](references/compiler-idioms.md).

## Types, vtables, and RTTI

- Fields: each `[reg+offset]` access through the same base gives one
  field; the access width gives its size; the instruction (signed or
  unsigned extend, float load, pointer use) gives its kind.
- Size: an allocation call with a constant size, followed by a constructor
  call on the result, gives the size of the object built there.
- Consistency: a field is confirmed only when every xref that touches it
  agrees on its offset, width, and kind. List conflicts; do not average
  them.
- Vtables: a store of a table address into offset 0 of a new object is a
  vptr. The table entries are virtual methods in slot order.
- RTTI: Itanium (GCC, Clang) emits `_ZTV`, `_ZTI`, and `_ZTS` symbols and
  typeinfo before the function pointers; MSVC puts a pointer to an
  `RTTICompleteObjectLocator` at `vftable[-1]`. A class name found there is
  "seen" evidence.

Field table format, layouts, and sources:
[types, vtables, and RTTI](references/types-vtables-rtti.md).

## Naming

Give every name you introduce a confidence level, and keep it with the
name in the report:

| Level | Meaning | Example evidence |
| --- | --- | --- |
| seen | The name is in the binary | symbol, export, RTTI name, log string naming the function |
| inferred | The use implies the name | only called with a file path and returns a handle |
| guess | Plausible, not supported | shape resembles a known library routine |

Mark a guessed name in the tool (for example, a `guess_` prefix or a
comment), because renames in a shared project change what others read.

## Stop rule

Stop at the first unresolved dependency that the answer depends on: a
callee whose effect decides the result, an indirect call with an unknown
target, a global whose writer is not found, or a type that the xrefs do
not agree on. Do not guess through it. List it with its address and what
would resolve it, then either analyze it next (when the user asked for
depth) or report.

## Report

Use this order: the answer (what the function does in one or two
sentences, its address, and the name confidence); the prototype with
evidence for each argument, the return, and cleanup; behavior claims with
addresses; types as field tables with evidence addresses; open questions,
each with its address and the check that would resolve it.

Template and a worked example:
[evidence and report](references/evidence-and-report.md#report-template).

## Rules

- Quote an address with every claim.
- Label decompiler output as the tool's reconstruction, not source.
- Keep auto-names visible until evidence replaces them.
- Rename or retype in a shared project only when the user asks.

## References

- [Calling conventions](references/calling-conventions.md): x86, Win64,
  SysV x86-64, and AAPCS64 registers, returns, preserved registers,
  varargs, and sources.
- [Compiler idioms](references/compiler-idioms.md): stack cookies,
  exception tables, inlined calls, jump tables, tail calls, block
  reordering, and sources.
- [Types, vtables, and RTTI](references/types-vtables-rtti.md): field
  recovery, Itanium vtables and typeinfo, MSVC RTTI, and sources.
- [Evidence and report](references/evidence-and-report.md): claim format,
  name confidence, stop rule, and the report template.

## Completion evidence

The report names the binary, architecture, and tool; the function address;
the calling convention with its evidence; each behavior claim with an
address; each recovered field with its evidence address; a confidence
level for each introduced name; and every open question with its address.
