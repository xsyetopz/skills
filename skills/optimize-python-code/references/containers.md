# Container and buffer constructs

These cards change the data structure or memory representation, which
usually changes the complexity class: where the FAQ says the large wins are
([programming FAQ][faq-perf]). Each example is a baseline/candidate pair in
[`containers.py`](../assets/examples/constructs/containers.py). `run()` proves
equivalence and a deterministic benefit (comparison calls, traced bytes, or
executed instructions);
[`bench.py`](../assets/examples/constructs/bench.py) times the pair with
pyperf.

Measured numbers are machine-specific: Apple M1 Max, macOS, Homebrew CPython
3.14.7 (GIL build), pyperf 2.10.0 `--fast`, from `sh
assets/examples/verify.sh measure` and its `compare_to --table` output, on a
machine loaded by other jobs. Counts and bytes come from `sh
assets/examples/verify.sh verify`; two consecutive runs printed identical
values. Tier: Executed. `check.Probe` is a value wrapper that counts `==`, `<`,
and `<=` calls, so comparison counts are exact.

Average-case complexities are from the CPython
[time complexity table][complexity]: `x in list` is O(n) and `x in set` or
`key in dict` is O(1) on average. Hash-based operations degrade to O(n) when
every key has the same hash.

## Contents

- set or dict membership instead of list membership
- collections.deque for FIFO queues
- collections.Counter instead of list.count per element
- bisect on a sorted list
- heapq.nsmallest and nlargest for top-k
- heapq.merge for sorted streams
- \_\_slots\_\_
- dataclass(slots=True)
- array.array for homogeneous numbers
- memoryview slices
- bytearray accumulation
- struct.Struct precompiled formats

## set or dict membership instead of list membership

**Definition.** `x in some_list` compares `x` with each element by `is` or
`==` until a match: O(n). `x in some_set` hashes `x` and compares only entries
with a matching hash: O(1) on average
([complexity][complexity]).

**Use when.**

- A profile shows `in`, `list.index`, or `list.remove` on a list inside a
  loop, and the list does not change during the loop.
- The elements are hashable and their `__eq__` agrees with `__hash__`.

**Do not use when.**

- The elements are unhashable (`list`, `dict`): `set()` raises `TypeError`.
- Equality is not hash-consistent (a custom class with a loose `__eq__`): the
  set lookup misses elements the list scan finds.
- Only a handful of lookups follow each construction: building the set is
  O(n) too. Build it once and reuse it.
- Other code needs the order or duplicates: keep the list and add the set
  beside it.

**Example.**

```python
def candidate_known(allowed, queries):
    members = set(allowed)  # requires hashable elements
    return [query in members for query in queries]
```

**Cost removed.** Linear scans. Measured: 2,000 allowed values and 100
queries went from 150,025 to 50 `__eq__` calls. pyperf `set_membership`
(strings): 1.44 ms -> 42.5 us, 33.85x faster.

**Verify.**

1. `sh assets/examples/verify.sh verify` checks hits, misses, and boundary
   values.
1. `METRIC set-membership __eq__ calls` must drop. In the project, count
   with a wrapper like `check.Probe` or time with pyperf.

## collections.deque for FIFO queues

**Definition.** `deque` supports appends and pops at both ends with
"approximately the same O(1) performance in either direction". `list`
"incur[s] O(n) memory movement costs for `pop(0)` and `insert(0, v)`".
Indexing a deque is O(1) at both ends and O(n) in the middle
([collections.deque][deque]).

**Use when.**

- Code pops or inserts at index 0 of a list: BFS queues, sliding windows,
  work queues.
- You need a bounded history: `deque(maxlen=n)` discards from the other end.

**Do not use when.**

- The code slices or indexes into the middle: a deque does not support
  slicing, and middle indexing is O(n).
- Threads use it as a synchronization channel: appends and pops are
  thread-safe, but blocking waits and backpressure need `queue.Queue`.

**Example.**

```python
def candidate_drain(values):
    pending = deque(values)
    out = []
    while pending:
        out.append(pending.popleft())
    return out
```

