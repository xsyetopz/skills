# Java Performance Gotchas

Read [jvm](jvm.md) first for JMH, JIT, GC, and JFR. This file covers Java code itself.

## Allocation and Strings

- Mistake: string `+=` or `String.format` in a loop. Fix: one `StringBuilder` sized with the
  expected capacity. A single `a + b + c` expression is fine: javac compiles it with `invokedynamic`
  (`StringConcatFactory`) since Java 9.
- Mistake: `String.split`, `substring`, and regex per record in a parser. Fix: scan with `indexOf`
  and `charAt` into the original string, or parse bytes directly. `String.split` has a fast path
  only for one-character non-regex delimiters. Compile `Pattern` once as a `static final` field.
- Mistake: `List<Integer>` and `Map<Long, V>` on a hot path. Fix: primitive arrays, or a primitive
  collections library after measuring; boxing allocates outside the `Integer` cache (-128 to 127)
  and costs a pointer hop per element.
- Mistake: `==` on boxed values after boxing removal. Fix: compare with `equals` or unbox; `==` on
  `Integer` works only inside the cache range, which hides bugs.
- Mistake: `Stream` with `boxed()` or `collect` in a hot loop. Fix: a loop, or
  `IntStream`/`LongStream` without boxing. Do not rewrite cold code, and keep the same encounter
  order and null and exception behavior.
- Mistake: using a `HashMap` keyed by a type with a poor `hashCode`, or keys mutated after
  insertion. Fix: check bucket collisions with a profile; include all identity fields, and make keys
  immutable. Size maps with `HashMap.newHashMap(n)` (Java 19) or
  `new HashMap<>((int) (n / 0.75f) + 1)` to avoid resizing; the constructor argument is capacity,
  not element count.
- Mistake: `ArrayList.remove(0)` or `contains` on a list in a loop. Fix: an `ArrayDeque` or a
  `HashSet`; `ArrayList.contains` is O(n).
- Mistake: `Optional` or wrapper objects allocated per element. Fix: return a sentinel or use null
  inside private hot code. Escape analysis only removes them when the call inlines, so verify with
  `-prof gc`.
- Mistake: `String.intern()` to save memory. Fix: use a bounded map or `-XX:+UseStringDeduplication`
  with G1 after measuring; intern tables add contention and their size is hard to bound.

## Code Generation

- Mistake: manual loop unrolling. Fix: C2 unrolls and vectorizes simple counted loops with `int`
  indexes and no calls; the usual blockers are a `long` loop variable in older JDKs, a call inside
  the loop, or non-inlined array-store checks. Check with `-XX:+PrintAssembly` (needs hsdis) or JMH
  `-prof perfasm`.
- Mistake: catching exceptions for control flow in a hot path. Fix: exceptions capture a stack
  trace, which is costly. Return a result or preallocate and override `fillInStackTrace` only for
  private control-flow exceptions.
- Mistake: `synchronized` replaced with `volatile` or a `ConcurrentHashMap` without analysis. Fix:
  `volatile` gives visibility, not atomic check-then-act. Use `compute`/`merge` on
  `ConcurrentHashMap`, `LongAdder` for contended counters, and never perform long work inside
  `compute`.
- Mistake: array-of-objects traversal in a hot loop. Fix: parallel primitive arrays for the hot
  fields; locality matters more than the object abstraction once the profile points at cache misses.
- Mistake: virtual-thread or executor changes for CPU-bound code. Fix: virtual threads help blocking
  I/O concurrency; they do not speed CPU work, and pinning on `synchronized` (before Java 24) can
  starve the carrier threads.

## Startup and Runtime

- Mistake: optimizing code when startup is slow. Fix: measure with `-Xlog:class+load` and `-Xshare`;
  AppCDS archives (`-XX:ArchiveClassesAtExit`, Java 13+) and reducing classpath scanning and
  reflection usually win more than code changes.
- Mistake: adding JVM flags copied from a blog. Fix: each flag needs a log or profile that motivates
  it, recorded with the JDK version; defaults change between releases and stale flags can be ignored
  or harmful.
- Mistake: benchmarking on one JDK and deploying on another. Fix: test on the production vendor and
  major version; C2 heuristics and GC defaults change per release.

## Concurrency

- Mistake: a shared `ThreadLocalRandom`, `SimpleDateFormat`, or `Random` across threads. Fix:
  `ThreadLocalRandom.current()` at the use site (never stored in a field or shared);
  `DateTimeFormatter` is thread-safe and `SimpleDateFormat` is not.
- Mistake: false sharing between hot fields updated by different threads. Fix: `@Contended` needs
  `-XX:-RestrictContended` outside the JDK; prefer `LongAdder` or per-thread state merged at the
  end.
- Mistake: sizing a thread pool to the CPU count for blocking I/O. Fix: an I/O-bound pool needs more
  threads than cores, or virtual threads (Java 21); a CPU-bound pool should stay near the core
  count.
