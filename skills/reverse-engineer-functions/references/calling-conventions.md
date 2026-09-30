# Calling conventions

Use these tables to read a prototype from the code. They describe the
documented conventions. A function that is only called from inside the
binary may not follow them, so confirm each one with the checks below.

## Contents

- [Checks that work on every platform](#checks-that-work-on-every-platform)
- [x86 (32-bit, MSVC keywords)](#x86-32-bit-msvc-keywords)
- [Win64 (Microsoft x64)](#win64-microsoft-x64)
- [SysV x86-64 (Linux, BSD, macOS)](#sysv-x86-64-linux-bsd-macos)
- [AArch64 (AAPCS64)](#aarch64-aapcs64)
- [Sources](#sources)

## Checks that work on every platform

1. Entry: list registers that are read before they are written. They are
   arguments, or preserved registers that are saved before use.
1. Callers: at each call site, list the registers and stack slots set just
   before the `call` (or `bl` on AArch64).
1. Exit: find what is written to the return register on every path.
1. Stack cleanup: on x86, `ret N` means the callee removes `N` bytes of
   arguments; plain `ret` means the caller does. On x86-64 and AArch64 the
   callee ends with plain `ret`, and the caller owns the argument area.
1. Hidden result pointer: when a function returns a large struct, the
   caller passes the result address, and every visible argument moves.

## x86 (32-bit, MSVC keywords)

All arguments are widened to 32 bits.

| Convention | Arguments | Cleanup | Notes |
| --- | --- | --- | --- |
| `__cdecl` | stack, right to left | caller | allows varargs |
| `__stdcall` | stack, right to left | callee | decorated `_func@12`; varargs functions become `__cdecl` |
| `__fastcall` | first two DWORD-or-smaller args in `ECX`, `EDX`, left to right; rest on stack right to left | callee | structs always on stack; decorated `@name@N` |
| `__thiscall` | `this` in `ECX`; rest on stack, right to left | callee | varargs member functions use `__cdecl` with `this` pushed last |

- Return: `EAX`; 8-byte structs in `EDX:EAX`; larger structs through a
  hidden pointer, which the function also returns in `EAX`.
- Preserved: the prolog saves `ESI`, `EDI`, `EBX`, and `EBP` if the
  function uses them.
- On x64 and ARM, MSVC accepts these keywords and ignores them.

The decoration (`_func@12`, `@name@N`) gives the argument byte count when
symbols are present; that is "seen" evidence for the stack size.

## Win64 (Microsoft x64)

| Item | Rule |
| --- | --- |
| Integer and pointer arguments | `RCX`, `RDX`, `R8`, `R9` |
| Floating-point arguments | `XMM0`-`XMM3`, by argument position |
| Fifth and later arguments | stack, right to left |
| Shadow store | the caller allocates 32 bytes for the four register arguments |
| Aggregates | 8, 16, 32, or 64 bits pass as integers; others by pointer |
| Varargs or unprototyped | floats are duplicated in the integer register |
| Return | `RAX` or `XMM0`; non-POD or odd-size values go to caller memory whose pointer arrives in `RCX` and is returned in `RAX` |
| Volatile | `RAX`, `RCX`, `RDX`, `R8`-`R11`, `XMM0`-`XMM5` |
| Nonvolatile | `RBX`, `RBP`, `RDI`, `RSI`, `RSP`, `R12`-`R15`, `XMM6`-`XMM15` |
| Stack alignment | 16 bytes outside the prolog and epilog |

"By position" means the second argument uses `RDX` or `XMM1`, never both:
a `(int, double)` function reads `ECX` and `XMM1`.

With a hidden result pointer in `RCX`, the first visible argument is in
`RDX`.

## SysV x86-64 (Linux, BSD, macOS)

| Item | Rule |
| --- | --- |
| Integer and pointer arguments | `RDI`, `RSI`, `RDX`, `RCX`, `R8`, `R9` |
| SSE arguments | `XMM0`-`XMM7`, counted separately from integers |
| Memory-class arguments | stack, right to left |
| Varargs | `AL` holds an upper bound on the number of vector registers used (0 to 8) |
| Static chain | `R10` |
| Return | `RAX` then `RDX`, or `XMM0` then `XMM1`; memory-class results through a hidden pointer in `RDI`, returned in `RAX` |
| Callee-saved | `RBX`, `RBP`, `R12`-`R15`, `RSP` |
| Red zone | 128 bytes below `RSP` that the function may use without moving `RSP` |
| Alignment | the end of the argument area is 16-byte aligned |

The psABI text does not state in words who removes stack arguments. The
check: the callee ends in `ret` without an immediate, so the caller owns
that area.

Integer and SSE registers are counted separately: `f(int, double, int)`
uses `EDI`, `XMM0`, `ESI`. A `mov al, N` or `xor eax, eax` just before a
call suggests a varargs callee (such as a `printf`-style function).

## AArch64 (AAPCS64)

| Register | Role |
| --- | --- |
| `x0`-`x7` | arguments and results; caller-saved |
| `v0`-`v7` | FP and SIMD arguments and results |
| `x8` | indirect result location: the caller reserves memory and passes its address; the callee need not preserve `x8` |
| `x9`-`x15` | caller-saved temporaries |
| `x16`, `x17` | `IP0`, `IP1`: used by veneers and PLT code |
| `x18` | platform register |
| `x19`-`x28` | callee-saved |
| `x29` (FP) | frame pointer; callee-saved |
| `x30` (LR) | link register |
| `v8`-`v15` | only the low 64 bits are callee-saved |

- `SP` is 16-byte aligned at a public interface.
- Stacked arguments start at `SP` (the next stacked argument address),
  8-byte aligned.
- The frame record (`FP`, `LR`) forms a chain that you can walk.

Because the result pointer has its own register (`x8`), a large return
value does not shift `x0`-`x7`, unlike Win64 and SysV x86-64.

## Sources

- MSVC argument passing and naming conventions: [msvc-conv]
- MSVC `__cdecl`, `__stdcall`, `__fastcall`, `__thiscall`: [msvc-cdecl],
  [msvc-stdcall], [msvc-fastcall], [msvc-thiscall]
- Microsoft x64 calling convention: [msvc-x64]
- System V x86-64 psABI: [sysv]
- Arm AAPCS64: [aapcs64]

[msvc-conv]: https://learn.microsoft.com/en-us/cpp/cpp/argument-passing-and-naming-conventions
[msvc-cdecl]: https://learn.microsoft.com/en-us/cpp/cpp/cdecl
[msvc-stdcall]: https://learn.microsoft.com/en-us/cpp/cpp/stdcall
[msvc-fastcall]: https://learn.microsoft.com/en-us/cpp/cpp/fastcall
[msvc-thiscall]: https://learn.microsoft.com/en-us/cpp/cpp/thiscall
[msvc-x64]: https://learn.microsoft.com/en-us/cpp/build/x64-calling-convention
[sysv]: https://gitlab.com/x86-psABIs/x86-64-ABI
[aapcs64]: https://github.com/ARM-software/abi-aa/blob/main/aapcs64/aapcs64.rst
