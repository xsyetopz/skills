# Collections, I/O, and parallelism constructs

Cards for hash maps, buffered I/O, stdout, and data parallelism. Std-only
pairs live in [`collections.rs`][collections-rs] and [`io.rs`][io-rs];
pairs that need crates (`rustc-hash`, `rayon`) live in
[`ecosystem/src/lib.rs`](../assets/examples/ecosystem/src/lib.rs) and run
with `sh assets/examples/verify.sh ecosystem`, which fetches the
crates.io dependencies pinned by `ecosystem/Cargo.lock`.

Measured numbers are machine-specific: Apple M1 Max (10 rayon threads),
macOS arm64, rustc 1.98.1, default `release` profile, rustc-hash 2.1.3,
rayon 1.12.0, criterion 0.8.2.

## Contents

- HashMap entry API
- HashMap::with_capacity
- FxHashMap for trusted keys
- BufWriter around many small writes
- BufReader around many small reads
- read_line into a reused String
- Lock stdout once
- Buffered stdout
- rayon parallel iterators

## HashMap entry API

**Definition.** `HashMap::entry(key)` hashes and probes once and returns
an `Entry` that inserts or updates in place ([`HashMap`][hashmap]);
`contains_key` + `get_mut`/`insert` hashes the key twice.

**Use when.**

- Code does `if map.contains_key(k) { *map.get_mut(k).unwrap() += 1 }
  else { map.insert(k, 1) }` or `get` followed by `insert`.

**Do not use when.**

- Keys are owned (`String`) and most calls hit: `entry(k.to_owned())`
  allocates the key even when it already exists. Use `get_mut(&str)`
  first and `entry` only on a miss, or borrow keys (`HashMap<&str, _>`)
  as in the example.

**Example.**

```rust
pub fn count_words_candidate<'a, S: BuildHasher>(
    counts: &mut Counts<'a, S>,
    text: &'a str,
) {
    for word in text.split_whitespace() {
        *counts.entry(word).or_insert(0) += 1;
    }
}
```

**Cost removed.** Hash computations. The oracle's `CountingState` wraps
`RandomState` and counts `finish()`: `COUNT entry-api: 11 -> 6 hash
computations` for `"b a b c b a"`. Time 190.11 -> 156.41 µs (about
3,000 words).

**Verify.**

1. Oracle compares sorted `(word, count)` lists.
1. `COUNT entry-api` line.

## HashMap::with_capacity

**Definition.** `HashMap::with_capacity(n)` can hold at least `n` elements
without reallocating ([`HashMap`][hashmap]); growing from empty rehashes
every element at each resize.

**Use when.**

- The number of distinct keys is known or bounded before insertion
  (building an index over a slice).

**Do not use when.**

- The bound is untrusted input (see the `Vec::with_capacity` card).

**Example.**

```rust
pub fn index_candidate(keys: &[u32]) -> HashMap<u32, usize> {
    let mut map = HashMap::with_capacity(keys.len());
    for (i, &key) in keys.iter().enumerate() {
        map.insert(key, i);
    }
    map
}
```

**Cost removed.** Resize allocations and rehashing. Measured:
`ALLOC hashmap-capacity: 12 -> 1` (4,096 keys); time 130.57 -> 40.18 µs.

**Verify.**

1. Oracle compares the two maps with `==`.
1. `ALLOC hashmap-capacity` line.

## FxHashMap for trusted keys

**Definition.** `std::collections::HashMap` defaults to randomly seeded
SipHash 1-3, which resists HashDoS. For small keys such as integers,
other hashers outperform it but "will typically not protect against
attacks such as HashDoS" ([`HashMap`][hashmap]). `rustc_hash::FxHashMap`
is a `HashMap` with rustc's fast non-cryptographic Fx hash
([docs][rustc-hash]).

**Use when.**

- The profile shows hashing (`SipHasher13`, `hash_one`) as a hot cost and
  keys are not attacker-controlled (internal IDs, compiler symbols).
- A new dependency is allowed.

**Do not use when.**

- Keys come from untrusted input (HTTP headers, user names): the
  [Performance Book][perf-hashing] limits these hashers to cases where
  "HashDoS attacks are not a concern".
- Output depends on iteration order: a different hasher changes it.

**Example.**

```rust
use rustc_hash::FxHashMap;

pub fn histogram_fx(keys: &[u32]) -> FxHashMap<u32, u32> {
    let mut counts =
        FxHashMap::with_capacity_and_hasher(keys.len(), Default::default());
    for &key in keys {
        *counts.entry(key).or_insert(0) += 1;
    }
    counts
}
```

**Cost removed.** Hashing time. Measured with Criterion (100,000 `u32`
keys, 1,013 distinct): siphash `[902.72 927.30 964.09] µs`, fxhash
`[208.47 208.76 209.05] µs`. The Performance Book cites rustc speedups
"of up to 6%" from fnv to fx, and "slowdowns of 1-4%" from switching
rustc to `ahash`; ahash was not measured here.

