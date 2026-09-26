# Code-generation constructs

Cards that change the machine code of a hot call or loop. Pairs live in
[`constructs/codegen.cpp`](../assets/examples/constructs/codegen.cpp);
the hardening program is
[`standalone/hardening.cpp`](../assets/examples/standalone/hardening.cpp).
`verify.sh verify` proves equal results; `verify.sh asm` asserts the
instruction patterns per `extern "C"` symbol; `verify.sh time` times
the pairs.

Measured numbers are machine-specific: Apple M1 Max, macOS 27.0 arm64,
Apple clang 21.0.0, libc++ 21.1, `-std=c++23 -O2`; times are medians
from `verify.sh time` on a shared machine (1000-element inputs unless
stated). Several cards record no difference or a slowdown; those are
findings, not harness failures.

## Contents

- Templates instead of virtual dispatch
- CRTP for static polymorphism
- std::variant with std::visit
- std::variant with get_if
- final for devirtualization
- Template callable instead of std::function
- constexpr lookup table
- consteval for guaranteed compile-time values
- likely and unlikely attributes
- std::expected for frequent failures
- Exceptions for rare failures
- libc++ hardening mode
- std::sort instead of std::stable_sort
- partial_sort for top-k
- Lazy ranges views instead of intermediate containers

## Templates instead of virtual dispatch

**Definition.** A virtual call goes through the vtable (`blr` on arm64)
and blocks inlining; a template instantiated for the concrete type calls
directly, so the body can inline and vectorize.

**Use when.**

- A hot loop calls a virtual function on objects whose concrete type is
  known at the call site, or a container holds one type only.

**Do not use when.**

- The set of types is open (plugins, types defined by other modules),
  or the requirement is a heterogeneous container.
- Many types times many templated functions would grow the binary and
  instruction-cache footprint: every instantiation adds code. Check size
  with `size -m` or `ls -l` on the binary.

**Example.**

```cpp
template <class T> long template_total_impl(std::vector<T> const &v) {
  long s = 0;
  for (auto const &x : v) s += x.area(); // direct, inlinable
  return s;
}
// baseline: for (auto const &p : boxed) s += p->area(); // blr
```

Runnable: `assets/examples/constructs/codegen.cpp`.

**Cost removed.** Indirect calls. Measured:
`ASM virtual_total_baseline: 1 line(s) match /blr/`,
`template_total_candidate: 0`; time 998 -> 332 ns. The baseline also
reads through `std::unique_ptr` (one pointer load per element), so the
time difference combines dispatch and layout.

**Verify.**

1. `verify.sh verify` checks that every dispatch form returns the same
   total.
1. `verify.sh asm` asserts `blr` in the baseline and not in the
   candidate.

## CRTP for static polymorphism

**Definition.** A CRTP base class template calls the derived class
through `static_cast<D const*>(this)`, resolved at compile time: no
vtable, no indirect call.

**Use when.**

- A base class supplies shared behavior around a customization point,
  the derived type is always known statically, and the profile shows
  the virtual call.

**Do not use when.**

- Objects of different derived types must live in one container or be
  passed through one non-template interface: `ShapeBase<A>` and
  `ShapeBase<B>` are unrelated types.
- C++23 is available and the only goal is to avoid repeating the
  derived type: explicit object parameters (`this auto const& self`,
  [P0847R7][p0847]) express the same thing with less code.

**Example.**

```cpp
template <class D> struct ShapeBase {
  long area() const { return static_cast<D const *>(this)->area_impl(); }
};
struct CSquare : ShapeBase<CSquare> {
  long side;
  long area_impl() const { return side * side; }
};
```

Runnable: `assets/examples/constructs/codegen.cpp`.

**Cost removed.** Measured: `ASM crtp_total_candidate: 0 line(s) match
/blr/`; time 998 -> 322 ns (same layout caveat as the previous card).

**Verify.**

1. `verify.sh verify` compares totals.
1. `verify.sh asm`.

## std::variant with std::visit