**Cost removed.** O(n) memory movement per pop. Measured CPU time for 60,000
items: 0.33 s -> 0.0017 s (`verify` asserts at least 5×). pyperf `deque`
(20,000 items): 31.3 ms -> 805 us, 38.92x faster.

**Verify.**

1. `verify.sh verify` checks order preservation and `[]`.
1. `METRIC deque cpu s` must show the ratio. Doubling the input should
   roughly quadruple the baseline.

## collections.Counter instead of list.count per element

**Definition.** `values.count(v)` scans the whole list, so calling it for
every element is O(n²). `Counter(values)` is a `dict` subclass that counts in
one hashed pass ([Counter][counter]).

**Use when.**

- Code computes frequencies with `list.count`, nested loops, or
  `if k in d: d[k] += 1 else: d[k] = 1`.
- The elements are hashable.

**Do not use when.**

- Callers need `KeyError` for a missing key and would receive the
  `Counter` itself: it returns 0 for missing keys. Return `dict(counter)`,
  as the example does.
- The caller relies on an order other than first occurrence: both the
  baseline dict comprehension and `Counter` keep first-seen order.

**Example.**

```python
def candidate_counts(values):
    return dict(Counter(values))
```

**Cost removed.** Quadratic comparisons. Measured: 2,000 values with 40
distinct keys went from 3,999,960 to 3,920 `__eq__` calls. pyperf
`counter` (strings): 46.9 ms -> 74.6 us, 628.36x faster.

**Verify.**

1. `verify.sh verify` compares the `(key, count)` sequences, including order.
1. `METRIC counter __eq__ calls` must drop by orders of magnitude.

## bisect on a sorted list

**Definition.** `bisect_left(a, x)` and `bisect_right(a, x)` binary-search a
sorted sequence in O(log n) comparisons and return insertion points. The
count of items in `[lo, hi)` is `bisect_left(a, hi) - bisect_left(a, lo)`.
The `key=` parameter was added in 3.10 ([bisect][bisect]).

**Use when.**

- A sorted list answers range or rank queries ("how many between",
  "nearest").
- The list is read far more often than it is modified.

**Do not use when.**

- The list is not sorted by the same ordering: bisect silently returns wrong
  answers. Assert sortedness in tests.
- You look up exact values: "for locating specific values, dictionaries are
  more performant" ([bisect][bisect]).
- You insert often: `insort` is O(n) because the "insertion step" dominates.
- The range is closed, `[lo, hi]`: the example's half-open form misses
  the upper end. Use `bisect_right(a, hi) - bisect_left(a, lo)`. The
  oracle checks both forms.

**Example.**

```python
def candidate_in_range(ordered, lo, hi):
    # ordered must be sorted ascending by the same ordering
    return bisect_left(ordered, hi) - bisect_left(ordered, lo)
```

**Cost removed.** The linear scan. Measured, 9,000 values with duplicates:
17,700 -> 28 comparison calls.

**Verify.**

1. `verify.sh verify` checks empty ranges, ranges below the minimum, ranges
   past the maximum, duplicate runs, and the closed-range variant.
1. `METRIC bisect comparison calls` must drop to about 2·log2(n).

## heapq.nsmallest and nlargest for top-k

**Definition.** `heapq.nsmallest(k, it)` streams the input through a heap of
k items: fewer comparisons than a full sort and no copy of the input. The
result equals `sorted(it)[:k]`. These functions "perform best for smaller
values of n"; for larger n use `sorted()`, and for n == 1 use
`min()`/`max()` ([heapq][heapq]).

**Use when.**

- Code sorts a large sequence only to take the first or last k items, with k
  much smaller than the length.
- The input is an iterator too large to hold in memory.

**Do not use when.**

- k is close to the input length: the heap overhead exceeds a sort.
- k == 1: `min(it, key=...)` is simpler and cheaper.
- You need the whole sorted list elsewhere: sort once and slice.

**Example.**

