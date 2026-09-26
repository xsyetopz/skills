# Container, string, and allocator constructs

Cards that remove allocations, rehashes, repeated hashing, element
moves, and pointer chasing from container and string code. Pairs live in
[`constructs/containers.cpp`](../assets/examples/constructs/containers.cpp).
`verify.sh verify` checks equal results (including empty input, embedded
NUL, non-ASCII bytes, and missing keys), then asserts the counted
benefit.

Measured numbers are machine-specific: Apple M1 Max, macOS 27.0 arm64,
Apple clang 21.0.0, libc++ 21.1, `-std=c++23 -O2`. Counts come from
`verify.sh verify`; times are medians from `verify.sh time` on a shared
machine.

## Contents

- vector::reserve
- shrink_to_fit
- clear() to reuse a buffer
- Short string optimization capacity
- string_view for substrings
- string_view for read-only text parameters
- span for read-only sequence parameters
- unordered_map::reserve
- try_emplace for a single lookup
- Heterogeneous lookup with a transparent hash
- Hash map instead of an ordered map for point lookups
- Sorted vector with lower_bound
- std::flat_map
- pmr::monotonic_buffer_resource
- std::erase_if instead of erase in a loop

## vector::reserve

**Definition.** `reserve(n)` makes `capacity() >= n`; "No reallocation
shall take place during insertions that happen after a call to
reserve() until an insertion would make the size of the vector greater
than the value of capacity()" ([vector.capacity]).

**Use when.**

- The final size or a tight upper bound is known before a
  `push_back`/`emplace_back` loop (`input.size()`, a counted loop, a
  header field).

**Do not use when.**

- The call would be `reserve(size() + 1)` inside the loop: each call may
  reallocate to the exact size, which destroys the geometric growth that
  makes `push_back` amortized constant.
- The bound comes from untrusted input: clamp it first, or a hostile
  length becomes a huge allocation or `std::length_error`.
- Code keeps pointers or iterators into the vector across insertions
  and uses them after `size()` passes `capacity()`: reallocation
  invalidates them. Measured: `INVALIDATE reserve: data() moved after
  exceeding capacity: yes`.

**Example.**

```cpp
std::vector<long> squares_candidate(int n) {
  std::vector<long> v;
  v.reserve(static_cast<std::size_t>(n));
  for (int i = 0; i < n; ++i) v.push_back(long{i} * i);
  return v;
}
```

Runnable: `assets/examples/constructs/containers.cpp`.

**Cost removed.** Growth reallocations and element relocation. Measured:
`ALLOC reserve: 11 -> 1` (n = 1000); time 886 -> 542 ns.

**Verify.**

1. `verify.sh verify` compares n = 0 and n = 1000 outputs, then `ALLOC`.
1. `verify.sh time reserve`.

## shrink_to_fit

**Definition.** "shrink_to_fit is a non-binding request to reduce
capacity() to size()" ([vector.capacity]). If it reallocates, the cost
is linear and all iterators and references are invalidated.

**Use when.**

- A long-lived vector (a cache, a loaded table) grew far beyond its
  final size, and memory footprint is the metric.

**Do not use when.**

- The vector will grow again: the next insertion reallocates.
- The call sits inside a loop: every call can allocate and copy.
- Portable code depends on the capacity becoming exactly `size()`: the
  request is non-binding. Check `capacity()` after the call.

**Example.**

```cpp
std::vector<long> v;
v.reserve(4096);
v.resize(10);
v.shrink_to_fit(); // libc++ 21.1 here: capacity 4096 -> 10
```

Runnable: `assets/examples/constructs/containers.cpp`.

**Cost removed.** Retained memory. Measured:
`CAPACITY shrink-to-fit: 4096 -> 10 elements (1 alloc)`: 32 KiB of
`long` capacity released at the cost of one allocation and copy.

**Verify.**

1. `verify.sh verify` prints the capacity line and checks `size()`.
1. Measure the application's resident memory before and after with
   `/usr/bin/time -l ./app`; on this machine it prints a
   `maximum resident set size` line (`-l` option of macOS `time(1)`).

## clear() to reuse a buffer

**Definition.** `vector::clear()` destroys the elements and keeps the
capacity, so a buffer hoisted out of a loop and cleared each iteration
is allocated only while it grows.

**Use when.**

- A temporary vector or string is created per loop iteration (per line,
  request, or frame) and discarded at its end.

**Do not use when.**

