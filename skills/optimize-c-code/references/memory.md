# Memory layout and allocation constructs

Cards for data layout, memory traffic, and allocation strategy. Pairs
live in
`assets/examples/constructs/memory.c` and `alloc.c`. The oracles
`memory_verify` and `alloc_verify` compare results on edge inputs;
`alloc_verify` also asserts allocator call counts through the counting
wrappers in `count.h`.

Measured results are machine-specific: Apple M1 Max, macOS arm64, Apple
clang 21.0.0 (swift.org toolchain), `-std=c17 -O2`, medians from
`sh assets/examples/verify.sh time` (21 batches), machine shared with
other builds (load average 8 to 60). Paired numbers come from separate
runs. `ALLOC` counts come from
`sh assets/examples/verify.sh verify`.

## Contents

- Struct member ordering
- Struct of arrays
- Row-major loop order
- memcpy for non-overlapping copies
- memmove for overlapping ranges
- memset for zeroing
- End offset instead of strcat
- Single-pass compaction
- Direct-indexed counting table
- Arena allocator
- Free list of fixed-size slots
- Geometric growth with realloc

## Struct member ordering

**Definition.** Members are laid out in declaration order, each at an
offset that satisfies its alignment; the compiler inserts unnamed
padding between members and at the end, never at the beginning
([N3220][n3220] 6.7.3.2; N1570 6.7.2.1). Declare members in decreasing
alignment order to remove interior padding.

**Use when.**

- Code scans large arrays of a record whose `sizeof` exceeds the sum of
  its member sizes.

**Do not use when.**

- The layout is an ABI or file format (shared headers, network or disk
  structs, `mmap`ed data): reordering breaks compatibility.
- Members are grouped so hot fields share a cache line; measure before
  and after any reorder.

**Example.**

```c
struct rec_padded { char tag; double value; char flag; int32_t id; };
struct rec_packed { double value; int32_t id; char tag; char flag; };

_Static_assert(sizeof(struct rec_packed) <= sizeof(struct rec_padded),
               "reordering must not grow the record");
_Static_assert(offsetof(struct rec_packed, value) == 0, "value first");
```

C23 also spells the assertion `static_assert` ([N3220][n3220] 6.7.12).
Assert exact sizes only for the ABIs you ship: the standard guarantees
the order, not the numbers.

**Cost removed.** Bytes per record: measured `LAYOUT sizeof padded=24
packed=16 bytes` (arm64). Scan of 2^20 records: `layout` 533100 ->
521600, 577700 -> 524800, 583700 -> 522600 ns.

**Verify.**

1. The oracle sums the same values from both layouts.
1. `sh assets/examples/verify.sh verify` prints the sizes and fails if
   the reordered record is not smaller.

## Struct of arrays

**Definition.** Store each field in its own array (`x[]`, `vx[]`)
instead of an array of records (`struct particle p[]`), so a loop over
two fields streams two dense arrays.

**Use when.**

- Hot loops read a few fields of a wide record over many elements.

**Do not use when.**

- Most accesses read whole records one at a time (random lookups): SoA
  turns one cache line into several.
- APIs that receive the record need the struct form.

**Example.**

```c
struct particle { float x, y, z, vx, vy, vz, mass, charge; };

NOINLINE void advance_aos(struct particle *p, size_t n, float dt) {
  for (size_t i = 0; i < n; ++i)
    p[i].x += p[i].vx * dt;
}

NOINLINE void advance_soa(float *restrict x, const float *restrict vx,
                          size_t n, float dt) {
  for (size_t i = 0; i < n; ++i)
    x[i] += vx[i] * dt;
}
```

**Cost removed.** Bytes loaded per element: measured `aos=32 soa=8`.
2^20 particles: `aos-soa` 630100 -> 127500 and 873500 -> 147100 ns.

**Verify.**

1. The oracle compares the resulting `x` values bit for bit (same
   expression, same rounding).
1. `sh assets/examples/verify.sh time aos-soa`.

## Row-major loop order

**Definition.** `m[r * cols + c]` for adjacent `c` are adjacent in
memory, so make the column index the inner loop.

**Use when.**

- The inner loop's index multiplies a large stride (`r * cols`) and the
  matrix exceeds the cache.

**Do not use when.**