```python
def candidate_top_k(values, k):
    return heapq.nsmallest(k, values)
```

**Cost removed.** Comparisons and the sorted copy. Measured, 10,007 shuffled
values, k = 10: 120,352 -> 10,715 `__lt__` calls. pyperf `nsmallest` (ints):
483 us -> 152 us ± 33 us, 3.18x faster.

**Verify.**

1. `verify.sh verify` checks k = 0, 1, 10, and k larger than the input.
1. `METRIC nsmallest __lt__ calls` must drop.

## heapq.merge for sorted streams

**Definition.** `heapq.merge(*iterables)` lazily merges inputs that are
already sorted. It is "similar to `sorted(itertools.chain(*iterables))`" but
"does not pull the data into memory all at once" ([heapq][heapq-merge]).

**Use when.**

- The inputs are individually sorted: log files by timestamp, sorted run
  files, paginated results.
- The consumer streams the output (writes, reduces, stops early).

**Do not use when.**

- Any input is unsorted: merge does not check, and the output is silently
  unsorted.
- The consumer materializes the output anyway and the inputs are small
  lists: `sorted` is simpler.

**Example.**

```python
def candidate_merged_total(a, b):
    total = 0
    for value in heapq.merge(a, b):  # inputs must each be sorted
        total = total * 31 + value & 0xFFFFFFFF
    return total
```

**Cost removed.** The materialized concatenation and sorted copy. Measured
tracemalloc peak for 400,000 values: 20,791,992 B -> 4,860 B.

**Verify.**

1. `verify.sh verify` checks the fold and that
   `list(merge(a, b)) == sorted(a + b)` on a prefix.
1. `METRIC heapq-merge tracemalloc peak B` must drop and stay flat when the
   input doubles.

## \_\_slots\_\_

**Definition.** A class-level `__slots__ = ("x", "y")` reserves fixed storage
for the named attributes and "prevents the automatic creation of `__dict__`
and `__weakref__`" per instance. The data model says "the space saved over
using `__dict__` can be significant" and that attribute lookup "can be
significantly improved" ([data model][slots]).

**Use when.**

- tracemalloc attributes memory to many small instances of one class
  (records, nodes, points).
- The attribute set is fixed and known when the class is defined.

**Do not use when.**

- Code assigns new attributes dynamically: this raises `AttributeError`.
  Adding `"__dict__"` to the slots allows it but gives back the saving.
- Something weak-references instances and `"__weakref__"` is not in the
  slots.
- A class attribute provides a default for a slotted name: slots are
  descriptors, so the names conflict. Set defaults in `__init__`.
- A subclass omits `__slots__`: its instances regain a `__dict__`.
- Multiple bases have nonempty slot layouts: this raises `TypeError`.
- `functools.cached_property` needs a `__dict__` on the instance
  ([functools][cached-property]).

**Example.**

```python
class SlotPoint:
    __slots__ = ("x", "y")

    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y
```

**Cost removed.** The per-instance dict. Measured tracemalloc peak for 10,000
points: 1,597,304 B -> 1,197,304 B. `sys.getsizeof` of an empty instance is
48 B versus 40 B, which does not count the dict. pyperf `slots`:
2.05 ms -> 1.80 ms, 1.14x faster.

**Verify.**

1. `verify.sh verify` checks equal sums. In the project, run the tests:
   `AttributeError` shows up only on dynamic assignment.
1. `METRIC slots tracemalloc peak B` must drop.

## dataclass(slots=True)

**Definition.** `@dataclass(slots=True)` (3.10+) generates `__slots__` from
the fields and returns a new class. `weakref_slot=True` (3.11+) adds
`__weakref__` ([dataclasses][dataclass]).

**Use when.**

- Many instances of a dataclass are alive at once and the fields are fixed.
- The project's minimum Python version is 3.10 or later.

**Do not use when.**

- The class defines `__slots__` itself: this raises `TypeError`.
- A base class's `__init_subclass__` takes parameters: `slots=True` raises
  `TypeError` (gh-91126, see [dataclasses][dataclass]).