**Definition.** `std::variant<Ts...>` stores one of a closed set of
types inline; `std::visit` calls a visitor for the active alternative.
The standard requires constant-time dispatch for one variant but sets
no mechanism ([variant.visit]).

**Use when.**

- The set of types is closed, objects should live contiguously without a
  heap allocation each, and the visitor is small.

**Do not use when.**

- You expect it to remove the indirect call on libc++: libc++ 21.1
  dispatches through a table of function pointers. Measured:
  `ASM variant_total_candidate: 1 blr`, and time 976 -> 993 ns versus
  the virtual baseline (no difference). Use `get_if` (next card) for
  two or three hot alternatives.
- Alternatives differ greatly in size: every element takes the size of
  the largest one.

**Example.**

```cpp
using AnyShape = std::variant<VSquare, VRect>;
for (auto const &x : v)
  s += std::visit([](auto const &shape) { return shape.area(); }, x);
```

Runnable: `assets/examples/constructs/codegen.cpp`.

**Cost removed.** The per-object heap allocation and pointer load of
`std::unique_ptr<Base>` (not measured separately), but not the indirect
call on this library.

**Verify.**

1. `verify.sh verify` compares totals, including a mixed vector.
1. `verify.sh asm` prints the `blr` count for `variant_total_candidate`
   (recorded, not asserted; it may change with the library version).

## std::variant with get_if

**Definition.** `std::get_if<T>(&v)` returns a pointer to the
alternative if it is active, else `nullptr`. A chain of `get_if` tests
compiles to compares and direct, inlinable code.

**Use when.**

- A variant has few alternatives and the profile shows `std::visit`
  dispatch in a hot loop.

**Do not use when.**

- There are many alternatives or new ones are added often: a missed
  alternative compiles silently into the final `else` branch (here
  `std::get<VRect>` throws `std::bad_variant_access` for any other
  type). `std::visit` with an overload set fails to compile instead.

**Example.**

```cpp
for (auto const &x : v) {
  if (auto const *sq = std::get_if<VSquare>(&x)) s += sq->area();
  else s += std::get<VRect>(x).area();
}
```

Runnable: `assets/examples/constructs/codegen.cpp`.

**Cost removed.** Measured: `ASM variant_index_candidate: 0 line(s) match
/blr/`; time 999 -> 504 ns (second run 998 -> 485 ns) versus the
virtual baseline.

**Verify.**

1. `verify.sh verify` compares totals with `std::visit`.
1. `verify.sh asm` asserts no `blr`.

## final for devirtualization

**Definition.** `final` on a class forbids further derivation, so a
virtual call through a reference or pointer to that class has one
possible target, and clang calls (or inlines) it directly.

**Use when.**

- Hot code calls a leaf class, not meant for derivation, through its own
  type (`FinalSquare&`, not `Shape&`).

**Do not use when.**

- Calls go through the base type (`Shape&`): the dynamic type is
  unknown, so `final` on the derived class does not help.
- Tests or downstream code derive from the class (mocks): `final`
  breaks their build.

**Example.**

```cpp
struct FinalSquare final : Shape {
  long side;
  long area() const override { return side * side; }
};
long final_area_candidate(FinalSquare const &s) { return s.area(); }
```

Runnable: `assets/examples/constructs/codegen.cpp`.

**Cost removed.** Measured: `ASM nonfinal_area_baseline: 1 line(s) match
/blr|br /`, `final_area_candidate: 0` (the call is inlined to a
multiply). Not timed: the single call is below timer resolution.

**Verify.**

1. `verify.sh verify` compares the two areas.
1. `verify.sh asm`.

## Template callable instead of std::function

**Definition.** `std::function<R(Args...)>` type-erases a callable:
calls are indirect, and storing a callable larger than the internal
buffer allocates (the standard only recommends avoiding allocation for
small callables such as a pointer plus member pointer,
[func.wrap.func.con]). A template parameter `F` keeps the concrete type
and lets the call inline.

**Use when.**