- The body carries a dependence across outer-index iterations that the
  interchange would reorder (running sums along columns written back in
  place).
- The loop sums floating-point values: interchange changes the
  summation order.

**Example.**

```c
NOINLINE uint64_t matrix_sum_rows(const uint32_t *m, size_t rows,
                                  size_t cols) {
  uint64_t s = 0;
  for (size_t r = 0; r < rows; ++r)
    for (size_t c = 0; c < cols; ++c)
      s += m[r * cols + c];
  return s;
}
```

**Cost removed.** Cache misses from stride `cols * 4` bytes. Measured,
2048 x 2048 `uint32_t` (16 MiB): `loop-order` 13047500 -> 282000,
28030500 -> 353500 ns. Clang 21 did not interchange the baseline at
`-O2` or `-O3`.

**Verify.**

1. The oracle checks both orders on a 2 x 3 matrix, empty dimensions,
   and unsigned modular sums.
1. `sh assets/examples/verify.sh time loop-order`.

## memcpy for non-overlapping copies

**Definition.** [`memcpy`][n3220] "copies n characters from the object
pointed to by s2 into the object pointed to by s1. If copying takes
place between objects that overlap, the behavior is undefined"
(N3220 7.26.2.1; N1570 7.24.2.1).

**Use when.**

- A byte or element loop copies between buffers that never overlap.

**Do not use when.**

- The ranges can overlap: use `memmove`.
- The copy is a struct assignment: `a = b` is clearer and compiles to
  the same copy.

**Example.**

```c
NOINLINE void copy_memcpy(unsigned char *dst, const unsigned char *src,
                          size_t n) {
  memcpy(dst, src, n);
}
```

**Cost removed.** Measured, 1 MiB: `memcpy` 22150 -> 19550 and 23850 ->
20800 ns against the plain loop. Clang already vectorizes the plain loop
with overlap checks and turns it into a `memcpy` call when the pointers
are `restrict` (`copy_restrict` in `codegen.c`).

**Verify.**

1. The oracle compares both for every length 0..67 with guard bytes.
1. `sh assets/examples/verify.sh asm` shows `memcpy` in `copy_restrict`
   and not in `copy_plain`.

## memmove for overlapping ranges

**Definition.** [`memmove`][n3220] copies as if through a temporary
array, so overlapping source and destination give the expected result
(N3220 7.26.2.3; N1570 7.24.2.2).

**Use when.**

- Code shifts elements within one array (insert, delete, ring buffers).

**Do not use when.**

- The ranges provably never overlap and the profile shows the call hot:
  `memcpy` may be cheaper. State the proof.
- Code removes many elements one at a time: each call moves the tail.
  See single-pass compaction.

**Example.**

```c
/* Shift a[0..n-2] to a[1..n-1]. A forward loop would give aaaa. */
NOINLINE void shift_memmove(uint32_t *a, size_t n) {
  if (n > 1)
    memmove(a + 1, a, (n - 1) * sizeof *a);
}
```

**Cost removed.** None versus a correct backward loop: clang 21 turns
`shift_loop` into a `memmove` call itself. The card is about
correctness: a forward copy loop over overlapping ranges replicates the
first element.

**Verify.**

1. The oracle checks every length 0..33 and asserts the order
   (`s[0] == 1`, `s[1] == 1`, `s[n-1] == n-1`).
1. `sh assets/examples/verify.sh asm` asserts `memmove` in `shift_loop`.

## memset for zeroing

**Definition.** `memset(p, 0, n)` sets `n` bytes to zero (N3220
7.26.6.1). For fresh allocations, `calloc` returns zeroed memory.
All-zero bytes are zero for integer types; ISO C does not guarantee that
they form a null pointer.

**Use when.**

- Code clears arrays of integers or of structs of integers.

**Do not use when.**

- The memory holds secrets to clear before release: the compiler may
  remove a `memset` of memory that is not read again. Use C23
  `memset_explicit` (N3220 7.26.6.2) where the libc has it; the macOS
  26.5 and 27.0 SDK headers lack it and declare Annex K `memset_s` when
  `__STDC_WANT_LIB_EXT1__` is 1.
- You expect a speedup over a zeroing loop at `-O2` (see cost).

**Example.**

```c
NOINLINE void zero_memset(uint32_t *a, size_t n) {
  memset(a, 0, n * sizeof *a);
}
```