**Verify.**

1. `sh assets/examples/verify.sh ecosystem` compares the Fx and std
   histograms as maps.
1. `BENCH_FILTER=hasher sh assets/examples/verify.sh measure`.

## BufWriter around many small writes

**Definition.** [`BufWriter`][bufwriter] collects writes in memory
(default capacity "currently 8 KiB") and issues one inner write per full
buffer. Drop tries to flush but ignores errors, so call `flush()`.

**Use when.**

- Code makes many small `write!`/`writeln!` calls to an unbuffered sink:
  `File`, `TcpStream`, `StdoutLock` (see Buffered stdout).

**Do not use when.**

- The sink is in memory (`Vec<u8>`, `String`): the docs say it "provides
  no advantage".
- Data is written in one large call, or output must appear immediately
  (interactive prompts, logs read live) and nothing flushes
  explicitly.

**Example.**

```rust
pub fn write_rows_candidate<W: Write>(
    out: &mut W,
    rows: u32,
) -> io::Result<()> {
    let mut buffered = BufWriter::new(out);
    for row in 0..rows {
        writeln!(buffered, "row {row}")?;
    }
    buffered.flush() // surfaces the error that drop would ignore
}
```

**Cost removed.** Inner write calls (system calls on a real file). The
counting writer reports `COUNT bufwriter: 3000 -> 1 inner write calls`
(1,000 rows; unbuffered, `writeln!` issues three writes per row).

**Verify.**

1. Oracle compares the written bytes.
1. `COUNT bufwriter` line. On a real file, `sudo fs_usage`/`dtruss`
   count `write` calls (not run here).

## BufReader around many small reads

**Definition.** [`BufReader`][bufreader] reads large chunks from the
inner reader and serves small reads from memory; `fill_buf`/`consume`
expose the buffer directly. "Rust file I/O is unbuffered by default"
([Performance Book][perf-io]).

**Use when.**

- Code calls `read` with tiny buffers (one byte, one struct) on a `File`
  or socket.

**Do not use when.**

- The input is already in memory (`&[u8]`, `Cursor`).
- The whole file is read once: `std::fs::read` is simpler.

**Example.**

```rust
pub fn count_lines_candidate<R: Read>(input: R) -> io::Result<usize> {
    let mut reader = BufReader::new(input);
    let mut lines = 0;
    loop {
        let chunk = reader.fill_buf()?;
        if chunk.is_empty() {
            return Ok(lines);
        }
        lines += chunk.iter().filter(|&&b| b == b'\n').count();
        let consumed = chunk.len();
        reader.consume(consumed);
    }
}
```

**Cost removed.** Inner read calls: `COUNT bufreader: 18615 -> 4 inner
read calls` (about 18 KB of input); time 65.17 -> 4.05 µs.

**Verify.**

1. Oracle compares the line counts.
1. `COUNT bufreader` line.

## read_line into a reused String

**Definition.** `BufRead::lines()` allocates a new `String` per line;
`read_line(&mut buf)` appends into a caller-owned buffer that is
`clear()`ed and reused ([Performance Book][perf-heap]).

**Use when.**

- A loop over `lines()` shows one allocation per line in the allocation
  count or profile.

**Do not use when.**

- The loop keeps each line (pushes it into a `Vec<String>`): each needs
  its own allocation anyway.
- The loop depends on `lines()` stripping `"\n"` (and `"\r\n"`):
  `read_line` keeps them, so strip them yourself, as the example does.

**Example.**

```rust
let mut line = String::new();
loop {
    line.clear();
    if input.read_line(&mut line)? == 0 {
        return Ok(longest);
    }
    let text = line.strip_suffix('\n').unwrap_or(&line);
    let text = if line.ends_with('\n') {
        text.strip_suffix('\r').unwrap_or(text)
    } else {
        text
    };
    longest = longest.max(text.len());
}
```

**Cost removed.** Measured: `ALLOC read-line-reuse: 512 -> 2` (512 lines);
time 36.51 -> 14.38 µs.

**Verify.**

1. Oracle compares `""`, `"a\r\nbbb\n"`, `"cc\rdd"` (bare `\r` kept), a
   trailing blank line, and the fixture.
1. `ALLOC read-line-reuse` line.

## Lock stdout once

**Definition.** `print!`/`println!` lock stdout on every call
([Performance Book][perf-io]); `io::stdout().lock()` returns a
`StdoutLock<'static>` held for the whole loop ([`Stdout`][stdout]).

**Use when.**

- A loop prints many lines and the profile shows lock acquisition, or
  another thread's output must not interleave within the block.

**Do not use when.**

- The goal is a large speedup from the lock alone: `Stdout` is
  line-buffered when connected to a terminal ([`Stdout`][stdout]), and
  the measured run to `/dev/null` below also spent its time in per-line
  writes. Buffered stdout (next card) is the default fix.