- One outlier iteration makes the buffer huge and the loop is
  long-lived: the capacity stays. Call `shrink_to_fit` after outliers.
- Each iteration moves the contents out of the loop: the moved-from
  buffer has no capacity left to reuse.

**Example.**

```cpp
std::vector<std::string_view> fields; // outside the loop
for (auto const &line : lines) {
  fields.clear(); // keeps capacity
  split_into(fields, line);
  widest = std::max(widest, fields.size());
}
```

Runnable: `assets/examples/constructs/containers.cpp`.

**Cost removed.** Per-iteration allocations. Measured:
`ALLOC clear-reuse: 257 -> 4` (65 lines, one empty).

**Verify.**

1. `verify.sh verify` compares widths including the empty line.
1. The `ALLOC clear-reuse` line.

## Short string optimization capacity

**Definition.** libc++ stores short strings inside the `std::string`
object without a heap allocation (an implementation technique, not a
standard requirement). The limit is `std::string{}.capacity()`.

**Use when.**

- You choose a key or token representation for hot maps and vectors:
  keys at or below the limit cost no allocation to construct or copy.
- A string change shows no allocation difference for short inputs, and
  you need to explain why.

**Do not use when.**

- You assume the same limit in another library: libstdc++ and MSVC use
  different layouts. Measure on the target library.
- You expect moves to be free: moving a short string copies its bytes
  (there is no pointer to steal).

**Example.**

```cpp
std::printf("%zu\n", std::string{}.capacity()); // 22 here
std::string a(22, 'k'); // no allocation
std::string b(23, 'k'); // one allocation
```

Runnable: `assets/examples/constructs/containers.cpp`.

**Cost removed.** Measured: `SSO: std::string{}.capacity() = 22; largest
length without allocation = 22`; `ALLOC sso-boundary: 1 -> 0` (23 versus
22 characters). This also explains `ALLOC from-chars-vs-stol: 0 -> 0`
in the io cards.

**Verify.**

1. `verify.sh verify` finds the boundary by counting allocations for
   lengths 0 to 63.
1. Rerun on the deployment standard library before relying on it.

## string_view for substrings

**Definition.** `std::string_view` is a non-owning pointer and length;
`string_view::substr` returns another view in constant time, while
`std::string::substr` allocates a new string when the piece exceeds the
SSO capacity ([string.view]).

**Use when.**

- Code parses or tokenizes text that stays alive and unmodified while
  the pieces are in use (split, trim, prefix checks).

**Do not use when.**

- A view is stored beyond the lifetime of its `std::string`, or the
  string is modified or reallocated while the view exists: reads then
  touch freed memory. `std::string_view v = make_key(7);` dangles at the
  end of the statement; `standalone/dangling.cpp` shows ASan reporting
  `heap-use-after-free`.
- The result goes to a C API that needs a terminating NUL: a view is not
  NUL-terminated.

**Example.**

```cpp
std::vector<std::size_t> field_lengths_candidate(std::string_view text) {
  std::vector<std::size_t> out;
  std::size_t start = 0;
  while (true) {
    auto const end = text.find(':', start);
    auto const n = end == text.npos ? text.size() - start : end - start;
    out.push_back(text.substr(start, n).size()); // no copy
    if (end == text.npos) break;
    start = end + 1;
  }
  return out;
}
```

Runnable: `assets/examples/constructs/containers.cpp`.

**Cost removed.** One allocation per field above the SSO capacity.
Measured: `ALLOC string-view-substr: 39 -> 7` (33 fields of 30 bytes);
time 1217 -> 431 ns.

**Verify.**

1. `verify.sh verify` compares empty text, embedded NUL (`"a\0:b"`
   gives `{2, 1}`), and a two-byte UTF-8 tail (byte lengths).
1. `verify.sh sanitize` and `verify.sh diagnose` (`-Wdangling-gsl`).

## string_view for read-only text parameters

**Definition.** A `std::string const&` parameter forces callers holding
a `char const*` or a literal to construct a temporary `std::string`; a
`std::string_view` parameter binds to all of them without allocation.

**Use when.**

- A function only reads its text argument, and callers pass literals,
  `char const*`, or substrings.

**Do not use when.**

- The function passes the text to an API that needs `c_str()` (a
  NUL-terminated string): converting back allocates again.
- The function stores the text: take `std::string` by value and move
  it (see the sink-parameter card in `objects.md`).

**Example.**

```cpp
bool is_admin_candidate(std::string_view name) {
  return name.starts_with("administrator-account-");
}
// baseline: bool is_admin_baseline(std::string const &name)
```

