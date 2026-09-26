# Stream, formatting, and conversion constructs

Cards that remove flushes, stream overhead, temporary strings, and
locale work from text output and number conversion. Pairs and stdout
printers live in [`constructs/io.cpp`](../assets/examples/constructs/io.cpp).
`verify.sh verify` checks that every conversion produces identical text
(including `LONG_MIN`, `LONG_MAX`, `-0.0`, `5e-324`) and that all stdout
printers write the same bytes (`cksum`); `verify.sh io` times the
printers with hyperfine.

Measured numbers are machine-specific: Apple M1 Max, macOS 27.0 arm64,
Apple clang 21.0.0, libc++ 21.1, `-std=c++23 -O2`, output to a pipe
(`hyperfine --output=pipe`, 200000 rows, shared machine).

## Contents

- Newline instead of std::endl
- sync_with_stdio(false) and cin.tie(nullptr)
- Build text in a buffer and write once
- std::print
- std::format_to into a reused buffer
- std::to_chars for numbers to text
- std::from_chars for text to numbers

## Newline instead of std::endl

**Definition.** `std::endl` inserts `'\n'` and then calls `flush()`
([ostream.manip]); on `std::cout` each flush is a `write` system call.
`'\n'` alone leaves the data in the stream buffer.

**Use when.**

- A loop writes many lines with `std::endl` to a file, pipe, or string
  stream.

**Do not use when.**

- Each line must be visible immediately: progress output, logs read
  while the process runs, or output before a possible crash. Keep the
  flush there, or use `std::cerr`, which is unit-buffered
  ([narrow.stream.objects]).
- Ordering against interleaved C `stdio` output relies on the flush.

**Example.**

```cpp
for (long i = 0; i < rows; ++i) {
  out << "row " << i << '\n'; // baseline: << std::endl
}
```

Runnable: `assets/examples/constructs/io.cpp`.

**Cost removed.** One flush per line. Measured: a counting `streambuf`
shows `FLUSHES newline-not-endl: 100 -> 0`; hyperfine
`print-endl` 155.7 ms ± 13.8 (system 75.1 ms) -> `print-newline`
46.3 ms ± 5.0 (system 4.4 ms).

**Verify.**

1. `verify.sh verify` checks identical bytes and the `FLUSHES` line.
1. `verify.sh io` compares the two printers.

## sync_with_stdio(false) and cin.tie(nullptr)

**Definition.** Called with `false` before any I/O on the standard
streams, `std::ios::sync_with_stdio` "allows the standard streams to
operate independently of the standard C streams"
([ios.members.static]); `cin.tie(nullptr)` stops `cin` from flushing
`cout` before every input operation.

**Use when.**

- A program reads or writes large volumes through `std::cin` and
  `std::cout`, the profile shows stream code, and no C `stdio` calls
  touch the same streams.

**Do not use when.**

- The program also uses `printf`/`puts`/`scanf` on stdout or stdin:
  the order between the two APIs is no longer guaranteed.
- Any I/O has already happened: the call's effect is then
  implementation-defined.
- Interactive prompts rely on `cin` flushing `cout`: keep the tie.

**Example.**

```cpp
int main() {
  std::ios::sync_with_stdio(false); // first statement, before any I/O
  std::cin.tie(nullptr);
  // ... std::cout << ... << '\n';
}
```

Runnable: `assets/examples/constructs/io.cpp` (`print-nosync`).

**Cost removed.** No measured difference for output on libc++:
`print-newline` 46.3 ms ± 5.0 versus `print-nosync` 45.0 ms ± 3.8. The
large gains reported for this idiom come from other standard libraries
and from input loops, so measure the target library before claiming
one.

**Verify.**

1. `verify.sh verify` checks identical bytes.
1. `verify.sh io`; report the result, even a tie.

## Build text in a buffer and write once

**Definition.** Format many records into one `std::string` and pass it
to one `fwrite` (or `write`) per chunk, instead of one stream or `FILE*`
call per record.

**Use when.**

- Output is the bottleneck and records are small (logs, CSV, numbers
  per line).