- Code relies on the decorated class object's identity (for example, a
  registry filled inside the class body): `slots=True` returns a different
  class.
- The class uses `functools.cached_property` or dynamic attributes (see the
  `__slots__` card).

**Example.**

```python
@dataclass(frozen=True, slots=True)
class SlotQuote:
    symbol: str
    price: float
```

**Cost removed.** The per-instance dict. Measured tracemalloc peak for 10,000
quotes: 1,205,926 B -> 805,926 B. pyperf `dataclass_slots`:
3.45 ms -> 3.25 ms, 1.06x faster.

**Verify.**

1. `verify.sh verify` checks equal totals.
   `dataclasses.fields(SlotQuote)` lists the same fields as before.
1. `METRIC dataclass-slots tracemalloc peak B` must drop.

## array.array for homogeneous numbers

**Definition.** `array.array(typecode, ...)` stores values as packed C types
("compactly represent an array of basic values"). `'d'` is a C `double`, 8
bytes per item, instead of one pointer plus one float object per element
([array][array]).

**Use when.**

- Large sequences of one numeric type stay in memory: samples, offsets, IDs.
- The values go to or come from binary files or sockets (`tofile`,
  `frombytes`, buffer protocol).

**Do not use when.**

- Values exceed the type: `array('i', [2**40])` raises `OverflowError`
  (observed locally). Pick `'q'` or keep a list.
- Precision would change: `'f'` stores C `float`, so `0.1` reads back as
  `0.10000000149011612` (observed locally). Use `'d'` for Python floats.
- Speed is the goal and the code does per-element Python arithmetic or
  builds the array from a generator: each access boxes a new Python object.
  Measured: building and scanning 100,000 floats was 1.96x slower than a
  list (pyperf row below). The saving is memory only.

**Example.**

```python
def candidate_samples(n):
    samples = array("d", (i * 0.25 for i in range(n)))
    return max(samples, default=0.0)
```

**Cost removed.** Per-element object headers and pointers, not time. Measured
tracemalloc peak for 100,000 floats: 3,201,184 B -> 817,256 B. pyperf `array`:
4.70 ms -> 9.20 ms, 1.96x slower.

**Verify.**

1. `verify.sh verify` checks n = 0, 1, and 100,000 (empty uses `default=`).
1. `METRIC array tracemalloc peak B` must drop.

## memoryview slices

**Definition.** `memoryview(obj)` exposes the buffer of `bytes`,
`bytearray`, `array`, or `mmap` "without copying". Slicing a memoryview is
O(1) and returns another view ([memoryview][memoryview],
[complexity][complexity]).

**Use when.**

- Code slices large `bytes` to parse headers and payloads, or passes chunks
  to `socket.send`, `file.write`, or `struct.unpack_from`.
- tracemalloc shows the copies from those slices.

**Do not use when.**

- A small view of a huge buffer would outlive its use: a view pins the whole
  buffer. Copy with `bytes(view)` when you keep it.
- The source is a `bytearray` resized while a view exists: the resize
  raises `BufferError: Existing exports of data: object cannot be
  re-sized` (observed locally). Release the view with `with memoryview(...)`
  or `.release()`.
- A consumer requires `bytes` (`dict` keys, `bytes` methods such as
  `split`): a view is hashable only when read-only with format `B`, `b`, or
  `c`, and it has none of the `bytes` search or split methods
  ([memoryview][memoryview]).

**Example.**

```python
def candidate_payload_sum(frame: bytes) -> int:
    _magic, length = HEADER.unpack_from(frame)
    with memoryview(frame) as view:
        payload = view[HEADER.size : HEADER.size + length]  # no copy
        return sum(payload[::4096])
```

**Cost removed.** One payload-sized copy. Measured tracemalloc peak for a 1
MiB payload: 1,049,167 B -> 1,021 B.

**Verify.**

1. `verify.sh verify` checks equal results for the header and payload parse.
1. `METRIC memoryview tracemalloc peak B` must drop by about the payload
   size.

## bytearray accumulation

