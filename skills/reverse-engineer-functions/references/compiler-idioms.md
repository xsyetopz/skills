# Compiler idioms

Compilers add code that the source did not spell out, and remove or move
code that it did. Name each idiom in the report and leave it out of the
description of the function's logic.

Exact instruction shapes change with the compiler, its version, the target,
and the flags. This file describes each idiom by its effect. When the shape
in the binary is uncertain, use the [confirmation method](#confirm-a-shape).

## Contents

- [Stack cookies](#stack-cookies)
- [Exception handling](#exception-handling)
- [Inlined library calls](#inlined-library-calls)
- [Switch jump tables](#switch-jump-tables)
- [Tail calls](#tail-calls)
- [Reordered and split blocks](#reordered-and-split-blocks)
- [Confirm a shape](#confirm-a-shape)
- [Sources](#sources)

## Stack cookies

MSVC `/GS` is on by default. The compiler places a cookie before the
return address, sets it on entry, and checks it on exit through a helper.
`__security_init_cookie` initializes the global cookie value. On x86 the
check also protects the exception handler address. Parameters that could
be overwritten are copied to locals below the buffers.

GCC `-fstack-protector` adds a guard to functions that call `alloca` or
have buffers of 8 bytes or more.

How it looks by effect:

- Entry: a load from a global (or a thread-local slot), often combined with
  the frame pointer or stack pointer, stored into the frame just below the
  saved registers.
- Exit: the stored value is reloaded, compared or combined, and passed to a
  check helper or followed by a call to a failure routine that does not
  return.

Effects on analysis:

- The cookie slot is not a local variable of the source. Do not give it a
  name or a type.
- The presence of a cookie is evidence that the function has a local
  buffer (under GCC's rule above, one of 8 bytes or more, or an `alloca`).
- Copied parameters appear as a second location for the same argument.
  Treat both as one argument.

## Exception handling

Win64 exception handling is table-based. The code has no frame setup for
it. Each function with unwind data has a `RUNTIME_FUNCTION` entry in
`.pdata` (image-relative start, end, and unwind information). Its
`UNWIND_INFO` flags include `UNW_FLAG_EHANDLER` (has an exception handler),
`UNW_FLAG_UHANDLER` (has a termination handler), and `UNW_FLAG_CHAININFO`
(chained to another unwind entry).

Use these to:

- Find function boundaries that the auto-analysis missed: every `.pdata`
  entry starts a function or a chained part of one.
- Tell that a function has a handler before reading its code.
- Recognize a code region that belongs to a parent function (chained
  unwind information) instead of treating it as a separate function.

x86 (32-bit) SEH frames are built in code. Their exact layout is not
covered here; confirm it with the [method below](#confirm-a-shape) before
you describe it.

## Inlined library calls

A call to `memcpy`, `memset`, or `strlen` in the source can become inline
code. GCC documents that with `-fno-builtin`, `memcpy` calls may become
inline copy loops, and `-foptimize-strlen` optimizes `strlen` and related
calls.

By effect:

- Copy: loads and stores through two pointers with the same stride,
  counting up to a length, or a fixed sequence of wide moves for a known
  size.
- Fill: repeated stores of one value.
- Length: a loop that reads bytes (or wider units) until a zero is found,
  then subtracts the start pointer.

Report these as the library call (`memcpy(dst, src, 0x40)` inlined at
`0x...`), with the loop addresses as evidence.

## Switch jump tables

A dense `switch` usually becomes a bounds check on the index, a branch to
the default case, and an indirect jump through a table of code addresses
or offsets. GCC's `-fno-jump-tables` turns this off, which shows that
jump tables are the default for suitable switches.

Recover it as follows:

1. Read the bounds check: the compared constant is the highest case
   index after any subtraction of the lowest case value.
1. Read the table: its base address, entry size, and whether entries are
   absolute addresses or offsets relative to a base.
1. Map each index to its target, and group indexes that share a target.
1. Add the subtracted lowest value back to get the source case values.

If the tool did not recover the table, the targets look like unreachable
code. Check for an indirect jump before you call code dead.

## Tail calls

GCC's `-foptimize-sibling-calls` (on at `-O2`, `-O3`, and `-Os`) turns a
call in tail position into a jump. The function ends with a `jmp` to
another function instead of `call` then `ret`.

Effects on analysis:

- The jump target's return value is this function's return value.
- The target may appear as part of this function if the tool treats the
  `jmp` as an internal branch. Check whether the target has other callers
  or its own entry.
- Arguments for the target are set up just before the `jmp`, in the
  target's convention.

## Reordered and split blocks

GCC's `-freorder-blocks` (on at `-O1` and above) reorders basic blocks,
and `-freorder-blocks-and-partition` moves hot and cold blocks into
different sections.

- Branch order in the binary need not match the `if` order in the source.
  Read conditions, not layout.
- Cold code (error paths, rarely used cases) can sit at the end of the
  function or in a separate section. A block there with a jump back into
  the function belongs to that function.

## Confirm a shape

When you are not sure that a sequence is a given idiom:

1. Identify the compiler and version if you can, from strings, build
   metadata, or runtime library functions in the binary. Cite where.
1. Write a small function that uses the suspected construct.
1. Compile it with that compiler and the likely flags.
1. Disassemble the result and compare its shape with the binary.
1. Report the comparison as the evidence, with the compiler and flags
   used. If no match is found, keep the claim as inference.

## Sources

- MSVC `/GS`: [msvc-gs]
- Win64 exception handling: [msvc-eh]
- GCC optimize options (`-foptimize-sibling-calls`, `-foptimize-strlen`,
  `-freorder-blocks`, `-freorder-blocks-and-partition`): [gcc-opt]
- GCC `-fno-builtin`: [gcc-dialect]
- GCC `-fno-jump-tables`: [gcc-codegen]
- GCC `-fstack-protector`: [gcc-instr]

[msvc-gs]: https://learn.microsoft.com/en-us/cpp/build/reference/gs-buffer-security-check
[msvc-eh]: https://learn.microsoft.com/en-us/cpp/build/exception-handling-x64
[gcc-opt]: https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html
[gcc-dialect]: https://gcc.gnu.org/onlinedocs/gcc/C-Dialect-Options.html
[gcc-codegen]: https://gcc.gnu.org/onlinedocs/gcc/Code-Gen-Options.html
[gcc-instr]: https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html