**Do not use when.**

- Partial output must survive a crash, or the consumer reads line by
  line in real time.
- The whole output is too large to hold in memory: flush in bounded
  chunks (the example writes every 32 KiB).

**Example.**

```cpp
std::string buf;
buf.reserve(1 << 16);
for (long i = 0; i < rows; ++i) {
  std::format_to(std::back_inserter(buf), "row {}\n", i);
  if (buf.size() > (1 << 15)) {
    std::fwrite(buf.data(), 1, buf.size(), stdout);
    buf.clear();
  }
}
std::fwrite(buf.data(), 1, buf.size(), stdout);
```

Runnable: `assets/examples/constructs/io.cpp` (`print-format-to`).

**Cost removed.** Measured: `print-format-to` 16.6 ms ± 3.9 versus
`print-printf` 28.0 ms ± 7.9 and `print-newline` 46.3 ms ± 5.0.

**Verify.**

1. `verify.sh verify` checks identical bytes (`cksum`).
1. `verify.sh io`.

## std::print

**Definition.** `std::print(fmt, args...)` (C++23, [print.fun]) formats
with `std::format` rules and writes to `stdout`. libc++ lists
P2093R14 complete since version 18 ([libc++ C++23 status][libcxx-23]).

**Use when.**

- Output volume is modest and you want type safety over `printf` (no
  format/argument mismatch) or readability over `iostream` chains.

**Do not use when.**

- It is the hot output path of a line-oriented program on libc++:
  libc++ 21.1's `<print>` formats each call into a temporary
  `std::string` and checks on every call whether the stream is a
  terminal (`__print::__is_terminal`). Measured: `print-print` 107.3 ms ± 16.1
  (system 38.2 ms) versus `print-printf` 28.0 ms and `print-format-to`
  16.6 ms. Use the buffer card instead.
- The deployment target is older than the SDK's availability markup
  allows: compile once with the real `-mmacosx-version-min` to check.

**Example.**

```cpp
std::print("row {}\n", i);
```

Runnable: `assets/examples/constructs/io.cpp` (`print-print`).

**Cost removed.** None on this machine: std::print was the slowest
printer measured. Use it for correctness and readability, not speed.

**Verify.**

1. `verify.sh verify` checks identical bytes.
1. `verify.sh io`.

## std::format_to into a reused buffer

**Definition.** `std::format_to(out, fmt, args...)` (C++20,
[format.functions]) writes formatted output through an output iterator;
with `std::back_inserter` into a reserved `std::string` it appends
without temporaries. `std::format` returns a new `std::string` per
call.

**Use when.**

- Code builds text with `std::ostringstream` or by concatenating
  repeated `std::format`/`std::to_string` results.

**Do not use when.**

- Locale-specific formatting is required: `std::format` is
  locale-independent unless the `L` option is used.
- The format string is not a compile-time constant: use
  `std::vformat_to` with `std::make_format_args`. A runtime string is
  checked only at run time and throws `std::format_error`.

**Example.**

```cpp
std::string out;
out.reserve(v.size() * 21);
auto it = std::back_inserter(out);
for (auto x : v) it = std::format_to(it, "{},", x);
```

Runnable: `assets/examples/constructs/io.cpp`.

**Cost removed.** Measured: `ALLOC format-to-vs-ostringstream: 11 -> 1`
(1002 numbers); time 51.1 -> 31.9 µs.

**Verify.**

1. `verify.sh verify` compares the text with three other formatters.
1. The `ALLOC` line and `verify.sh time format-to`.

## std::to_chars for numbers to text

**Definition.** `std::to_chars(first, last, value)` (C++17,
[charconv.to.chars]) writes a number into a caller buffer without
allocation, locale, or exceptions. For floating point without a
precision, it writes the shortest text that `from_chars` parses back to
the same value. When the buffer is too small it returns
`errc::value_too_large`.

**Use when.**

- A hot loop converts numbers to text with `std::to_string`,
  `snprintf`, or `std::ostringstream`.

**Do not use when.**