Runnable: `assets/examples/constructs/containers.cpp`.

**Cost removed.** Measured: `ALLOC string-view-param: 1 -> 0` per call
with a 23-byte `char const*` argument.

**Verify.**

1. `verify.sh verify` checks that both return `true`.
1. `rg -n 'std::string const ?&' src/` lists remaining candidates.

## span for read-only sequence parameters

**Definition.** `std::span<T const>` (C++20, [views.span]) is a pointer
and length over contiguous elements; it binds to `std::vector`,
`std::array`, C arrays, and pointer ranges without copying.

**Use when.**

- A function takes `std::vector<T> const&` but callers hold arrays,
  other contiguous containers, or sub-ranges and copy them into a
  vector to call it.

**Do not use when.**

- The data is not contiguous (`std::deque`, `std::list`).
- The span outlives the container or survives a reallocation (same
  dangling rules as `string_view`).

**Example.**

```cpp
long sum_candidate(std::span<long const> v) {
  return std::accumulate(v.begin(), v.end(), 0L);
}
std::array<long, 256> data{};
sum_candidate(data); // baseline: sum_baseline(std::vector(data...))
```

Runnable: `assets/examples/constructs/containers.cpp`.

**Cost removed.** Measured: `ALLOC span-param: 1 -> 0` per call.

**Verify.**

1. `verify.sh verify` checks the sum `256 * 257 / 2`.
1. The `ALLOC span-param` line.

## unordered_map::reserve

**Definition.** `a.reserve(n)` has the effect of
`a.rehash(ceil(n / a.max_load_factor()))` ([unord.req]), so `n`
insertions do not trigger rehashes.

**Use when.**

- The number of keys is known before bulk insertion.

**Do not use when.**

- The count is a loose upper bound on a long-lived map: the bucket
  array stays at that size.
- You expect node allocations to disappear: `std::unordered_map` still
  allocates one node per element.

**Example.**

```cpp
std::unordered_map<long, long> m;
m.reserve(static_cast<std::size_t>(n));
for (int i = 0; i < n; ++i) m.emplace(i, i);
```

Runnable: `assets/examples/constructs/containers.cpp`.

**Cost removed.** Rehashes only. Measured:
`ALLOC unordered-reserve: 1010 -> 1001` (1000 nodes remain); time
25.7 -> 23.4 µs, a small gain because node allocation dominates.

**Verify.**

1. `verify.sh verify` compares the maps.
1. `verify.sh time unordered-reserve`.

## try_emplace for a single lookup

**Definition.** `try_emplace(k, args...)` (C++17,
[unord.map.modifiers]) looks the key up once and constructs the value
only if the key is absent; it returns the iterator either way.
`find` followed by `emplace` or `operator[]` hashes twice.

**Use when.**

- Code does `if (m.find(k) == m.end()) m.emplace(k, v); else m[k]...`
  or `if (!m.contains(k))` followed by an insert.
- The mapped type must not be default-constructed, which rules out
  `operator[]`: pass the constructor arguments to `try_emplace`.

**Do not use when.**

- The code already uses an ordered `std::map` with a hint iterator
  correctly (`emplace_hint` after `lower_bound`).

**Example.**

```cpp
for (auto const &w : words) {
  auto [it, inserted] = m.try_emplace(w, 0);
  it->second += 1;
}
```

Runnable: `assets/examples/constructs/containers.cpp`.

**Cost removed.** One hash and bucket probe per operation. Measured:
`HASHES try-emplace: 599 -> 351` (300 words, 50 distinct). 300 of the
351 are one per word; the other 51 happen inside libc++ on the 50
inserting calls and were not investigated.

**Verify.**

1. `verify.sh verify` compares the two count maps.
1. The `HASHES` line from the counting hasher.

## Heterogeneous lookup with a transparent hash

**Definition.** Since C++20 ([P0919R3][p0919], [P1690R1][p1690]),
`unordered_map::find`, `count`, `contains`, and `equal_range` accept
any key type when both `Hash::is_transparent` and `Pred::is_transparent`
exist; a `std::string_view` probe then needs no temporary
`std::string`. libc++ 21.1 defines
`__cpp_lib_generic_unordered_lookup` as `201811L`.

**Use when.**

- Lookups into a `std::unordered_map<std::string, V>` use
  `string_view`, `char const*`, or substrings and build
  `std::string(key)` to do it.

**Do not use when.**