**Cost removed.** None measured: clang 21 compiles `zero_loop` to a
`bzero` call. Measured, 1 MiB: `memset` 38400 -> 37650 and 38700 -> 39800
ns.

**Verify.**

1. The oracle compares both for every length 0..33.
1. `sh assets/examples/verify.sh asm` asserts `bzero|memset` in
   `zero_loop`.

## End offset instead of strcat

**Definition.** `strcat(out, part)` scans `out` from the start to find
its end on every call, so joining `n` parts is quadratic. Tracking the
end offset and copying with `memcpy` makes it linear.

**Use when.**

- `strcat`, `strcpy(out + strlen(out), ...)`, or `sprintf(out, "%s...",
  out, ...)` runs in a loop.

**Do not use when.**

- The buffer size is not computed first: both forms overflow a short
  buffer. Sum the lengths with overflow checks and allocate once.

**Example.**

```c
NOINLINE void join_offset(char *out, const char *const *parts,
                          size_t n) {
  size_t end = 0;
  for (size_t i = 0; i < n; ++i) {
    size_t len = strlen(parts[i]);
    memcpy(out + end, parts[i], len);
    end += len;
  }
  out[end] = '\0';
}
```

**Cost removed.** Rescans of the output. Measured, 4096 parts of `"ab"`:
`join` 450500 -> 13000 and 558000 -> 13500 ns. `sample` of the
`hot` workload shows 1179 of 1249 samples in `strcat` under
`join_strcat`.

**Verify.**

1. The oracle compares both on empty, UTF-8, and multi-byte parts for
   every prefix count 0..5.
1. `sh assets/examples/verify.sh time join`.

## Single-pass compaction

**Definition.** Remove matching elements in one pass with a read index
and a write index, instead of calling `memmove` to close the gap after
each removal.

**Use when.**

- A loop deletes elements from an array one at a time with `memmove`.

**Do not use when.**

- Other code holds indexes into the array: compaction changes positions.
  Keep identifiers, not slot numbers.
- Order need not be stable and removals are rare: swap-with-last is O(1)
  per removal.

**Example.**

```c
NOINLINE size_t compact_single_pass(uint32_t *a, size_t n) {
  size_t out = 0;
  for (size_t i = 0; i < n; ++i)
    if (a[i] != 0)
      a[out++] = a[i];
  return out;
}
```

**Cost removed.** Quadratic element moves. Measured, 16384 elements, one
third zero: `compaction` 2606000 -> 4750 and 3689250 -> 4750 ns.

**Verify.**

1. The oracle runs every sequence over {0,1,2} of length 0..6, which
   includes adjacent zeros (a baseline that advances after a removal
   skips the second zero).
1. `sh assets/examples/verify.sh time compaction`.

## Direct-indexed counting table

**Definition.** Count byte values in one pass with a 256-entry table
indexed by the byte, instead of one pass per value.

**Use when.**

- Nested loops scan the same data once per key (histograms, character
  classes).

**Do not use when.**

- The key space is large or sparse (32-bit keys): use a hash table or
  sort.

**Example.**

```c
NOINLINE void histogram_direct(const unsigned char *b, size_t n,
                               size_t out[256]) {
  memset(out, 0, 256 * sizeof out[0]);
  for (size_t i = 0; i < n; ++i)
    ++out[b[i]];
}
```

**Cost removed.** 255 of 256 passes. Measured, 65536 bytes: `histogram`
2552000 -> 21500 and 2607000 -> 22500 ns.

**Verify.**

1. The oracle compares both for lengths 0, 150, and 300.
1. `sh assets/examples/verify.sh time histogram`.

## Arena allocator

**Definition.** A bump allocator that takes large blocks from `malloc`,
hands out aligned pieces by advancing an offset, and frees all blocks at
once. Pieces are aligned to `alignof(max_align_t)` ([N3220][n3220]
7.21), the alignment `malloc` guarantees.

**Use when.**

- Many small objects share one lifetime (a parse tree, a request, a
  frame) and are released together.

**Do not use when.**

- Objects need individual `free`: an arena cannot return one piece.
- The arena's lifetime is unbounded: memory only grows.
- Sanitizers must catch overflows between pieces: ASan sees one block.

**Example.**

