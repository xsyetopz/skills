# Allocation constructs

Each card removes or shrinks heap allocation on a measured hot path. Pairs
live in
[`Allocation.java`][example-src].
`Verify.allocation()` proves equivalence, and `AllocationBench` measures
`gc.alloc.rate.norm` (bytes per operation) with JMH `-prof gc`.

Measured on: Apple M1 Max, macOS arm64, OpenJDK 25.0.4.1 (G1, `-Xms1g
-Xmx1g`), JMH 1.37, `-wi 3 -i 5` with 1 s iterations and 1 fork unless a
card says otherwise. Bytes per operation repeat across runs for this JDK
and input (the stream card notes a small variation). Timings come from a
shared machine (load average 4 to 91), are machine-specific, and carry
JMH's 99.9% error. Overlapping intervals mean **no measurable
difference**, which several cards report.

## Contents

- Escape analysis and scalar replacement
- Escaping temporaries
- StringBuilder for loop concatenation
- Single-expression concatenation
- Primitive arrays instead of boxed collections
- Primitive accumulators
- Integer cache and boxed identity
- Presized ArrayList
- HashMap newHashMap sizing
- Records as composite map keys
- Streams versus loops with collection
- Primitive stream reductions

## Escape analysis and scalar replacement

**Definition.** C2's escape analysis (`-XX:+DoEscapeAnalysis`, on by
default) proves that an object never leaves the compiled method (after
inlining) and then replaces its fields with locals, so the allocation
disappears (scalar replacement, `EliminateAllocations`, on by default).
Arrays qualify up to `EliminateAllocationArraySizeLimit` elements (64 on
this JDK, `java -XX:+PrintFlagsFinal -version`).

**Use when.**

- A hot method creates small short-lived objects (points, pairs, records,
  iterators) used only inside it and its inlined callees: keep them
  local. You do not need to hand-inline fields.

**Do not use when.**

- Correctness depends on it: EA is a C2-only optimization. The
  interpreter and C1 allocate, so allocation is present during warmup and
  in `-XX:TieredStopAtLevel=1` runs.