- The hash of the probe type can differ from the hash of the stored
  type: the transparent hash must return the same value for equal
  strings, or lookups silently miss.
- Insertion is the hot operation: heterogeneous `try_emplace`,
  `operator[]`, `insert_or_assign`, and `at` are added by
  [P2363R5][p2363] for the C++26 working draft, not C++20 or C++23.

**Example.**

```cpp
struct StringHash {
  using is_transparent = void;
  std::size_t operator()(std::string_view s) const {
    return std::hash<std::string_view>{}(s);
  }
};
using HeteroMap =
    std::unordered_map<std::string, long, StringHash, std::equal_to<>>;
auto it = map.find(std::string_view{"key"}); // no allocation
```

Runnable: `assets/examples/constructs/containers.cpp`.

**Cost removed.** One allocation per lookup for keys above the SSO
capacity. Measured: `ALLOC heterogeneous-lookup: 65 -> 0`.

**Verify.**

1. `verify.sh verify` includes a missing key and compares sums.
1. The `ALLOC` line.

## Hash map instead of an ordered map for point lookups

**Definition.** `std::map` is a node-based balanced tree (logarithmic
lookup through pointer chasing); `std::unordered_map` hashes to a bucket
(average constant-time lookup, [unord.req]).

**Use when.**

- The profile shows `std::map::find` and the code never uses ordering
  (`lower_bound`, ordered iteration, first/last element).

**Do not use when.**

- Iteration order is observable (output, serialization, tests).
- Keys come from untrusted input and the hash is predictable:
  collision attacks degrade lookups to linear time.
- The map is small and built once: a sorted vector (next cards) avoids
  the allocation per node.

**Example.**

```cpp
std::unordered_map<long, long> um;
for (auto k : keys) um.emplace(k, k * 2);
auto const it = um.find(key);
```

Runnable: `assets/examples/constructs/containers.cpp`.

**Cost removed.** Tree traversal. Measured, 1000 keys, 3000 probes (a
third hit): `std::flat_map` 37.6 µs -> `std::unordered_map` 9.2 µs;
`std::map` measured 43.0 µs.

**Verify.**

1. `verify.sh verify` checks that every structure returns the same sum.
1. `verify.sh time lookup`.

## Sorted vector with lower_bound