**Example.**

```rust
pub fn print_rows_candidate(rows: u32) -> io::Result<()> {
    let mut out = io::stdout().lock();
    for row in 0..rows {
        writeln!(out, "row {row}")?;
    }
    out.flush()
}
```

**Cost removed.** Per-line lock/unlock. Measured with hyperfine
(200,000 lines to `/dev/null`): baseline 250.5 ms ± 7.9 ms, candidate
244.7 ms ± 2.4 ms. Both spent about 210 ms in System time, so per-line
writes, not locking, dominate.

**Verify.**

1. `sh assets/examples/verify.sh verify` compares `cksum` of both outputs.
1. `sh assets/examples/verify.sh time` runs the hyperfine comparison.

## Buffered stdout

**Definition.** `BufWriter::new(io::stdout().lock())` combines one lock
with an 8 KiB buffer, so stdout receives one write per buffer instead
of one per line.

**Use when.**

- A command-line tool prints many lines to a pipe or file (reports,
  generated code, CSV).

**Do not use when.**

- Output must appear line by line while the program runs (progress,
  interactive prompts, logs followed live) and the code does not flush
  at those points.
- The program can exit through `std::process::exit` before the writer is
  flushed: [`exit`][exit] does not run destructors, so buffered output
  is lost.

**Example.**

```rust
pub fn print_rows_buffered(rows: u32) -> io::Result<()> {
    let mut out = BufWriter::new(io::stdout().lock());
    for row in 0..rows {
        writeln!(out, "row {row}")?;
    }
    out.flush()
}
```

**Cost removed.** Measured with hyperfine: 244.7 ms -> 8.7 ms ± 1.2 ms;
System time 210.2 ms -> 1.4 ms (200,000 lines to `/dev/null`).

**Verify.**

1. `sh assets/examples/verify.sh verify` compares `cksum` against
   `println!` output.
1. `sh assets/examples/verify.sh time`.

## rayon parallel iterators

**Definition.** With `use rayon::prelude::*`, `par_iter()` splits a
slice across a work-stealing thread pool and runs the same adapter chain
in parallel; rayon "guarantees data-race free executions"
([rayon][rayon]). The pool size defaults to `RAYON_NUM_THREADS` or the
number of logical CPUs ([`ThreadPoolBuilder`][rayon-pool]).

**Use when.**

- Items are independent, each does enough CPU work to outweigh task
  overhead, and adding a dependency is allowed.

**Do not use when.**

- Per-item work is tiny (a few additions): splitting overhead
  dominates. Measure, or use `with_min_len`.
- Items share state behind a `Mutex`: contention serializes the work.
- The workload already runs inside a parallel context (another pool,
  async runtime worker threads): the CPUs get oversubscribed.
- Floating-point reductions must match the serial result bit-for-bit:
  parallel `sum` reassociates.

**Example.**

```rust
use rayon::prelude::*;

pub fn steps_parallel(inputs: &[u64]) -> Vec<u32> {
    inputs.par_iter().map(|&n| collatz_steps(n)).collect()
}
```

**Cost removed.** Wall time on idle cores; CPU time does not drop.
Measured with Criterion (99,999 inputs, 10 threads): serial
`[13.269 14.158 15.662] ms`, parallel `[2.2530 2.3734 2.5083] ms`.

**Verify.**

1. `sh assets/examples/verify.sh ecosystem` asserts
   `steps_serial == steps_parallel` element by element. That `collect`
   into `Vec` preserves order is tested, not cited: the fetched rayon
   docs did not state it.
1. `BENCH_FILTER=rayon sh assets/examples/verify.sh measure`; run the
   application with `RAYON_NUM_THREADS=1` as the serial control.

[hashmap]: https://doc.rust-lang.org/std/collections/struct.HashMap.html
[rustc-hash]: https://docs.rs/rustc-hash/2.1.3/rustc_hash/
[perf-hashing]: https://nnethercote.github.io/perf-book/hashing.html
[bufwriter]: https://doc.rust-lang.org/std/io/struct.BufWriter.html
[bufreader]: https://doc.rust-lang.org/std/io/struct.BufReader.html
[perf-io]: https://nnethercote.github.io/perf-book/io.html
[perf-heap]: https://nnethercote.github.io/perf-book/heap-allocations.html
[stdout]: https://doc.rust-lang.org/std/io/struct.Stdout.html
[exit]: https://doc.rust-lang.org/std/process/fn.exit.html
[rayon]: https://docs.rs/rayon/1.12.0/rayon/
[rayon-pool]: https://docs.rs/rayon/1.12.0/rayon/struct.ThreadPoolBuilder.html
[collections-rs]: ../assets/examples/constructs/src/collections.rs
[io-rs]: ../assets/examples/constructs/src/io.rs