- A hot function takes `std::function` only to call it (algorithms,
  visitors, per-element callbacks), and the caller knows the callable.

**Do not use when.**

- The callable is stored in a data structure, crosses an ABI or
  virtual boundary, or is chosen at run time: type erasure is the
  requirement (consider C++26 `std::function_ref`, [P0792R14][p0792],
  or C++23 `std::move_only_function`, [P0288R9][p0288], when the
  library has them).
- Many callers with different lambdas would each instantiate a large
  template.

**Example.**

```cpp
template <class F> long apply_template(std::vector<long> const &v,
                                       F const &f) {
  long s = 0;
  for (auto x : v) s += f(x); // inlined
  return s;
}
// baseline: long apply(std::vector<long> const&,
//                      std::function<long(long)> const &f)
```

Runnable: `assets/examples/constructs/codegen.cpp`.

**Cost removed.** Measured: `ASM apply_function_baseline: 1 line(s) match
/blr/`, `apply_template_candidate: 0`; time 960 -> 333 ns;
`ALLOC std-function-large-capture: 1 -> 0` for a 64-byte capture.
`SBO std::function: largest tested capture without allocation = 16
bytes` (tested 8, 16, 24, 32) on libc++ 21.1.

**Verify.**

1. `verify.sh verify` compares results and prints `ALLOC` and `SBO`.
1. `verify.sh asm`.

## constexpr lookup table

**Definition.** A `static constexpr` table is constant-initialized: the
compiler computes its contents and emits them as data, so no
initialization runs at run time. A function-local `static` initialized
by a non-constant expression is dynamically initialized on first call
behind a thread-safe guard (`__cxa_guard_acquire`) ([stmt.dcl],
[basic.start.static]).

**Use when.**

- A lookup table (CRC, character classes, powers) derives from
  constants.

**Do not use when.**

- You expect a steady-state speedup: after the first call the guard is
  one load and a predictable branch. Measured: time 10.73 -> 10.73 µs for
  4096 bytes (no difference).
- The computation exceeds constant-evaluation limits (clang
  `-fconstexpr-steps`, [Clang user manual][clang-manual]) and fails the
  build: keep it at run time or generate the table offline.

**Example.**

```cpp
constexpr std::array<std::uint32_t, 256> make_crc_table() { /* ... */ }
std::uint32_t crc(char const *p, std::size_t n) {
  static constexpr auto table = make_crc_table(); // data, no guard
  // baseline: static auto const table = make_crc_table_runtime();
}
static_assert(make_crc_table()[1] == 0x77073096U);
```

Runnable: `assets/examples/constructs/codegen.cpp`.

**Cost removed.** The first-call initialization and the guard check.
Measured: `ASM crc_static_baseline: 2 line(s) match /__cxa_guard/`,
`crc_constexpr_candidate: 0`. The `static_assert` also turns a wrong
table into a compile error.

**Verify.**

1. `verify.sh verify` checks the CRC-32 check value `0xCBF43926` for
   `"123456789"` from both.
1. `verify.sh asm`.

## consteval for guaranteed compile-time values

**Definition.** A `consteval` function is an immediate function: every
call must be a constant expression, so it always runs at compile time,
and a call with a run-time argument is ill-formed
([dcl.constexpr], [expr.const]).

**Use when.**

- Hashes, masks, or IDs of string literals must never be computed at
  run time (case labels, table keys), and a silent run-time fallback
  would be a bug.

**Do not use when.**

- You expect different code from a `constexpr` call that the optimizer
  already folds. Measured: `route_runtime_baseline` and
  `route_consteval_candidate` both contain 0 `bl` calls (clang folded
  `fnv1a("GET")` at `-O2` too). The gain is the guarantee.
- The same function must also run on run-time data: keep a `constexpr`
  function and wrap it in a `consteval` one for literals.

**Example.**

```cpp
consteval std::uint64_t key(std::string_view s) { return fnv1a(s); }
switch (fnv1a({p, n})) {
case key("GET"): return 1;
case key("POST"): return 2;
default: return 0;
}
```