**Definition.** `bytes` is immutable, so `out += chunk` copies the whole
accumulated buffer each time: quadratic. `bytearray` has "an efficient
overallocation mechanism", so `+=` appends in amortized O(len(chunk)).
`b"".join(chunks)` and `io.BytesIO` are the other linear idioms
([sequence note][seq-concat], [programming FAQ][faq-concat]).

**Use when.**

- A loop builds a binary message, file, or frame with `bytes +=`.
- Default to `bytearray` when chunks arrive incrementally; use `b"".join`
  when they are all available at once.

**Do not use when.**

- Callers would receive a bytearray where they need `bytes` (hashable,
  immutable): convert once at the end with `bytes(out)`, one copy, as the
  example does.
- A memoryview of the bytearray is alive while you append: `BufferError`
  (memoryview card).

**Example.**

```python
def candidate_pack(chunks):
    out = bytearray()
    for chunk in chunks:
        out += chunk
    return bytes(out)
```

**Cost removed.** Quadratic copying. Measured CPU time, 20,000 chunks of 32 B:
0.14 s -> 0.00054 s (`verify` asserts at least 10×). pyperf `bytearray`
(20,000 × 4 B): 28.3 ms -> 536 us, 52.78x faster.

**Verify.**

1. `verify.sh verify` checks equality and `[]`.
1. `METRIC bytearray cpu s` must show the ratio.

## struct.Struct precompiled formats

**Definition.** `struct.Struct(fmt)` compiles a format once. "Creating a
Struct object once and calling its methods is more efficient than calling
module-level functions with the same format since the format string is only
compiled once." `iter_unpack(buffer)` yields one tuple per record, and
`unpack_from(buffer, offset)` reads without slicing ([struct][struct]).

**Use when.**

- A loop parses fixed-size binary records with `struct.unpack(fmt,
  data[off:off + n])`.
- Code writes records with `pack_into` into a preallocated `bytearray`.

**Do not use when.**

- The buffer length is not a multiple of `Struct.size`: `iter_unpack` raises
  `struct.error`. If the baseline tolerated a partial tail, handle it
  explicitly.
- A few formats are called rarely: the module-level cache already avoids
  recompiling ([struct][struct]).

**Example.**

```python
RECORD = struct.Struct("<iHf")

def candidate_records(data: bytes):
    return list(RECORD.iter_unpack(data))
```

**Cost removed.** The per-record Python loop, slice copy, and format lookup.
Measured, 5,000 records: 85,029 -> 22 executed instructions. pyperf `struct`:
1.08 ms -> 518 us, 2.08x faster.

**Verify.**

1. `verify.sh verify` checks 5,000 records and `b""`.
1. `METRIC struct executed instructions` must drop.

[array]: https://docs.python.org/3/library/array.html
[bisect]: https://docs.python.org/3/library/bisect.html
[cached-property]:
  https://docs.python.org/3/library/functools.html#functools.cached_property
[complexity]: https://docs.python.org/3/builtins/time-complexity.html
[counter]: https://docs.python.org/3/library/collections.html#collections.Counter
[dataclass]: https://docs.python.org/3/library/dataclasses.html#module-contents
[deque]: https://docs.python.org/3/library/collections.html#collections.deque
[faq-concat]:
  https://docs.python.org/3/faq/programming.html#what-is-the-most-efficient-way-to-concatenate-many-strings-together
[faq-perf]:
  https://docs.python.org/3/faq/programming.html#my-program-is-too-slow-how-do-i-speed-it-up
[heapq]: https://docs.python.org/3/library/heapq.html#heapq.nsmallest
[heapq-merge]: https://docs.python.org/3/library/heapq.html#heapq.merge
[memoryview]: https://docs.python.org/3/library/stdtypes.html#memoryview
[seq-concat]:
  https://docs.python.org/3/library/stdtypes.html#common-sequence-operations
[slots]: https://docs.python.org/3/reference/datamodel.html#slots
[struct]: https://docs.python.org/3/library/struct.html#struct.Struct