```c
static void *arena_alloc(struct arena *a, size_t size) {
  size_t align = alignof(max_align_t);
  if (size > SIZE_MAX - sizeof(struct arena_block) - (align - 1))
    return NULL; /* rounding or the block header would wrap */
  size = (size + align - 1) & ~(align - 1);
  struct arena_block *b = a->head;
  if (b == NULL || b->cap - b->used < size) {
    size_t cap = size > a->block_size ? size : a->block_size;
    b = cm_malloc(sizeof *b + cap);
    if (b == NULL)
      return NULL;
    b->next = a->head;
    b->used = 0;
    b->cap = cap;
    a->head = b;
  }
  void *p = b->data + b->used;
  b->used += size;
  return p;
}
```

Runnable: `assets/examples/constructs/alloc.c` (`list_arena`).

**Cost removed.** Allocator calls. Measured: `ALLOC arena baseline 5000
calls candidate 2 calls`; 100000 nodes: `arena` 1795200 -> 386400 and
2804800 -> 386200 ns.

**Verify.**

1. The oracle compares list sums for 0, 1, 2, 1000, and 5000 nodes and
   checks that every block is freed.
1. `sh assets/examples/verify.sh verify` prints the `ALLOC arena` line;
   `sh assets/examples/verify.sh profile` runs `leaks --atExit`.

## Free list of fixed-size slots

**Definition.** A pool that keeps released objects on a singly linked
list threaded through the objects themselves and hands them out again
before asking the backing arena for new memory.

**Use when.**

- Objects of one size are created and destroyed at a high rate with a
  bounded number alive (connections, timers, nodes).

**Do not use when.**

- Object sizes vary: use size classes or `malloc`.
- Several threads share the pool without a lock or per-thread pools.
- Use-after-free must be detected: recycled slots hide it from ASan.

**Example.**

```c
union slot {
  union slot *next_free;
  struct node node;
};

static struct node *pool_get(struct pool *p) {
  union slot *s = p->free;
  if (s != NULL)
    p->free = s->next_free;
  else
    s = arena_alloc(&p->backing, sizeof *s);
  return s == NULL ? NULL : &s->node;
}

static void pool_put(struct pool *p, struct node *n) {
  union slot *s = (union slot *)n;
  s->next_free = p->free;
  p->free = s;
}
```

**Cost removed.** Allocator calls per object. Measured, 10000 operations
with 64 live: `ALLOC free-list baseline 10000 calls candidate 1 calls`;
100000 operations: `free-list` 1855800 -> 130200 and 2203200 -> 132000
ns.

**Verify.**

1. The oracle compares sums for live windows of 1, 4, 16, and 64.
1. `sh assets/examples/verify.sh sanitize` runs it under ASan.

## Geometric growth with realloc

**Definition.** When a dynamic array is full, grow its capacity by a
factor (2 here; 1.5 is also common) instead of by one element, so `n`
pushes cost O(log n) `realloc` calls. `realloc` may move the block: pointers
into the old block become invalid, and on failure it returns a null
pointer and leaves the old block intact ([N3220][n3220] 7.24.3.7).

**Use when.**

- A push or append loop calls `realloc` for each element.

**Do not use when.**

- The final size is known: allocate it once.
- Memory is tight and the array is long-lived: shrink with one final
  `realloc` after the fill.

**Example.**

```c
static int push_grow_double(struct u32vec *v, uint32_t x) {
  if (v->len == v->cap) {
    size_t cap = v->cap ? v->cap * 2 : 16;
    if (cap > SIZE_MAX / sizeof *v->data)
      return -1;
    uint32_t *d = cm_realloc(v->data, cap * sizeof *d);
    if (d == NULL)
      return -1; /* v->data is still valid */
    v->data = d;
    v->cap = cap;
  }
  v->data[v->len++] = x;
  return 0;
}
```

**Cost removed.** `realloc` calls and copies. Measured, 5000 pushes: `ALLOC
growth baseline 5000 calls candidate 10 calls`; 100000 pushes: `growth`
2037000 -> 98800 and 3299200 -> 102200 ns.

**Verify.**

1. The oracle compares results for 0, 1, 2, 1000, and 5000 pushes.
1. Never assign `realloc`'s result to the only pointer before checking
   it for null; review for pointers kept into the old block.

[n3220]: https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3220.pdf