Runnable: `assets/examples/constructs/codegen.cpp`;
`assets/examples/standalone/consteval_error.cpp` must not compile.

**Cost removed.** Risk of run-time hashing; no measured time change.

**Verify.**

1. `verify.sh verify` compares routes for `GET`, `POST`, `PUT`, `""`.
1. `verify.sh diagnose` asserts "call to consteval function 'key' is
   not a constant expression".

## likely and unlikely attributes

**Definition.** `[[likely]]` and `[[unlikely]]` (C++20,
[dcl.attr.likelihood]) mark a path as more or less likely; the standard
notes that "Excessive usage of either of these attributes is liable to
result in performance degradation."

**Use when.**

- A profile shows a mispredicted or badly laid out branch, the
  distribution is known and stable (error paths), and a measurement
  after the change confirms a gain.

**Do not use when.**

- No measurement supports it. Measured: marking the 1-in-100 negative
  branch `[[unlikely]]` made the loop slower in three runs; minimums
  1395 -> 1544, 1436 -> 1610, and 1436 -> 1609 ns (one baseline median
  was inflated by load). `-S` shows both versions branch-free (`csel`);
  the attribute changed the unrolling from four independent
  accumulators to one serial chain.
- The data distribution varies by customer or input.

**Example.**

```cpp
if (v[i] < 0) [[unlikely]] {
  s -= v[i] * 3;
} else {
  s += v[i];
}
```

Runnable: `assets/examples/constructs/codegen.cpp`.

**Cost removed.** None here; it measured as a regression.

**Verify.**

1. `verify.sh verify` compares sums.
1. `verify.sh time unlikely`; keep the attribute only if the candidate
   is faster in repeated runs.

## std::expected for frequent failures

**Definition.** `std::expected<T, E>` (C++23, [expected]) carries
either a value or an error in the return value, so the failure path is
an ordinary return instead of a throw the unwinder must process.

**Use when.**

- Failure is a normal outcome on a hot path (parsing user input,
  lookups that miss, validation), and the profile shows
  `__cxa_throw`, `_Unwind_RaiseException`, or `__gxx_personality_v0`.

**Do not use when.**

- Failures are rare: measured with 0 % failures, 559 -> 624 ns, so
  exceptions were faster (next card).
- Errors must cross many layers that do not handle them: every layer
  must then propagate the `expected`, and the compiler does not force
  callers to check it unless `[[nodiscard]]` is used.

**Example.**

```cpp
std::expected<int, std::errc> parse_expected(std::string_view s) {
  int v = 0;
  auto const [p, ec] = std::from_chars(s.data(), s.data() + s.size(), v);
  if (ec != std::errc{}) return std::unexpected(ec);
  if (p != s.data() + s.size())
    return std::unexpected(std::errc::invalid_argument);
  return v;
}
```

Runnable: `assets/examples/constructs/codegen.cpp`.

**Cost removed.** Exception throw and unwind cost. Measured, 100 inputs
with 50 failures: 264 µs -> 487 ns (about 5 µs per throw and catch).

**Verify.**

1. `verify.sh verify` compares both paths on junk, overflow, empty, and
   trailing-garbage inputs.
1. `verify.sh time expected`.

## Exceptions for rare failures

**Definition.** Clang on macOS and Linux uses the Itanium C++ ABI's
table-based exception handling ([Itanium C++ ABI: Exception
Handling][itanium-eh]). The non-throwing path runs no handler setup
code; the cost falls on the throw (allocating the exception object,
two-phase unwinding through tables) and on binary size.

**Use when.**

- Errors are exceptional (I/O failure, corrupt input, out of memory),
  and handling them far up the stack keeps hot code free of error
  checks.

**Do not use when.**

- Failures are frequent (previous card).
- The code compiles with `-fno-exceptions`, or the error crosses a C or
  `noexcept` boundary: a throw that reaches a `noexcept` function calls
  `std::terminate`.

