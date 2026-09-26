# Nondeterminism, tools, and packaging

Intermittent failures, memory errors, and packaging a reproduction
someone else can run. Examples are in
[`assets/examples/reproduce/`](../assets/examples/reproduce/verify.sh).

## Contents

- Failure rate over repeated runs
- Forced interleaving
- Fixed seeds and environment
- AddressSanitizer
- Race detectors
- Artifact shape per ecosystem
- Delivery record
- Regression test from the reproduction

## Failure rate over repeated runs

**Definition.** Run the reproduction N times and report failures/N instead
of "it fails sometimes".

**Use when.** The failure is intermittent. When bisecting it, turn the
measured rate into a
[majority vote](bisect-oracles.md#majority-vote-for-flaky-tests).

**Do not use when.** Claiming a fix from one passing run of an
intermittent failure.

**Example.**

```sh
python3 race/counter.py rate 200
# unforced failures: 0/200
```

Measured: the timing-dependent lost-increment race failed 0 times in 200
runs although the bug is real. A rate of 0 does not prove absence.

**Cost removed.** False "cannot reproduce" and false "fixed" claims.

**Verify.**

1. Report N, failures, and the command; compare rates before and after a
   fix with the same N.

## Forced interleaving

**Definition.** Insert barriers or callbacks so the bad thread interleaving
happens on every run, turning a race into a deterministic reproduction.

**Use when.** The suspected race can be expressed as "A reads, B reads,
A writes, B writes".

**Do not use when.** The interleaving is unknown; use a race detector
first.

**Example.**

```python
value = total[0]            # read
both_read.wait()            # both threads have read the old value
total[0] = value + 1        # write
```

**Cost removed.** Flaky reproductions. Measured: 6/6 failures forced,
versus 0/200 by timing.

**Verify.**

1. `verify.sh` runs the forced version six times, requires six failures,
   and requires the locked version to succeed.

## Fixed seeds and environment

**Definition.** Pin every source of variation: random seeds, hash seeds
(`PYTHONHASHSEED`), time zone (`TZ`), locale (`LC_ALL`), current time
(injected clock), environment variables (`env -i`), and tool versions.

**Use when.** A failure depends on ordering, time, locale, or randomness.

**Do not use when.** Pinning hides the condition that causes the bug;
record the value that fails.

**Example.**

```sh
env -i PATH="$PATH" TZ=UTC LC_ALL=C PYTHONHASHSEED=0 python3 repro.py
```

**Cost removed.** "Works on my machine".

**Verify.**

1. The reproduction fails with the pinned values on two machines.

## AddressSanitizer

**Definition.** `-fsanitize=address` makes a C or C++ program stop at the
first invalid memory access and print its kind, size, and stacks
([AddressSanitizer][asan]).

**Use when.** A C/C++ bug shows corrupted data, random crashes, or
different behavior between builds.

**Do not use when.** Measuring performance; ASan slows execution.

**Example.**

```sh
cc -g -fsanitize=address -fno-omit-frame-pointer overflow.c -o overflow
./overflow
# ERROR: AddressSanitizer: heap-buffer-overflow ... WRITE of size 6
```

Trap: on the authoring machine the default macOS SDK failed to link
(`ld: tapi error: malformed file`). `verify.sh` falls back to the first
installed SDK that links (`SDKROOT=...MacOSX15.2.sdk` here).

**Cost removed.** Memory bugs that corrupt state far from the cause.

**Verify.**

1. `verify.sh` asserts `heap-buffer-overflow` in the report and a
   non-zero exit.

## Race detectors

**Definition.** Runtime detectors that report unsynchronized concurrent
accesses: `go test -race` ([Go race detector][go-race]) and
`-fsanitize=thread` for C/C++ ([ThreadSanitizer][tsan]).

**Use when.** A concurrency bug is suspected but the interleaving is
unknown.

**Do not use when.** The language has no detector for the runtime in use
(Python threads); use forced interleaving.

**Example.**

```sh
go test -race ./...
cc -g -fsanitize=thread race.c -o race && ./race
```

**Cost removed.** Guessing which accesses race.

**Verify.**

1. The detector report names both stacks; a forced-interleaving test
   then reproduces the failure deterministically.

## Artifact shape per ecosystem

**Definition.** The smallest runnable form for the ecosystem: one source
file and an exact command when that is enough; the smallest manifest,
lockfile, and config only when they affect the behavior.

| Ecosystem | Smallest form |
| --- | --- |
| C/C++ | one source file plus the exact compiler command |
| Rust | exact `rustc` command, or `Cargo.toml` when features or resolution matter |
| .NET | one project file and one source file |
| JVM | a `javac` command, or the smallest Maven/Gradle project when build behavior matters |
| JS/TS/Bun | one file and a runtime command; manifest and lockfile when dependencies matter |
| Browser | runnable HTML/CSS/JS plus browser and version |
| Integrations | both sides, minimal fixtures, the real host or engine |

**Use when.** Packaging for a teammate or an upstream issue.

**Do not use when.** You would send prose steps instead of files; send the
files.

**Example.** `python-delimiter-repro/`: `repro.py` and `verify.py` only.
The failing code, from
`assets/examples/reproduce/python-delimiter-repro/repro.py`:

```python
message = "42|start|stop"
message_id, text = message.split("|")
print(message_id, text)
```

Executed from `assets/examples/reproduce/` on a copy in an empty
directory:

```sh
scratch=$(mktemp -d)
cp -R python-delimiter-repro "$scratch/empty"
cd "$scratch/empty" && ls && python3 verify.py
# repro.py
# verify.py
# Reproduced the documented delimiter parsing failure.
```

**Cost removed.** Maintainers rebuilding your environment.

**Verify.**

1. Copy the artifact to an empty directory and run it there.

## Delivery record

**Definition.** A README or issue body with the fields a maintainer needs
to run and judge the reproduction ([minimal reproducible
example][mre]).

**Use when.** Sharing any reproduction.

**Do not use when.** Including credentials or private data; replace them
with synthetic values that keep the condition.

**Example.**

```text
Title: parse_message fails when the text contains "|"
Prerequisites: Python 3.10+
Tested environment: macOS 27 arm64, CPython 3.14.7
Run: python3 repro.py
Input: 42|start|stop
Expected: message ID 42 and text "start|stop"
Actual: ValueError: too many values to unpack (expected 2)
Verification: python3 verify.py (exit 0)
Nondeterminism: deterministic
```

**Cost removed.** Back-and-forth on missing details.

**Verify.**

1. A reader with only the artifact and the record reproduces the failure.

## Regression test from the reproduction

**Definition.** A test in the project's suite, converted from the
reproduction, that fails before the fix and passes after.

**Use when.** The bug will be fixed in this repository.

**Do not use when.** The failure is in an upstream dependency; keep the
standalone artifact for the upstream report.

**Example.**

```python
def test_text_may_contain_delimiter(self) -> None:
    self.assertEqual(parse_message("42|start|stop"), ("42", "start|stop"))
```

**Cost removed.** The bug coming back.

**Verify.**

1. The test fails on the unfixed code and passes on the fix.

[asan]: https://clang.llvm.org/docs/AddressSanitizer.html
[go-race]: https://go.dev/doc/articles/race_detector
[tsan]: https://clang.llvm.org/docs/ThreadSanitizer.html
[mre]: https://stackoverflow.com/help/minimal-reproducible-example