- The object reaches a call that is not inlined, a field, an array, or
  another thread (see [escaping temporaries](#escaping-temporaries)).

**Example.**

```java
public record Point(int x, int y) {
    long lengthSquared() {
        return (long) x * x + (long) y * y;
    }
}

public static long local(int[] xs) {
    long sum = 0;
    for (int i = 0; i < xs.length; i++) {
        Point p = new Point(xs[i], i);   // never escapes
        sum += p.lengthSquared();        // inlined
    }
    return sum;
}
```

Runnable: `Allocation.Escape.local`; benchmark `escapeLocal`, and the
same code in a fork with `-XX:-DoEscapeAnalysis` (`escapeLocalNoEA`).

**Cost removed.** One 24-byte `Point` per element (12-byte header plus
two `int` fields, aligned to 8). Measured, 1,000 elements, two runs:
`escapeLocal` 0.013 and 0.003 B/op, 1,855 ± 272 and 446 ± 20 ns/op;
`escapeLocalNoEA` 24,000 B/op, 9,549 ± 6,721 and 2,162 ± 226 ns/op. The
second run was on a quieter machine.

**Verify.**

1. `sh assets/examples/verify.sh verify` checks that `local` and
   `escaping` return the same sum for 0, 1, 7, and 1,000 elements.
1. `sh assets/examples/verify.sh measure` asserts that `escapeLocal`
   allocates less than `escapeLocalNoEA` and `escapeEscaping`, and its
   `# VM options:` lines show `-XX:-DoEscapeAnalysis` for one fork.
1. `-XX:+UnlockDiagnosticVMOptions -XX:+PrintInlining` shows whether the
   callee inlined
   ([JIT logs](measurement.md#jit-compilation-and-inlining-logs)).

## Escaping temporaries

**Definition.** An allocation escapes when the object is passed to a call
C2 does not inline, stored in a field or array, returned, or published to
another thread. C2 must then allocate it on the heap.

**Use when.**

- A profile or `gc.alloc.rate.norm` shows allocation of a small temporary
  whose only use is a call. Check `PrintInlining` for that call site:
  `too big`, `hot method too big`, and
  `already compiled into a big method` are C2 reasons in
  [bytecodeInfo.cpp][bytecode-info]; a local C1 compile printed
  `failed to inline: callee uses too much stack`. Shrinking the callee
  below `FreqInlineSize` (325 bytecodes here), or splitting a cold path
  out of it, lets it inline so EA applies.

**Do not use when.**

- The callee is megamorphic (three or more receiver types at that site):
  it will not inline. Pass primitives instead of an object.
- You would force inlining with `@ForceInline`-style JDK internals or
  production JVM flags such as `-XX:FreqInlineSize`: that changes every
  method's compilation.

**Example.**

```java
public static long escaping(int[] xs) {
    long sum = 0;
    for (int i = 0; i < xs.length; i++) {
        sum += measure(new Point(xs[i], i));
    }
    return sum;
}

@CompilerControl(CompilerControl.Mode.DONT_INLINE)  // simulates a
private static long measure(Point p) {              // non-inlined call
    return p.lengthSquared();
}
```

Runnable: `Allocation.Escape.escaping`, benchmark `escapeEscaping`.

**Cost removed.** The same object as the previous card: 24,000 B/op for
1,000 elements when it escapes (measured: 24,000 B/op; 12,774 ± 5,786
and 3,277 ± 335 ns/op in two runs), versus under 0.02 B/op when inlined.

**Verify.**

1. Equivalence: the `escape` check in `Verify.allocation()`.
1. Benefit: `escapeEscaping:escapeLocal` in the `measure` assertions.

## StringBuilder for loop concatenation

**Definition.** `s = s + part` inside a loop creates a new `String` and
backing array on every iteration, copying everything built so far:
O(n²) bytes copied. One `StringBuilder` appends into a growing buffer and
creates the `String` once. [JEP 280][jep280] changed how javac compiles
each `+` expression (an `invokedynamic` to `StringConcatFactory`), not
the per-iteration copy.

**Use when.**

- A loop, recursion, or repeated method call extends one string.

**Do not use when.**

- The concatenation is a single expression (`a + ":" + b`): see
  [single-expression concatenation](#single-expression-concatenation).
- The parts are already a collection and need a separator:
  `String.join` or `Collectors.joining` is clearer and also uses a
  builder.

**Example.**

```java
public static String loopConcat(List<String> parts) {
    String result = "";
    for (String part : parts) {
        result = result + part;          // copies result every time
    }
    return result;
}

public static String loopBuilder(List<String> parts) {
    StringBuilder result = new StringBuilder();
    for (String part : parts) {
        result.append(part);
    }
    return result.toString();
}
```

Runnable: `Allocation.Strings`, benchmarks `stringLoopConcat` and
`stringLoopBuilder` over 64 parts.

**Cost removed.** Intermediate strings. Measured: 14,616 B/op to
1,648 B/op for 64 parts (`gc.alloc.rate.norm`). Time with 3 forks:
914.2 ± 26.6 ns/op (concat) versus 412.1 ± 26.8 ns/op (builder). The
baseline's copied bytes grow quadratically with the number of parts;
this run used 64.

**Verify.**

1. `Verify.allocation()` compares both on `"a", "", "é", "🙂", "\0"` and
   on an empty list.
1. `measure` asserts that `stringLoopConcat:stringLoopBuilder`
   allocation drops.

## Single-expression concatenation

**Definition.** Since JDK 9, javac compiles each string concatenation
expression to an `invokedynamic` call bootstrapped by
`StringConcatFactory` ([JEP 280][jep280]). The JDK chooses the strategy
at link time and sizes the result exactly.

**Use when.**

- Always, for one expression: keep `key + sep + id`. Do not rewrite it as
  a manual `StringBuilder` chain.

**Do not use when.**

- The code compiles with `--release 8` or lower: javac then emits the
  old `StringBuilder` chain, and this card's measurement does not apply.

**Example.**

```java
public static String exprConcat(String key, int id, char sep) {
    return key + sep + id;                 // invokedynamic (JEP 280)
}

public static String exprBuilder(String key, int id, char sep) {
    return new StringBuilder().append(key).append(sep).append(id)
        .toString();
}
```

Runnable: `Allocation.Strings`, benchmarks `stringExprConcat` and
`stringExprBuilder`.

**Cost removed.** None: **no measurable difference**. Both allocate
56.000 B/op. Mean times flipped direction across three loaded runs
(concat 33.1, 90.8, 13.7 ns/op; builder 17.4, 19.4, 71.9 ns/op, errors
up to ± 77). The fastest iterations of the 5-fork run were 11.6 ns/op
(concat) and 12.1 ns/op (builder).

**Verify.**

1. `Verify.allocation()` compares both, including a `null` key (both give
   `"null:-1"`).
1. `measure` asserts `--alloc-same stringExprBuilder:stringExprConcat`.
1. `javap -c -p -cp target/classes 'example.Allocation$Strings'` shows
   `invokedynamic ... makeConcatWithConstants` in `exprConcat`.

## Primitive arrays instead of boxed collections

**Definition.** A `List<Integer>` stores a reference array plus one
`Integer` object per value (16 bytes each here: 12-byte header plus a
4-byte `int`). An `int[]` stores 4 bytes per value inline.

**Use when.**

- Large numeric collections dominate heap
  (`jcmd <pid> GC.class_histogram` shows many
  `java.lang.Integer`/`Long`), or building them dominates allocation.
- The values have no identity and are never `null`.

**Do not use when.**

- The collection may contain `null` (meaning "missing"): `int[]` cannot
  represent it, and unboxing a `null` throws `NullPointerException`.
- The API contract returns `List<Integer>` to callers: converting at the
  boundary pays for the boxing again.
- You expect faster iteration over already-built small lists: see the
  measurement below.

**Example.**

```java
public static long sumBoxedList(List<Integer> values) {
    long sum = 0;
    for (Integer value : values) {
        sum += value;                    // unbox; NPE on null
    }
    return sum;
}

public static long sumArray(int[] values) {
    long sum = 0;
    for (int value : values) {
        sum += value;
    }
    return sum;
}
```

Runnable: `Allocation.Boxing`, `Verify.boxedFootprint()`, benchmarks
`boxedListSum` and `primitiveArraySum` (1,000 values, mostly outside the
Integer cache).

**Cost removed.** Footprint and construction allocation. Building
100,000 uncached values took 2,000,832 bytes as a presized
`List<Integer>` versus 400,808 bytes as `int[]` (thread-allocated
bytes). Summing an existing 1,000-element list: **no measurable
difference** (three runs: `boxedListSum` 2,893 ± 2,091, 1,254 ± 486,
863 ± 379 ns/op; `primitiveArraySum` 2,303 ± 793, 4,494 ± 3,262,
747 ± 249 ns/op). These boxes were allocated in order and sat in cache;
scattered boxes in a large heap behave differently, so measure the real
data.

**Verify.**

1. `Verify.allocation()` compares sums and asserts that the boxed list
   throws `NullPointerException` on a `null` element.
1. `Verify.boxedFootprint()` asserts that the list needs more than 4x the
   bytes of the array, and prints `FOOTPRINT ...`.

## Primitive accumulators

**Definition.** `Long total = 0L; total += v;` unboxes, adds, and boxes
via `Long.valueOf` on every iteration, and values outside -128..127
allocate a new `Long`. A `long` local does not.

**Use when.**

- A loop accumulates into a wrapper-typed local or field (`Long`,
  `Integer`, `Double`), often left by a generic API or an IDE refactor.

**Do not use when.**

- Callers depend on the wrapper's `null` meaning "no value yet": keep
  those semantics with an explicit flag or `OptionalLong`.

**Example.**

```java
public static Long boxedAccumulator(int[] values) {
    Long total = 0L;
    for (int value : values) {
        total += value;                  // Long.valueOf each time
    }
    return total;
}

public static long primitiveAccumulator(int[] values) {
    long total = 0L;
    for (int value : values) {
        total += value;
    }
    return total;
}
```

Runnable: `Allocation.Boxing`, benchmarks `boxedAccumulator` and
`primitiveAccumulator` (values 1..1,000).

**Cost removed.** One 24-byte `Long` per iteration once the total leaves
the cache. Measured: 23,640 B/op versus 0.007 B/op; 5,863 ± 1,302 ns/op
versus 956 ± 2,261 ns/op (the second interval is too wide for a time
claim). Escape analysis did **not** remove these boxes on JDK 25.

**Verify.**

1. `Verify.allocation()` checks equal totals.
1. JMH `-prof gc`: `boxedAccumulator` shows about 24 B per element.

## Integer cache and boxed identity

**Definition.** JLS [5.1.7][jls-boxing] guarantees that boxing an `int`
in -128..127 yields the same object every time. Outside that range,
`Integer.valueOf` may return distinct objects. HotSpot sizes the cache
with the C2 flag `-XX:AutoBoxCacheMax`, whose default prints as 128 here,
but HotSpot passes it to `Integer.IntegerCache` (as the property
`java.lang.Integer.IntegerCache.high`) only when the flag is set
explicitly ([`arguments.cpp`][jdk-args]). Otherwise the cache ends at 127,
so `Integer 128 == 128` printed `false` locally. `==` on boxes compares
references.

**Use when.**

- Reviewing a change that replaces `.equals` with `==` for speed, or that
  introduces boxed values into comparisons. This is a correctness card.

**Do not use when.**

- Never compare boxed numbers for value with `==` or `!=`: it passes
  tests that use small numbers and fails in production with larger ones.

**Example.**

```java
Integer small1 = 127;
Integer small2 = 127;
Integer big1 = 1_000;
Integer big2 = 1_000;
boolean cached = small1 == small2;      // true: JLS 5.1.7 guarantee
boolean same = big1 == big2;            // false here: separate objects
boolean equal = big1.equals(big2);      // true: value comparison
```

Runnable: `Verify.allocation()` (the `integer-cache` checks).

**Cost removed.** A latent bug, not time. Local verification output:
`128 == 128 is false`, `1000 == 1000 is false`.

**Verify.**

1. `sh assets/examples/verify.sh verify` prints the `INFO integer-cache`
   line and asserts that `.equals` is true.
1. Static check: Error Prone's [BoxedPrimitiveEquality][ep-boxed]
   (default severity ERROR) flags `==` between boxed primitives. Run it
   if the build has Error Prone; otherwise review each `==` on a
   wrapper-typed variable.

## Presized ArrayList

**Definition.** `new ArrayList<>()` starts with capacity 10 and grows by
copying into a larger array. `new ArrayList<>(n)` allocates the final
array once ([ArrayList][arraylist]).

**Use when.**

- The final size, or a tight upper bound, is known before the loop, and
  the list is built on a hot path.

**Do not use when.**

- The size is unknown or usually much smaller than the bound: the array
  is allocated at full size anyway, wasting memory.

**Example.**

```java
List<Integer> list = new ArrayList<>(n);   // one array of n slots
for (int i = 0; i < n; i++) {
    list.add(i & 127);                      // cached Integer values
}
```

Runnable: `Allocation.Presize.listPresized`, benchmarks `listDefault` and
`listPresized` (1,000 elements).

**Cost removed.** Growth copies: 15,024 B/op to 4,040 B/op
(`gc.alloc.rate.norm`). Time: 5,830 ± 1,227 versus 5,081 ± 549 ns/op
with 3 forks, **no measurable difference**. The benefit is allocation
and GC pressure.

**Verify.**

1. `Verify.allocation()` checks equal lists for 0, 1, 7, and 1,000
   elements.
1. `measure` asserts `listDefault:listPresized`.

## HashMap newHashMap sizing

**Definition.** `HashMap.newHashMap(int numMappings)` (JDK 19+) returns a
map sized to hold `numMappings` entries without resizing at the default
load factor 0.75. `new HashMap<>(n)` takes a *capacity*, so it resizes
once `n` exceeds 0.75 x the power-of-two table size ([HashMap][hashmap]).
JDK 25's implementation computes `ceil(numMappings / 0.75)`
([HashMap.java][hashmap-src]).

**Use when.**

- The number of entries is known before filling (copying, indexing,
  grouping a known input). JDK 19 added the matching factories
  `HashSet.newHashSet`, `LinkedHashMap.newLinkedHashMap`, and
  `LinkedHashSet.newLinkedHashSet`.

**Do not use when.**

- The target JDK is below 19: pass `(int) Math.ceil(n / 0.75)` to the
  constructor instead.
- The expected size is far above the real size: the table is allocated
  at full size.

**Example.**

```java
Map<Integer, Integer> map = HashMap.newHashMap(keys.length);
for (Integer key : keys) {
    map.put(key, key);
}
```

Runnable: `Allocation.Presize`, benchmarks `mapDefault`, `mapCapacityArg`,
`mapNewHashMap` (1,000 keys).

**Cost removed.** Table resizes, counted by reading the table length
after each `put` (`Verify.hashMapResizes`, needs
`--add-opens java.base/java.util=ALL-UNNAMED`):

| n | `new HashMap<>()` | `new HashMap<>(n)` | `newHashMap(n)` |
| --- | --- | --- | --- |
| 700 | 6 | 0 | 0 |
| 1,000 | 7 | 1 | 0 |
| 10,000 | 10 | 0 | 0 |

`new HashMap<>(n)` resizes only when `n` lands above 0.75 of its
power-of-two capacity (1,000 > 768). Allocation for 1,000 keys: 48,496
B/op (default), 44,368 B/op (capacity argument), 40,256 B/op
(`newHashMap`). Time with 3 forks: 24,794 ± 22,205 (default), 14,542 ±
6,653 (capacity argument), 4,781 ± 701 ns/op (`newHashMap`). Only the
last pair's intervals separate, and the machine was loaded.

**Verify.**

1. `Verify.hashMapResizes()` asserts equal maps and zero resizes for
   `newHashMap`, and prints the `RESIZES` lines.
1. `measure` asserts `mapDefault:mapNewHashMap` and
   `mapCapacityArg:mapNewHashMap` (5% margin).

## Records as composite map keys

**Definition.** A `record Key(String tenant, int id)` derives `equals`
and `hashCode` from its components: reference components compare with
`Objects.equals`, primitives with the wrapper's `compare`
([Record][record]). As a key, it replaces building a concatenated
`String` per lookup.

**Use when.**

- Lookups build a key string (`tenant + ":" + id`) on the hot path, and
  the allocation shows in `gc.alloc.rate.norm` or JFR allocation samples.
- Separator ambiguity is a risk: string keys collide when a component
  can contain the separator; record components cannot.

**Do not use when.**

- A component is an array: record equality uses the array's identity
  `equals`, so equal contents do not match (checked in `Verify`). Wrap it
  in a `List` or store a copy with content-based equality.
- A component is mutable and changes after insertion: lookups can no
  longer reach the entry.
- The key must be persisted or sent as text: the `hashCode` algorithm is
  unspecified and may change ([Record][record]).

**Example.**

```java
public record Key(String tenant, int id) {
}

public static long lookupRecord(Map<Key, Integer> map,
        String[] tenants, int[] ids) {
    long sum = 0;
    for (int i = 0; i < ids.length; i++) {
        sum += map.get(new Key(tenants[i], ids[i]));
    }
    return sum;
}
```

Runnable: `Allocation.Keys`, benchmarks `keyLookupString` and
`keyLookupRecord` (1,000 lookups).

**Cost removed.** The key string per lookup: 56,000 B/op to 0.230 B/op,
so in C2 code the lookup `Key` itself never reached the heap;
133,975 ± 60,580 ns/op versus 33,117 ± 25,677 ns/op.

**Verify.**

1. `Verify.recordKeys()` checks equal lookup sums, record
   `equals`/`hashCode` across distinct `String` instances, and that array
   components compare by identity.
1. `measure` asserts `keyLookupString:keyLookupRecord`.

## Streams versus loops with collection

**Definition.** A stream pipeline (`filter`, `mapToLong`, `boxed`,
`collect`) builds pipeline stage objects and lambdas, and collects into
a list that grows from default capacity. An equivalent loop can presize
the result.

**Use when.**

- A hot path shows stream stage allocation or `ArrayList.grow` under a
  `collect`, and the loop is equally clear.

**Do not use when.**

- The pipeline uses `parallel()`, short-circuiting (`findFirst`,
  `anyMatch`), or `sorted`/`distinct`: a hand loop must reproduce the
  ordering and short-circuit semantics exactly.
- There is no measured cost in your code: the time difference was not
  consistently measurable here.

**Example.**

```java
public static List<Long> squaresStream(int[] values) {
    return Arrays.stream(values)
        .filter(v -> v > 0)
        .mapToLong(v -> (long) v * v)
        .boxed()
        .collect(Collectors.toList());
}

public static List<Long> squaresLoop(int[] values) {
    List<Long> result = new ArrayList<>(values.length);
    for (int v : values) {
        if (v > 0) {
            result.add((long) v * v);
        }
    }
    return result;
}
```

Runnable: `Allocation.Pipelines`, benchmarks `squaresStream` and
`squaresLoop`.

**Cost removed.** Allocation: stream 16,296 to 16,360 B/op across three
runs, loop 13,208 B/op. Most of both is the `Long` boxes the contract
requires. Time (stream versus loop): first run (1 fork)
5,256 ± 3,567 versus 2,936 ± 2,886 ns/op, overlapping; second run
(3 forks) 3,421 ± 372 versus 1,697 ± 99 ns/op.

**Verify.**

1. `Verify.allocation()` compares both lists (order included) for 0, 1,
   7, and 1,000 inputs.
1. `measure` asserts `squaresStream:squaresLoop`.

## Primitive stream reductions

**Definition.** `IntStream.of(values).filter(...).asLongStream().sum()`
reduces without boxing, but still creates the pipeline objects on every
call.

**Use when.**

- Readability matters and the call is not in a measured hot loop: the
  cost is a few hundred bytes per call, not per element.

**Do not use when.**

- The reduction runs millions of times per second on small arrays, and
  allocation rate is the problem: a loop allocates nothing.

**Example.**

```java
public static long sumStream(int[] values) {
    return IntStream.of(values).filter(v -> v > 0)
        .asLongStream().sum();
}
```

Runnable: `Allocation.Pipelines.sumStream` versus `sumLoop`.

**Cost removed.** Measured per call over 1,000 elements: 336 B/op
(stream) versus 0.004 B/op (loop). Time: **no measurable difference**
(585 ± 279 and 603 ± 85 ns/op stream; 507 ± 50 and 678 ± 192 ns/op
loop, two runs).

**Verify.**

1. `Verify.allocation()` compares both sums.
1. JMH `-prof gc` on `sumStream` and `sumLoop`.

[jep280]: https://openjdk.org/jeps/280
[jls-boxing]: https://docs.oracle.com/javase/specs/jls/se25/html/jls-5.html#jls-5.1.7
[jdk-args]: https://github.com/openjdk/jdk/blob/jdk-25%2B36/src/hotspot/share/runtime/arguments.cpp
[arraylist]: https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/ArrayList.html
[hashmap]: https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/HashMap.html#newHashMap(int)
[hashmap-src]: https://github.com/openjdk/jdk/blob/jdk-25%2B36/src/java.base/share/classes/java/util/HashMap.java
[record]: https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/Record.html#equals(java.lang.Object)
[ep-boxed]: https://errorprone.info/bugpattern/BoxedPrimitiveEquality
[example-src]: ../assets/examples/jmh/src/main/java/example/Allocation.java
[bytecode-info]: https://github.com/openjdk/jdk/blob/jdk-25%2B36/src/hotspot/share/opto/bytecodeInfo.cpp