**Example.**

```cpp
int parse_throw(std::string_view s) {
  int v = 0;
  auto const [p, ec] = std::from_chars(s.data(), s.data() + s.size(), v);
  if (ec != std::errc{} || p != s.data() + s.size())
    throw std::invalid_argument("not an int");
  return v;
}
```

Runnable: `assets/examples/constructs/codegen.cpp`.

**Cost removed.** Error checks on the success path. Measured, 100 valid
inputs: throwing version 559 ns, `std::expected` 624 ns.

**Verify.**

1. `verify.sh verify` compares the throwing and `expected` versions.
1. `verify.sh time expected-0pct`.

## libc++ hardening mode

**Definition.** libc++ hardening modes add precondition checks to the
library (`none`, `fast`, `extensive`, `debug`), selected with
`-D_LIBCPP_HARDENING_MODE=_LIBCPP_HARDENING_MODE_FAST` and so on "before
including any headers to avoid ODR issues"; production modes "trap
immediately via a single instruction" ([libc++ hardening][hardening]).
The SDK used here defaults to none (`_LIBCPP_HARDENING_MODE_DEFAULT 2`,
which is `_LIBCPP_HARDENING_MODE_NONE` in `__configuration/hardening.h`).

**Use when.**

- You must decide whether a hardened build is affordable: measure the
  hot paths with and without it instead of turning it off by default.
- A profile of a hardened build shows `brk` blocks in indexing loops:
  restructure the loop (iterate, use `std::span` once) instead of
  disabling hardening globally.

**Do not use when.**

- Translation units of one program would mix modes: that is an ODR
  violation.
- The code indexes with untrusted values: disabling it turns an
  out-of-bounds access from a trap into undefined behavior.

**Example.**

```sh
c++ -std=c++23 -O2 \
  -D_LIBCPP_HARDENING_MODE=_LIBCPP_HARDENING_MODE_FAST \
  standalone/hardening.cpp -o hardening_fast
./hardening_fast oob   # traps on v[4096]
```

Runnable: `assets/examples/standalone/hardening.cpp`.

**Cost removed or added.** Measured: `ASM gather_sum: 0 line(s) match
/brk/` with NONE and `1` with FAST; hyperfine for 20000 passes over a
4096-element gather: NONE 18.3 ms ± 3.2, FAST 32.4 ms ± 2.4 (FAST
1.78 ± 0.34 times slower on this loop; a rerun gave 20.9 versus
33.2 ms, 1.58 ± 0.46). The FAST build traps on the out-of-bounds read;
the NONE build is never run on it.

**Verify.**

1. `verify.sh hardening` checks that both builds compute the same sum
   and that FAST exits nonzero on `oob`.
1. The same mode prints the `brk` counts and the hyperfine comparison.

## std::sort instead of std::stable_sort