- The output must follow `printf`'s `%g` or a locale's digit grouping:
  `%g` rounds to 6 significant digits, so the shortest form differs
  (`3.141592653589793` vs `3.14159`, `5e-324` vs `4.94066e-324`).
- The deployment target is older than the SDK's availability markup:
  with the macOS 26.5 SDK, `to_chars` for `double` is "introduced in
  macOS 13.3" (a compile error with `-mmacosx-version-min=13.0`).
- `long double` is needed: libc++ does not implement it, which is why
  `__cpp_lib_to_chars` is undefined in libc++ 21.1
  ([libc++ C++17 status][libcxx-17]).

**Example.**

```cpp
char buf[24];
for (auto x : v) {
  auto const [end, ec] = std::to_chars(buf, buf + sizeof buf, x);
  out.append(buf, end); // 24 bytes fit any 64-bit integer
  out += ',';
}
```

Runnable: `assets/examples/constructs/io.cpp`.

**Cost removed.** Measured: `ALLOC to-chars-vs-ostringstream: 11 -> 1`,
time 49.8 -> 9.3 µs; `ALLOC to-chars-vs-to-string: 10 -> 1`, time
15.8 -> 9.1 µs (1000 numbers). Shortest doubles:
`0.1,-0,1e+300,5e-324,3.141592653589793`.

**Verify.**

1. `verify.sh verify` compares four formatters and round-trips the
   doubles through `from_chars`, including the sign of `-0.0`.
1. The `ALLOC` lines and `verify.sh time to-chars`.

## std::from_chars for text to numbers

**Definition.** `std::from_chars(first, last, value)` parses the "C"
locale form of `strtol`/`strtod` without allocation or exceptions
([charconv.from.chars]); it does not skip whitespace, rejects a leading
`+`, sets `ec = errc::invalid_argument` with `ptr == first` on no
match, and `errc::result_out_of_range` on overflow.

**Use when.**

- A hot loop parses numbers with `std::stol`/`std::stoi`,
  `std::istringstream`, or `sscanf`.

**Do not use when.**

- Inputs may carry leading spaces or `+` that the old parser accepted:
  handle them explicitly or the rewrite rejects valid data
  (`verify.sh verify` asserts both rejections).
- Code relied on `std::stol` throwing: check both `ec` and `ptr` to keep
  the same error behavior. Checking only `ec` accepts `"3a"` as 3.
- The deployment target is older than macOS 26.0 and the value is
  `double`: the 26.5 SDK marks floating `from_chars` "introduced in
  macOS 26.0". Integer overloads have no such restriction here.

**Example.**

```cpp
long v = 0;
auto const [p, ec] = std::from_chars(x.data(), x.data() + x.size(), v);
if (ec != std::errc{} || p != x.data() + x.size()) {
  // same error path the old parser had
}
```

Runnable: `assets/examples/constructs/io.cpp`.

**Cost removed.** Parsing overhead, not allocation for short inputs
(`ALLOC from-chars-vs-stol: 0 -> 0`, strings fit the SSO buffer).
Measured time: `std::stol` 25.0 -> 10.9 µs; `std::istringstream`
96.2 -> 11.3 µs (1000 numbers).

**Verify.**

1. `verify.sh verify` compares sums across three parsers and checks
   `" 42"`, `"+42"`, and overflow behavior.
1. `verify.sh time from-chars`.

[ostream.manip]: https://eel.is/c++draft/ostream.manip
[ios.members.static]: https://eel.is/c++draft/ios.members.static
[print.fun]: https://eel.is/c++draft/print.fun
[libcxx-23]: https://libcxx.llvm.org/Status/Cxx23.html
[format.functions]: https://eel.is/c++draft/format.functions
[charconv.to.chars]: https://eel.is/c++draft/charconv.to.chars
[libcxx-17]: https://libcxx.llvm.org/Status/Cxx17.html
[charconv.from.chars]: https://eel.is/c++draft/charconv.from.chars
[narrow.stream.objects]: https://eel.is/c++draft/narrow.stream.objects
