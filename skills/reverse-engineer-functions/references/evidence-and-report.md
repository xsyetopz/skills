# Evidence and report

## Contents

- [Claim format](#claim-format)
- [Auto-names and auto-types](#auto-names-and-auto-types)
- [Name confidence](#name-confidence)
- [Stop rule](#stop-rule)
- [Report template](#report-template)
- [Worked example](#worked-example)

## Claim format

Write each claim so that the user can open the address and see it:

```text
<claim> - <address or decompiler line> - <seen | inferred>
```

Examples:

```text
Returns -1 when the file cannot be opened
  - 0x140011a52: test rax,rax / jz 0x140011b10; 0x140011b10: mov eax,-1
  - seen in code
Argument 2 is a length in bytes
  - 0x140011a60: passed as r8 to the copy loop at 0x140011a70
  - inferred
```

- "Seen" means the instructions or data at the address show the claim
  directly.
- "Inferred" means the claim follows from several observations. List them.
- A claim that has no address is a guess. Put it under open questions, or
  leave it out.

Decompiler lines count as evidence only with their address. When the
decompiler output and the disassembly disagree, cite the disassembly, and
note the disagreement: it often means a wrong prototype, a wrong type, or a
missed jump table.

## Auto-names and auto-types

Tool-generated names (`FUN_00401a30`, `sub_401A30`, `param_1`,
`local_18`, `DAT_...`) and types (`undefined4`, `int` for a pointer,
`void *` for everything) are placeholders. Keep them visible in the report
until evidence replaces them, and state what replaced each one.

Library signature matches (for example, a tool's identification of a
statically linked C runtime function) are inferred evidence, not seen.
Cite the tool and the match.

## Name confidence

| Level | Use when | Cite |
| --- | --- | --- |
| seen | A symbol, export, import, debug record, RTTI name, or a string that names the function or type exists in the binary | the address of the symbol or string |
| inferred | The name follows from use: arguments, return value, callers, callees | the addresses of those uses |
| guess | The name is plausible, but no evidence above supports it | nothing; say it is a guess |

A log or assert string such as `"Session::Open failed"` referenced from the
function is seen evidence for its name. When several functions reference
the same string, say which one it names and why; that link is inferred.

## Stop rule

Stop at the first dependency that the answer depends on and that is not
resolved. Typical cases:

- A callee whose effect decides the result, not yet analyzed.
- An indirect call or jump whose target is unknown.
- A global or field whose writer is not found.
- A type whose accesses conflict across xrefs.
- Code that the tool did not disassemble (data between functions, a
  missed jump table target).

For each one, record:

```text
0x1400129f0  call qword ptr [rax+0x18]   target unknown
  blocks: whether the buffer is freed on the error path
  resolve: find the constructor that sets the vptr for this object;
           slot 3 (0x18 / 8) of that vtable is the target
```

Do not guess through the dependency. When the user asked for depth,
analyze the dependency next and return. Otherwise, report with the open
question listed.

## Report template

```markdown
## Answer

<What the function does, in one or two sentences.> Function at
`<address>`, named `<name>` (<seen | inferred | guess>).

Binary: `<file>` (<hash if known>), <architecture>, <format>, image base
`<base>`. Tool: <tool and version>.

## Prototype

`<return type> <name>(<arguments>)`, <calling convention>.

- <argument>: <register or stack slot> - <evidence address>
- Return: <register> - <evidence address>
- Cleanup: <caller | callee (ret N)> - <evidence address>

## Evidence

- <claim> - `<address>` - <seen | inferred>
- Compiler idioms left out of the logic: <stack cookie at ...,
  inlined memcpy at ...>

## Types

<Field tables with evidence addresses and confirmation state.>

## Open questions

- `<address>`: <what is unknown> - blocks <which part of the answer> -
  resolve by <check>
```

Keep sections that have nothing to report, with "none", so that the user
can see they were checked.

## Worked example

A short example on x86 (32-bit):

```text
0x00401a30  push ebp
0x00401a31  mov  ebp, esp
0x00401a33  mov  eax, [ebp+8]
0x00401a36  mov  ecx, [eax+4]
0x00401a39  add  ecx, [ebp+0xc]
0x00401a3c  mov  [eax+4], ecx
0x00401a3f  mov  eax, ecx
0x00401a41  pop  ebp
0x00401a42  ret  8
```

Report, in short:

- Answer: adds argument 2 to the 32-bit field at offset 4 of the object in
  argument 1, stores the sum, and returns it. Name: `FUN_00401a30`
  (no evidence for a better name).
- Prototype: `int32 __stdcall f(S *s, int32 delta)`, signedness
  unknown. Two stack
  arguments (`[ebp+8]`, `[ebp+0xc]`), `ret 8` at `0x00401a42` shows the
  callee removes 8 bytes: `__stdcall`, not `__cdecl`. Return in `EAX` at
  `0x00401a3f`.
- Types: `S+0x04`, 4 bytes, integer (add at `0x00401a39`), single use.
  Signedness unknown: `add` does not show it.
- Open questions: none for this function. The field's name needs callers.