**Definition.** `std::stable_sort` keeps equal elements in their input
order and uses a temporary buffer when it can allocate one ("If enough
extra memory is available, N log(N) comparisons. Otherwise, at most
N log²(N) comparisons", [stable.sort]); `std::sort` is not stable and
needs no buffer.

**Use when.**

- The comparison is a total order on the whole value (no two distinct
  elements compare equal), or no consumer cares about tie order.

**Do not use when.**

- Output order of equal keys is observable (UI lists, diffs, tests,
  multi-key sorts done in passes). Measured: `SORT: std::sort reordered
  equal keys: yes` on 2000 records with 1000 distinct keys.
- Ties must be deterministic with `std::sort` and the comparator has no
  tie-breaker: add one first (for example, the original index).

**Example.**

```cpp
std::sort(v.begin(), v.end(), by_key);
// baseline: std::stable_sort(v.begin(), v.end(), by_key);
```

Runnable: `assets/examples/constructs/codegen.cpp`.

**Cost removed.** Measured: `ALLOC sort-not-stable: 1 -> 0`; time
166 -> 59 µs (2000 records).

**Verify.**

1. `verify.sh verify` checks equal key order and that `stable_sort`
   kept ties in input order.
1. `verify.sh time stable-sort`.

## partial_sort for top-k

**Definition.** `std::partial_sort(first, middle, last)` places the
smallest `middle - first` elements, sorted, at the front with about
N log(M) comparisons ([partial.sort]); `std::nth_element` only
partitions around one position (linear on average,
[alg.nth.element]).

**Use when.**

- Code sorts a whole range, then keeps the first k elements, with k much
  smaller than N.

**Do not use when.**

- k is close to N: a full sort is as cheap or cheaper.
- Ties at the k boundary must match the full sort's choice: neither
  algorithm is stable, so the equal element that lands at position k can
  differ. Compare keys, not identities, in tests.

**Example.**

```cpp
std::partial_sort(v.begin(), v.begin() + k, v.end(), std::greater<>{});
v.resize(k);
```

Runnable: `assets/examples/constructs/codegen.cpp`.

**Cost removed.** Comparisons. Measured, 10000 elements, k = 10:
`COMPARES partial-sort-top-k: 150206 -> 10402`; time 145 -> 5.2 µs.

**Verify.**

1. `verify.sh verify` compares the top-10 from both.
1. The `COMPARES` line.

## Lazy ranges views instead of intermediate containers

**Definition.** Range adaptors such as `views::filter`,
`views::transform`, and `views::take` ([range.adaptors]) compose lazily:
iterating the view produces elements on demand, so nothing is
materialized in between and `take(k)` stops the pipeline early.

**Use when.**

- Code builds temporary vectors between pipeline stages, or computes a
  whole stage and then keeps only the first k results.

**Do not use when.**

- The predicate or transform has side effects or is expensive, and the
  view is iterated more than once: it runs again on every iteration
  (`views::filter` also caches its first match on the first `begin()`
  call, so a later iteration starts there even if the elements changed,
  [range.filter.view]).
- The underlying range dies before the view is used: views hold
  references, with the same dangling rules as `string_view`.

**Example.**

```cpp
auto view = v | std::views::filter(is_even) |
            std::views::transform([](long x) { return x * x; }) |
            std::views::take(k);
std::vector<long> out;
out.reserve(k);
std::ranges::copy(view, std::back_inserter(out));
```

Runnable: `assets/examples/constructs/codegen.cpp`.

**Cost removed.** Measured, 1000 inputs, k = 5:
`PREDICATE ranges-lazy: 1000 -> 11`, `ALLOC ranges-lazy: 20 -> 1`; time
2191 -> 33 ns.

**Verify.**

1. `verify.sh verify` compares the outputs.
1. Check the `PREDICATE` and `ALLOC` lines.

[variant.visit]: https://eel.is/c++draft/variant.visit
[func.wrap.func.con]: https://eel.is/c++draft/func.wrap.func.con
[stmt.dcl]: https://eel.is/c++draft/stmt.dcl
[basic.start.static]: https://eel.is/c++draft/basic.start.static
[range.filter.view]: https://eel.is/c++draft/range.filter.view
[dcl.constexpr]: https://eel.is/c++draft/dcl.constexpr
[expr.const]: https://eel.is/c++draft/expr.const
[dcl.attr.likelihood]: https://eel.is/c++draft/dcl.attr.likelihood
[expected]: https://eel.is/c++draft/expected
[itanium-eh]: https://itanium-cxx-abi.github.io/cxx-abi/abi-eh.html
[hardening]: https://libcxx.llvm.org/Hardening.html
[stable.sort]: https://eel.is/c++draft/stable.sort
[partial.sort]: https://eel.is/c++draft/partial.sort
[alg.nth.element]: https://eel.is/c++draft/alg.nth.element
[range.adaptors]: https://eel.is/c++draft/range.adaptors
[p0847]: https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2021/p0847r7.html
[p0792]: https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2023/p0792r14.html
[p0288]: https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2021/p0288r9.html
[clang-manual]: https://clang.llvm.org/docs/UsersManual.html