**Definition.** A `std::vector<std::pair<K, V>>` sorted by key and
searched with `std::lower_bound` ("at most log2(last - first) + O(1)
comparisons", [lower.bound]) stores all entries contiguously.

**Use when.**

- The table is built once (or rarely), read many times, and needs
  ordered iteration or range queries.

**Do not use when.**

- Inserts and erases interleave with lookups: each is linear.
- Nothing handles duplicate keys: before sorting, decide whether to keep
  the first, keep the last, or reject duplicates.

**Example.**

```cpp
auto const it = std::lower_bound(
    v.begin(), v.end(), k,
    [](auto const &e, long key) { return e.first < key; });
bool const hit = it != v.end() && it->first == k;
```

Runnable: `assets/examples/constructs/containers.cpp`.

**Cost removed.** Node allocations and pointer chasing. Measured:
`ALLOC sorted-vector-build: 1000 -> 1` versus `std::map`; lookups
43.0 -> 35.1 µs.

**Verify.**

1. `verify.sh verify` compares hits and misses with `std::map`.
1. `verify.sh time lookup-map-vs-sorted-vector`.

## std::flat_map

**Definition.** `std::flat_map` (C++23, [flat.map]) is an ordered
associative container adaptor over two sorted sequence containers (keys
and values, `std::vector` by default). libc++ ships it complete since
version 20 ([libc++ C++23 status][libcxx-23]); libc++ 21.1 defines
`__cpp_lib_flat_map` as `202207L`.

**Use when.**

- The sorted-vector card applies and you want a map interface (`find`,
  `operator[]`, `lower_bound`) instead of hand-written comparisons.
- The map is bulk-built from sorted unique data:
  `std::flat_map(std::sorted_unique, keys, values)` skips the sort.

**Do not use when.**

- Single-element inserts or erases are frequent: each shifts both
  vectors (linear) and invalidates iterators.
- The deployment toolchain's library lacks it: check
  `__cpp_lib_flat_map` from `<version>` on that toolchain (libc++
  before 20 has no `<flat_map>`).
- `sorted_unique` is passed with unsorted or duplicate keys: that is a
  precondition violation, not a checked error.

**Example.**

```cpp
std::flat_map<long, long> m(std::sorted_unique, std::move(keys),
                            std::move(values));
auto const it = m.find(k);
```

Runnable: `assets/examples/constructs/containers.cpp`.

**Cost removed.** Measured: `ALLOC flat-map-build: 1000 -> 3` versus
`std::map`; lookups 44.6 -> 37.6 µs. It matched the sorted vector
within noise.

**Verify.**

1. `verify.sh verify` compares hits and misses with `std::map`.
1. `verify.sh time lookup-map-vs-flat-map`.

## pmr::monotonic_buffer_resource

**Definition.** "A monotonic_buffer_resource is a special-purpose memory
resource intended for very fast memory allocations in situations where
memory is used to build up a few objects and then is released all at
once when the memory resource object is destroyed"
([mem.res.monotonic.buffer]); `deallocate` does nothing. `std::pmr`
containers take it as their allocator.

**Use when.**

- A request, frame, or parse builds many short-lived allocations that
  all die together, and the profile shows `malloc`/`free`.

**Do not use when.**

- Objects outlive the resource: they dangle when it is destroyed.
- The workload frees and reallocates repeatedly within one arena
  lifetime: memory only grows ("increases monotonically until its
  destruction").
- Several threads share it: it is not synchronized. Use
  `synchronized_pool_resource` or one arena per thread.
- `pmr` containers mix with plain ones: copying a `std::pmr::string`
  into a `std::string` allocates normally, and `pmr` types are distinct
  types in APIs.

**Example.**

```cpp
std::array<std::byte, 16384> buffer;
std::pmr::monotonic_buffer_resource arena(
    buffer.data(), buffer.size(), std::pmr::null_memory_resource());
std::pmr::vector<std::pmr::string> parts(&arena);
for (int i = 0; i < n; ++i) parts.emplace_back(40, 'a');
```

Runnable: `assets/examples/constructs/containers.cpp`.

**Cost removed.** Heap allocations for the request. Measured:
`ALLOC pmr-monotonic: 71 -> 0` (64 strings of 40 bytes); time
1643 -> 482 ns. With `null_memory_resource()` upstream, an overflow
throws `std::bad_alloc` (`PMR overflow ... bad_alloc thrown`) instead of
silently using the heap; drop that argument to allow fallback.

**Verify.**

1. `verify.sh verify` compares totals and checks the overflow throw.
1. `verify.sh sanitize` for lifetime errors.

## std::erase_if instead of erase in a loop

**Definition.** `std::erase_if(vector, pred)` (C++20, [vector.erasure])
is the erase-remove idiom: one pass that moves each kept element at
most once, then one tail erase. `v.erase(it)` in a loop shifts the whole
tail on every removal (quadratic moves).

**Use when.**

- A loop calls `erase(it)` on a `std::vector`, `std::string`, or
  `std::deque` for every matching element.

**Do not use when.**

- The loop also inspects neighbours or mutates other elements based on
  what was removed: the predicate sees only one element.
- The rewrite is an index loop with `erase(begin() + i)` and `++i`: it
  skips the element after each removal, so adjacent matches survive.

**Example.**

```cpp
std::erase_if(v, [](h::Item const &x) { return x.value == 0; });
// baseline: for (it...) if (it->value == 0) it = v.erase(it); else ++it;
```

Runnable: `assets/examples/constructs/containers.cpp`.

**Cost removed.** Element moves. Measured:
`MOVES erase-if: 135150 -> 600` (900 elements, every third removed);
time 7.95 -> 0.58 µs.

**Verify.**

1. `verify.sh verify` compares the vectors (order preserved, 600 left).
1. The `MOVES` line.

[vector.capacity]: https://eel.is/c++draft/vector.capacity
[string.view]: https://eel.is/c++draft/string.view
[views.span]: https://eel.is/c++draft/views.span
[unord.req]: https://eel.is/c++draft/unord.req
[unord.map.modifiers]: https://eel.is/c++draft/unord.map.modifiers
[p0919]: https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2018/p0919r3.html
[p1690]: https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2019/p1690r1.html
[p2363]: https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2023/p2363r5.html
[lower.bound]: https://eel.is/c++draft/lower.bound
[flat.map]: https://eel.is/c++draft/flat.map
[libcxx-23]: https://libcxx.llvm.org/Status/Cxx23.html
[mem.res.monotonic.buffer]: https://eel.is/c++draft/mem.res.monotonic.buffer
[vector.erasure]: https://eel.is/c++draft/vector.erasure
