# Interpreter-level constructs

These cards cut per-iteration interpreter work in pure-Python hot loops:
name lookups, method calls, temporary objects, string building, sort keys,
regular expressions, and repeated pure calls. Each example is a
`baseline_*`/`candidate_*` pair in
[`interpreter.py`](../assets/examples/constructs/interpreter.py). `run()`
proves equivalence and the deterministic benefit;
[`bench.py`](../assets/examples/constructs/bench.py) times the pair with
pyperf.

Measured numbers are machine-specific: Apple M1 Max, macOS, Homebrew CPython
3.14.7 (GIL build, no JIT), pyperf 2.10.0 `--fast` (10 worker runs × 2
values, per `pyperf stats`). Timings come from
`BENCH_OUT=... PYPERF_ARGS=--fast sh assets/examples/verify.sh measure`, read
from the `compare_to --table` output. Other jobs loaded the machine, so rows
with a large baseline std dev were rerun as single pairs with
`BENCH_FILTER=<name>`, as marked. Executed-instruction and call counts come
from `sh assets/examples/verify.sh verify`; two consecutive runs printed
identical counts and bytes. Tier: Executed. Counts are deterministic for
3.14.7 and differ on other versions, because bytecode changes between
releases.

Apply these cards only after cProfile or pyperf shows the loop matters. The
Python FAQ puts algorithm and data-structure changes ahead of
micro-optimizations ([programming FAQ][faq-perf]); check
[containers](containers.md) first.

## Contents

- Local binding of module attributes
- Hoisting a bound method
- List comprehension instead of an append loop
- C-implemented methods instead of Python loops
- Generator expression instead of a temporary list
- itertools.chain.from_iterable instead of sum(lists, [])
- str.join instead of repeated concatenation
- io.StringIO for incremental writers
- operator.itemgetter and attrgetter keys
- Precompiled regular expressions
- functools.cache and lru_cache

## Local binding of module attributes

