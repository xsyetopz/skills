# Output buffering constructs

Cards for handing output to the operating system fewer times. Pairs live
in `assets/examples/constructs/io.c`. The oracle writes records through a
custom `FILE` whose write callback counts calls and hashes every byte
(`funopen` on macOS and BSD, `fopencookie` on glibc), so it can assert
identical bytes and fewer calls. The glibc path compiles only on Linux
and was not built here.

Measured results are machine-specific: Apple M1 Max, macOS arm64, Apple
clang 21.0.0, `-std=c17 -O2`, hyperfine 1.20.0, shared machine.

## Contents

- Full buffering with setvbuf
- Line buffering
- Batched write calls

## Full buffering with setvbuf

**Definition.** [`setvbuf(stream, buf, mode, size)`][n3220] selects
`_IOFBF` (fully buffered), `_IOLBF` (line buffered), or `_IONBF`
(unbuffered) and optionally the buffer size. It "may be used only after
the stream ... has been associated with an open file and before any
other operation" (N3220 7.23.5.6; N1570 7.21.5.6). Standard output is
fully buffered "if and only if the stream can be determined not to refer
to an interactive device"; standard error is initially not fully buffered (N3220
7.23.3p7).

**Use when.**

- A stream was made unbuffered (`setvbuf(f, NULL, _IONBF, 0)`) or line
  buffered and writes many small records to a file or pipe.
- A high-volume log or export needs fewer calls from a larger buffer.

**Do not use when.**

- Output must reach the reader promptly (interactive prompts, progress,
  logs a crash must not lose): flush at those points or keep line
  buffering.
- Any other operation has already touched the stream: the call is then
  undefined.
- `buf` is an automatic array that dies before the stream is closed.

**Example.**

```c
FILE *f = counting_file(&st); /* or fopen(...) */
check(setvbuf(f, NULL, _IOFBF, 65536) == 0, "setvbuf");
for (size_t i = 0; i < lines; ++i)
  check(fprintf(f, "%zu,%zu\n", i, i * 7 % 1000) > 0, "fprintf");
check(fclose(f) == 0, "fclose flushes");
```

**Cost removed.** Calls into the OS. Measured, 20000 records, 186690
bytes: `STDIO _IONBF 80000 calls, _IOLBF 20000 calls, _IOFBF(64 KiB) 3
calls` (unbuffered `fprintf` handed over each record in 4 pieces).
Whole program, 200000 records to `/dev/null`: `emit-unbuffered`
336.1 ms ± 34.3 ms (System 239.0 ms), `emit-stdio` (default full
buffering to a non-terminal) 37.6 ms ± 22.4 ms (System 1.7 ms).

**Verify.**

1. `sh assets/examples/verify.sh verify` asserts identical bytes and
   hash in all three modes and prints the call counts.
1. On Linux, `strace -c -e trace=write ./prog` counts the system calls
   (not runnable here). On macOS, `dtruss` needs System Integrity
   Protection changes and was not used.

## Line buffering

**Definition.** With `_IOLBF`, characters "are intended to be
transmitted ... as a block when a new-line character is encountered",
when the buffer fills, or when input is requested; support for these
characteristics is implementation-defined (N3220 7.23.3p3). Terminals
usually get this mode.

**Use when.**

- Each line must appear promptly (a log an operator tails), but writing
  byte by byte costs too much.

**Do not use when.**

- Output goes to a file or pipe in bulk: every record still costs one
  OS call.

**Example.**

```c
check(setvbuf(f, NULL, _IOLBF, 4096) == 0, "setvbuf");
```

**Cost removed.** Relative to `_IONBF`: measured 80000 -> 20000 calls for
20000 records (one per line).

**Verify.**

1. The oracle asserts that `_IOLBF` makes no more calls than `_IONBF` and
   more than `_IOFBF`, with identical bytes.
1. Watch the consumer: lines must arrive as written.

## Batched write calls

**Definition.** Format records into a user buffer and call POSIX
[`write`][posix-write] once per filled buffer instead of once per record.
`write` may transfer fewer bytes than requested or fail with `EINTR`, so
loop until the remainder is written.

**Use when.**

- Code calls `write` or `send` per record on a file descriptor.

**Do not use when.**

- Each record must be durable or visible before the next is produced
  (a write-ahead log synced per record, a request-response socket).
- Other writers share the descriptor and rely on per-record atomic
  writes (pipes guarantee atomicity only up to `PIPE_BUF`).

**Example.**

```c
static void write_all(int fd, const char *buf, size_t n) {
  while (n > 0) {
    ssize_t w = write(fd, buf, n);
    if (w < 0 && errno == EINTR)
      continue;
    check(w > 0, "write");
    buf += w;
    n -= (size_t)w;
  }
}

NOINLINE void emit_batched(sink_fn sink, void *ctx, size_t lines) {
  static char buf[65536];
  size_t used = 0;
  for (size_t i = 0; i < lines; ++i) {
    if (sizeof buf - used < 64) {
      sink(ctx, buf, used);
      used = 0;
    }
    used += (size_t)format_record(buf + used, sizeof buf - used, i);
  }
  if (used != 0)
    sink(ctx, buf, used);
}
```

**Cost removed.** System calls. Measured: `WRITE per-record 20000 calls,
batched(64 KiB) 3 calls`; in-process, 20000 records to `/dev/null`:
`write-batching` 25949000 -> 1609333 ns; whole program, 200000 records:
`emit-write` 313.8 ms ± 30.3 ms (System 236.3 ms), `emit-batched`
27.0 ms ± 6.0 ms (System 1.8 ms).

**Verify.**

1. `sh assets/examples/verify.sh verify` compares the bytes of
   `emit-write`, `emit-batched`, `emit-stdio`, and `emit-unbuffered`
   with `cksum`.
1. `sh assets/examples/verify.sh time` runs the hyperfine comparison.

[n3220]: https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3220.pdf
[posix-write]:
  https://pubs.opengroup.org/onlinepubs/9799919799/functions/write.html
