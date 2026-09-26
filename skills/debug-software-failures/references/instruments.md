# Instruments

Tools that show where a program is stuck or why it crashed.
[`assets/examples/instruments/verify.sh`][verify] runs each one
against a program with a known fault (measured on macOS arm64: Python
3.14.7, Go 1.27.1, OpenJDK 25, lldb from Swift 6.3.3).

## Contents

- Python stack dumps with faulthandler
- Go deadlock detection and goroutine dumps
- JVM thread dump with jcmd
- Native crash backtrace with lldb
- System call tracing
- Verbose and clean builds
- Resource limits and open files

## Python stack dumps with faulthandler

**Definition.** `faulthandler.dump_traceback_later(timeout, exit=True)`
prints every thread's Python stack after `timeout` seconds and exits;
`python3 -X faulthandler` also dumps on fatal signals
([faulthandler][faulthandler]).

**Use when.** A Python program hangs or deadlocks.

**Do not use when.** The hang is in native code that holds the GIL with no
Python frames; use a native debugger.

**Example.**

```python
faulthandler.dump_traceback_later(2.0, exit=True)
```

Measured output: `line 20 in transfer_a_to_b` and `line 27 in
transfer_b_to_a`, the two opposite-order `with lock_x` lines.

**Cost removed.** Guessing where the program hangs.

**Verify.**

1. `verify.sh` asserts both thread frames appear in the dump.

## Go deadlock detection and goroutine dumps

**Definition.** When every goroutine is blocked, the Go runtime aborts with
`fatal error: all goroutines are asleep - deadlock!` and prints goroutine
stacks; a running process prints all goroutines on `SIGQUIT`
(`kill -QUIT pid`), with `GOTRACEBACK=all` controlling detail
([runtime][go-runtime]).

**Use when.** A Go program hangs or reports a deadlock.

**Do not use when.** Only some goroutines are blocked. The runtime does not
detect a partial deadlock; send `SIGQUIT` instead.

**Example.**

```go
results := make(chan int)
results <- 42 // no goroutine ever receives
```

Measured: the runtime printed the deadlock message and `main.go:9`.

**Cost removed.** Hangs with no location.

**Verify.**

1. `verify.sh` asserts the message and the blocked line.

## JVM thread dump with jcmd

**Definition.** `jcmd <pid> Thread.print` (or `jstack <pid>`) prints all
Java thread stacks with lock ownership and reports cycles as
`Found one Java-level deadlock` ([jcmd][jcmd]).

**Use when.** A JVM process hangs or throughput collapses.

**Do not use when.** The process has exited; enable
`-XX:+HeapDumpOnOutOfMemoryError` or JFR for post-mortem data instead.

**Example.**

```sh
jcmd "$pid" Thread.print > threads.txt
grep -A20 'Found one Java-level deadlock' threads.txt
```

Measured: the report named `Deadlock.java:14` and `Deadlock.java:26`.

**Cost removed.** Restarting a hung service without learning why.

**Verify.**

1. `verify.sh` starts the program, dumps its threads, and asserts the
   deadlock report.

## Native crash backtrace with lldb

**Definition.** lldb in batch mode runs a native program and, when it
crashes, prints the stop reason and the stack:
`lldb --batch -o run -k bt -k quit -- ./prog` (`-k` commands run only if
the target crashes) ([lldb][lldb]).

**Use when.** A C, C++, Rust, or Swift program crashes (signal, exception).

**Do not use when.** The crash depends on the debugger's timing; use core
dumps or sanitizers.

**Example.** From `assets/examples/instruments/verify.sh`:

```sh
    cc -g -O0 "$ROOT/crash.c" -o "$WORK/crash"
    # -k runs only if the target crashes; without "-k quit" batch mode can
    # wait on the stopped process (observed with the swiftly lldb).
    lldb --batch -o run -k bt -k quit -- "$WORK/crash" >"$WORK/lldb.log" 2>&1 ||
        true
    grep -q 'name_length' "$WORK/lldb.log"
    want=$(grep -n 'config->name\[length\]' "$ROOT/crash.c" | cut -d: -f1)
    got=$(grep -m1 -o 'crash.c:[0-9]*' "$WORK/lldb.log" | cut -d: -f2)
    [ "$got" = "$want" ] || {
        echo "lldb stopped at crash.c:$got, expected $want" >&2
        exit 1
    }
```

Measured: `stop reason = EXC_BAD_ACCESS (code=1, address=0x0)` in
`name_length(config=0x0000000000000000) at crash.c:11:18`, the
`config->name` read in the loop condition, with `main` at
`crash.c:25:19` as the next frame. Without `-k quit`, the
swiftly-installed lldb waited on the stopped process and never exited.

**Cost removed.** Crashes reported only as "Segmentation fault".

**Verify.**

1. `verify.sh` builds with `-g -O0`, asserts the `name_length` frame, and
   asserts that the first `crash.c:` line is the `config->name[length]`
   line of `crash.c`.

## System call tracing

**Definition.** `strace -f -e trace=file,network ./prog` (Linux) and
`dtruss` (macOS, limited by System Integrity Protection) print each system
call with its arguments and result.

**Use when.** A program fails on files, permissions, sockets, or
environment, and its own error is vague ("cannot open config").

**Do not use when.** On macOS with SIP enabled, `dtruss` cannot trace
system binaries; use application logging or run on Linux.

**Example.**

```sh
strace -f -e trace=openat,connect ./app 2>&1 | grep -E 'ENOENT|ECONNREFUSED'
```

Not measured: macOS has no `strace`, and `dtruss` needs SIP changes.

**Cost removed.** Guessing which file or host a program uses.

**Verify.**

1. The failing call and its error code match the application's failure.

## Verbose and clean builds

**Definition.** Verbose modes print the exact commands and the first
error: `cargo build -v`, `make V=1`, `cmake --build . --verbose`,
`dotnet build -v detailed`, `go build -x`. A clean build in a fresh
checkout separates cache problems from source problems.

**Use when.** A build fails with only a summary message, or only on some
machines.

**Do not use when.** You would delete caches as the fix. Name the cache
and explain why its content was wrong.

**Example.**

```sh
git worktree add /tmp/clean HEAD && cd /tmp/clean && cargo build -v
```

**Cost removed.** Misattributing stale artifacts to source changes.

**Verify.**

1. Record whether the failure appears in the clean checkout.

## Resource limits and open files

**Definition.** `ulimit -a` shows process limits; `lsof -p <pid>` lists
open files and sockets; `/usr/bin/time -l` (macOS) or `-v` (Linux) reports
peak memory.

**Use when.** Failures start after the program has run for a while
(`EMFILE`, `Too many open files`, out-of-memory kills).

**Do not use when.** You would raise the limit as the fix before finding
the leak.

**Example.**

```sh
lsof -p "$pid" | wc -l
/usr/bin/time -l ./batch-job input.csv
```

**Cost removed.** Leaks hidden by higher limits.

**Verify.**

1. The open-file or memory count grows with each operation before the
   fix and stays flat after it.

[faulthandler]: https://docs.python.org/3/library/faulthandler.html
[go-runtime]: https://pkg.go.dev/runtime
[jcmd]: https://docs.oracle.com/en/java/javase/25/docs/specs/man/jcmd.html
[lldb]: https://lldb.llvm.org/man/lldb.html
[verify]: ../assets/examples/instruments/verify.sh