**Definition.** Assigning `sqrt = math.sqrt` to a local before a loop turns
two lookups per iteration (`LOAD_GLOBAL math`, then `LOAD_ATTR sqrt`) into
one local load (`LOAD_FAST*`). Locals are indexed frame slots; globals and
attributes need a dictionary lookup, which CPython 3.11+ caches inline but
still guards ([What's New 3.11][wn311-spec]).

**Use when.**

- A profiled loop calls a module function or builtin (`math.sqrt`, `len`,
  `isinstance`) many times per call.
- The name is not rebound while the loop runs.

**Do not use when.**

- Tests or callers monkeypatch the global (`mock.patch("math.sqrt")`) and
  expect the loop to see it: the local keeps the old object, so the patch
  silently stops working.
- You would bind through a default argument (`def f(x, sqrt=math.sqrt)`):
  that widens the public signature. Assign a local inside the body.
- The loop runs only a few times: no measurable gain.

**Example.**

```python
def candidate_norms(points):
    sqrt = math.sqrt  # not rebound while the loop runs
    out = []
    for x, y in points:
        out.append(sqrt(x * x + y * y))
    return out
```

**Cost removed.** One `LOAD_GLOBAL` plus one `LOAD_ATTR` per iteration.
Measured executed-instruction count for 2,000 points: 6,004 -> 2,006
`LOAD_ATTR`+`LOAD_GLOBAL`. The remaining loads are `out.append` (next
card). pyperf `local_binding`: 148 us -> 142 us, 1.05x faster
(single-pair rerun).

**Verify.**

1. `sh assets/examples/verify.sh verify` checks `local-binding` equality on
   2,000 points and on `[]`.
1. The same run prints `METRIC local-binding executed LOAD_ATTR+LOAD_GLOBAL`
   with the candidate lower. Keep the change only if `verify.sh measure`
   with `BENCH_FILTER=local_binding` shows a significant row.

## Hoisting a bound method

**Definition.** `append = out.append` creates one bound-method object before
the loop, so each iteration calls the local instead of repeating `LOAD_ATTR`
(method form) on `out`.

**Use when.**

- A loop calls the same method on the same object each iteration
  (`out.append`, `seen.add`, `buf.write`).
- The receiver is not rebound inside the loop.

**Do not use when.**

- The loop reassigns the receiver (`out = []` mid-loop) or swaps
  `self.handler`: the hoisted method keeps pointing at the old object.
- A comprehension can replace the loop: that removes the call entirely (next
  card).
- The method is `list.append` on CPython 3.14: the specializer turns
  `out.append(x)` into `CALL_LIST_APPEND`, while the hoisted bound method
  runs as a generic `CALL_BUILTIN_O` (observed with
  `dis.get_instructions(f, adaptive=True)` after warmup). The pyperf row
  below is slower.

**Example.**

```python
def candidate_strip(lines):
    out = []
    append = out.append  # `out` is never rebound inside the loop
    for line in lines:
        append(line.strip())
    return out
```

**Cost removed.** One `LOAD_ATTR` per iteration, but not time for
`list.append` on 3.14.7. Measured, 2,000 lines: 4,003 -> 2,004 executed
`LOAD_ATTR`; `line.strip` remains. pyperf `hoist_method`:
85.3 us -> 90.2 us, 1.06x slower (single-pair rerun).

**Verify.**

1. `verify.sh verify` compares the pair on a list and on a one-shot iterator.
1. `METRIC hoist-method executed LOAD_ATTR` must drop, and the pyperf row
   must be significantly faster; instruction counts alone do not justify
   this card. For `list.append` on 3.14.7 it was slower: revert there.

## List comprehension instead of an append loop

**Definition.** A list comprehension appends each element with the
`LIST_APPEND` instruction instead of a method call ([dis][dis-list-append]).
Since 3.12, comprehensions are also inlined into the enclosing frame (PEP 709)
and no longer create a function object per execution
([What's New 3.12][wn312-709]).

**Use when.**

- A loop only filters and transforms items into a new list.
- The body has no side effects that other code observes between items.

**Do not use when.**

- The body must stop early with `break` or handle an exception per item: a
  comprehension cannot express that without changing semantics.
- Debugging or profiling relies on a comprehension frame: since 3.12 there is
  none in tracebacks or profiles.
- A reducer consumes the result once: use a generator expression and never
  build the list (generator card).

**Example.**

```python
def candidate_even_squares(values):
    return [value * value for value in values if value % 2 == 0]
```

**Cost removed.** One `LOAD_ATTR` and one `CALL` per appended element.
Measured, 2,000 values: 1,003 -> 3 executed `CALL*` instructions. pyperf
`comprehension`: 74.8 us -> 70.7 us, 1.06x faster (single-pair rerun).

**Verify.**

1. `verify.sh verify` checks equality on negative, zero, and positive values.
1. `METRIC comprehension executed CALL*` must drop. Confirm the time with
   `BENCH_FILTER=comprehension`.

## C-implemented methods instead of Python loops

**Definition.** Builtins and methods of built-in types (`bytes.count`,
`str.translate`, `sum`, `any`, `max`, `sorted`, `dict.fromkeys`) run their
loop in C and execute no bytecode per element. The FAQ calls library
primitives likely faster, "doubly true for primitives written in C"
([programming FAQ][faq-perf]).

**Use when.**

- The Python loop computes exactly what one C method defines: counting,
  searching, joining, min/max, membership, order-preserving deduplication.
- The element type is built in, so the method's semantics are known.

**Do not use when.**

- The loop's comparison differs from the method's (`str.lower() ==` versus
  `casefold()`, `==` on floats versus `math.isclose`): the results diverge.
- The replacement changes tie or error behavior: `sorted(xs)[-1]` returns the
  last of equal maxima and `max(xs)` returns the first ([max][max]); on empty
  input, `max` raises unless you pass `default=`.

**Example.**

```python
def candidate_count_zero(data: bytes) -> int:
    return data.count(0)
```

**Cost removed.** The whole per-element bytecode loop. Measured, 20,000 bytes:
168,597 -> 20 executed instructions. pyperf `builtin_method`:
278 us -> 7.68 us, 36.19x faster (single-pair rerun).

**Verify.**

1. `verify.sh verify` checks `b""`, `b"\0"`, and 20,000 bytes.
1. `METRIC builtin-method executed instructions` must drop by orders of
   magnitude.

## Generator expression instead of a temporary list

**Definition.** `sum(x * x for x in values)` passes a generator that yields
one item at a time. `sum([...])` first materializes the whole list, which
stays alive with its elements until the reducer returns
([generator expressions][genexpr]).

**Use when.**

- A reducer (`sum`, `max`, `any`, `all`, `"".join`, `set`, `dict`) consumes
  a temporary list exactly once.
- tracemalloc attributes the peak to that temporary.

**Do not use when.**

- The result is iterated twice or needs `len()`: a generator is exhausted
  after one pass, and the second pass silently sees nothing.
- The code relies on eager evaluation: with a generator, exceptions and side
  effects happen during consumption, not at construction.
- The goal is speed: per item, a generator can be slower than a list
  comprehension. The benefit is memory; check the pyperf row.

**Example.**

```python
def candidate_sum_squares(values):
    return sum(value * value for value in values)
```

**Cost removed.** Memory, not time. Measured tracemalloc peak for 200,000
items: 8,023,696 B -> 512 B. pyperf `generator_expression` (20,000 items):
713 us -> 749 us, 1.05x slower (single-pair rerun).

**Verify.**

1. `verify.sh verify` checks equality on `range(200_000)`.
1. `METRIC generator-expression tracemalloc peak B` must drop and stay flat
   when the input doubles.

## itertools.chain.from_iterable instead of sum(lists, [])

**Definition.** `sum(rows, [])` builds a new list for every row and copies
everything accumulated so far: quadratic in the total length.
`chain.from_iterable(rows)` yields each element once. The `sum` docs point to
`itertools.chain()` for concatenating iterables ([sum][sum],
[itertools][itertools]).

**Use when.**

- Code flattens lists with `sum(..., [])`, `functools.reduce(operator.add,
  ...)`, or `acc = acc + row` in a loop.

**Do not use when.**

- The rows are strings: use `"".join(rows)`. `sum` rejects a `str` start
  value.
- The rows' own `__add__` semantics matter (a custom sequence type whose `+`
  does more than concatenate).

**Example.**

```python
def candidate_flatten(rows):
    return list(chain.from_iterable(rows))
```

**Cost removed.** Quadratic copying. Measured CPU time, 2,000 rows of 10: 0.084
s -> 0.00019 s (`verify` asserts at least 10×). pyperf `chain_flatten`:
84.8 ms -> 183 us, 463.06x faster.

**Verify.**

1. `verify.sh verify` checks equality on 2,000 rows and on `[]`.
1. `METRIC chain-flatten cpu s` shows the ratio. Doubling the row count
   should roughly quadruple the baseline time and double the candidate's.

## str.join instead of repeated concatenation

**Definition.** `s = s + t` creates a new string and copies both parts, so
repeated concatenation is quadratic in the total length
([sequence note][seq-concat]). `"".join(parts)` computes the size once and
copies each part once. CPython sometimes resizes a string in place for
`local += piece`, but PEP 8 says not to rely on it: it "is fragile even in
CPython" and absent elsewhere ([PEP 8][pep8-concat]).

**Use when.**

- A loop grows a string with `+=` or `+`, especially into an attribute, a
  dict item, or a global: the in-place shortcut does not apply to those
  targets.
- The code must be linear on PyPy and other implementations too.

**Do not use when.**

- The string is a handful of fixed pieces: an f-string is clearer and
  equally linear.
- A writer API (`.write()`) produces the pieces: use `io.StringIO` (next
  card).

**Example.**

```python
def candidate_render(parts):
    return "".join(parts)
```

The baseline in `interpreter.py` appends to `report.text`, an attribute
target: quadratic on 3.14.7. A plain local `text += part` measured
near-linear on the same interpreter; that is the fragile shortcut PEP 8 warns
about.

**Cost removed.** Quadratic copying. Measured CPU time, 80,000 parts: 0.47 s ->
0.00053 s (`verify` asserts at least 10×). pyperf `str_join` (20,000 parts):
87.1 ms -> 102 us, 855.02x faster.

**Verify.**

1. `verify.sh verify` checks equality on mixed ASCII, non-BMP, and empty
   pieces, and on `[]`.
1. `METRIC str-join cpu s` must show the baseline at least 10× slower.

## io.StringIO for incremental writers

**Definition.** `io.StringIO` is an in-memory text stream: `write()` appends
to an internal buffer and `getvalue()` builds the string once. The FAQ calls
it "another reasonably efficient idiom" next to `str.join`
([programming FAQ][faq-concat]).

**Use when.**

- The producer already writes through a `.write()` interface (CSV writer,
  `print(..., file=out)`, template renderer, a function that takes a
  file-like object).
- Several functions produce the pieces, so collecting a list is awkward.

**Do not use when.**

- A list of strings already exists: `"".join` avoids the stream object.
- The output is bytes: use `io.BytesIO` or `bytearray`
  ([containers](containers.md#bytearray-accumulation)).

**Example.**

```python
def emit_rows(out, rows):
    for row in rows:
        out.write(f"{row},")
    return out.getvalue()

candidate = emit_rows(io.StringIO(), range(40_000))
```

**Cost removed.** Quadratic copying through a concatenating writer. Measured
CPU time for 40,000 rows: 0.15 s -> 0.0046 s (`verify` asserts at least 5×).
pyperf `stringio` (20,000 rows): 58.5 ms -> 2.22 ms, 26.32x faster.

**Verify.**

1. `verify.sh verify` checks equality between `ConcatWriter` and
   `io.StringIO`.
1. `METRIC stringio cpu s` must show the ratio.

## operator.itemgetter and attrgetter keys

**Definition.** `operator.itemgetter(i)` and `attrgetter("name")` are
C-implemented callables. As the `key=` of `sorted`, `min`, `max`, or
`groupby`, they start no Python frame per element. The sorting HOWTO calls them
"easier and faster" ([sorting HOWTO][sorting]).

**Use when.**

- A `key=lambda r: r[1]` or `key=lambda o: o.name` runs over many elements.
- Multi-level keys: `itemgetter(1, 2)` builds the tuple key in C.

**Do not use when.**

- The key transforms the value (`lambda r: r[1].lower()`): itemgetter
  cannot express it. Keep the lambda or precompute a decorated list.
- The lambda supplies a default for a missing field (`r.get(k, 0)`):
  itemgetter raises `IndexError`/`KeyError` instead, as a plain subscript
  lambda would.

**Example.**

```python
def candidate_sort_rows(rows):
    return sorted(rows, key=operator.itemgetter(1))
```

**Cost removed.** One Python call per element. Measured, 3,000 rows: 3,001 -> 1
Python function starts (`PY_START`). `max(rows, key=attrgetter("score"))`
over 1,000 slotted objects: 1,001 -> 1, and it returns the same first
maximal object (checked by identity). pyperf `itemgetter_key`:
261 us -> 198 us, 1.32x faster.

**Verify.**

1. `verify.sh verify` checks equality, including stable order for equal keys
   (`sorted` is stable in both variants).
1. `METRIC itemgetter-key Python calls` must drop to the one outer call.

## Precompiled regular expressions

**Definition.** `re.compile(pattern)` returns a `Pattern` whose methods skip
the pattern-cache lookup. Module-level functions (`re.match`,
`re.fullmatch`, `re.sub`) call an internal compile-and-cache function every
time. Saving the compiled object "is more efficient when the expression will
be used several times"; recent patterns are cached
([re][re-compile]).

**Use when.**

- A module-level `re.*` call with a constant pattern runs per record in a
  profiled loop.
- The program uses many patterns, so the module cache can evict entries.

**Do not use when.**

- The pattern is built from input per call: compiling it every time costs
  the same. Validate or cache the pattern explicitly.
- The call count is small: the internal cache already avoids recompiling, so
  the gain is only lookup and call overhead. Measure.

**Example.**

```python
ID_PATTERN = re.compile(r"[A-Z]{3}-\d{4}")

def candidate_valid_ids(values):
    fullmatch = ID_PATTERN.fullmatch
    return [fullmatch(value) is not None for value in values]
```

**Cost removed.** Two Python-level calls per record (`re.fullmatch` and its
internal compile helper). Measured, 2,000 records: 4,001 -> 1 Python function
starts. pyperf `re_compile`: 632 us -> 267 us, 2.36x faster.

**Verify.**

1. `verify.sh verify` checks valid, lower-case, too-long, and empty IDs.
1. `METRIC re-compile Python calls` must drop.

## functools.cache and lru_cache

**Definition.** `@functools.cache` (3.9+) memoizes a function in an unbounded
dict keyed by its arguments. `@lru_cache(maxsize=128)` is the bounded LRU
form. `cache_info()` reports `hits`, `misses`, `maxsize`, and `currsize`.
`cache` is "smaller and faster than @lru_cache with a size limit"
([functools][functools]).

**Use when.**

- A pure function is called repeatedly with the same hashable arguments: a
  profile shows repeated `ncalls` with identical inputs.
- The number of distinct arguments is bounded, or you pass `maxsize`.

**Do not use when.**

- The function reads mutable state, the clock, files, or the network: cached
  results become stale.
- It returns a mutable object that callers modify: every caller shares and
  corrupts the same cached instance.
- It is a method: `self` becomes part of the key, and the cache keeps every
  instance alive ([functools][functools]).
- Arguments are unhashable (`list`, `dict`): the call raises `TypeError`.
- The function must run once per key under threads: the cache is
  thread-safe, but racing misses can run the function more than once for the
  same key.
- `maxsize` is below the working set of cycling keys. The oracle cycles 3
  keys through `lru_cache(maxsize=2)` and gets 0 hits: every call misses and
  pays the cache bookkeeping on top. Size the cache from `cache_info()` on
  real traffic.

**Example.**

```python
@functools.cache
def cached_collatz_steps(n: int) -> int:
    return collatz_steps(n)

cached_collatz_steps.cache_info()  # hits, misses, maxsize, currsize
```

**Cost removed.** Repeated computation. Measured, 1,200 queries over 3
distinct inputs: 1,200 -> 3 underlying calls, `hits == 1,197`.

**Verify.**

1. `verify.sh verify` checks equality, then counts the underlying calls.
1. `cache_info().hits` equals queries minus distinct inputs. The `lru-cache`
   checks assert 0 hits for the undersized bounded cache. In production, log
   `cache_info()` to confirm the hit rate on real traffic.

[dis-list-append]: https://docs.python.org/3/library/dis.html#opcode-LIST_APPEND
[faq-concat]:
  https://docs.python.org/3/faq/programming.html#what-is-the-most-efficient-way-to-concatenate-many-strings-together
[faq-perf]:
  https://docs.python.org/3/faq/programming.html#my-program-is-too-slow-how-do-i-speed-it-up
[functools]: https://docs.python.org/3/library/functools.html#functools.cache
[genexpr]:
  https://docs.python.org/3/reference/expressions.html#generator-expressions
[itertools]:
  https://docs.python.org/3/library/itertools.html#itertools.chain.from_iterable
[max]: https://docs.python.org/3/library/functions.html#max
[pep8-concat]: https://peps.python.org/pep-0008/#programming-recommendations
[re-compile]: https://docs.python.org/3/library/re.html#re.compile
[seq-concat]:
  https://docs.python.org/3/library/stdtypes.html#common-sequence-operations
[sorting]:
  https://docs.python.org/3/howto/sorting.html#operator-module-functions-and-partial-function-evaluation
[sum]: https://docs.python.org/3/library/functions.html#sum
[wn311-spec]:
  https://docs.python.org/3/whatsnew/3.11.html#pep-659-specializing-adaptive-interpreter
[wn312-709]:
  https://docs.python.org/3/whatsnew/3.12.html#pep-709-comprehension-inlining
