# Scala performance gotchas

Read [jvm](jvm.md) for JMH (`sbt-jmh`), JIT, GC, and JFR. Inspect what
scalac emitted with `javap -c -p` on the class files; many costs below
only show there. Names and behavior differ between Scala 2.13 and 3, so
check the compiler version first.

## Collections

- Mistake: chained `map`, `filter`, `flatMap` on strict collections in a
  hot path. Fix: each step builds a collection. Use `.view` (2.13+) or
  an `Iterator` for long chains, or one `while` loop; views re-evaluate
  on every traversal, so call `.toVector` or similar once and keep it.
- Mistake: `List` with `apply(i)`, `length`, `:+`, or `++` in a loop. Fix:
  those are O(n) on a linked list. Use `Vector` for indexed access and
  `ArrayBuffer` or a builder (`Vector.newBuilder`) when appending.
- Mistake: `for` comprehensions over ranges in hot loops. Fix: a `for`
  desugars to `foreach`/`map` with a closure; on Scala 2.13 a
  `Range.foreach` over `Int` is specialized, but nested generators and
  guards allocate closures. Write a `while` loop (or `@tailrec`
  function) in the profiled hot spot only.
- Mistake: `Array[Int]` wrapped into a generic API. Fix: a generic
  `Array[T]` without `ClassTag` cannot be created, and passing arrays as
  `Seq` wraps them. `Seq(1, 2, 3)` allocates and boxes. Use primitive
  arrays inside the hot function and convert at the boundary.
- Mistake: `Map[Int, V]` and `List[Int]`/`Seq[Double]` boxing. Fix:
  Scala's generic collections box primitives; `@specialized` covers few
  standard classes. Use primitive arrays, or a primitive-specialized
  collection library after measuring.
- Mistake: `toList`, `toSeq`, `toSet` conversions at function boundaries.
  Fix: each one copies. Accept `Iterable`/`IterableOnce` or return the
  collection you built.
- Mistake: `mutable.Map` default capacity for big maps. Fix: use
  `mutable.HashMap.newBuilder` or `new HashMap(initialCapacity, loadFactor)`
  with a known size, and `mutable.Map.getOrElseUpdate` instead of
  `get` followed by `put`.
- Mistake: `String` concatenation and `s"..."` interpolation in loops. Fix:
  `StringBuilder`. A single interpolation is fine; interpolation compiles
  to a `StringContext` call or builder, not `String.format`.
- Mistake: `Option` per element. Fix: `Option` allocates a `Some` per
  present value; in a hot inner loop use a sentinel, `null` inside a
  private scope, or `Iterator.nextOption` patterns as a profile shows.
- Mistake: parallel collections as a speedup. Fix: in 2.13 they are a
  separate module (`scala-parallel-collections`), add overhead for small
  work, and need side-effect-free associative operations. Use a
  parallelism measure on real sizes.

## Language features

- Mistake: `case class` used as a map key with many fields in a hot
  loop, or large `copy` chains. Fix: the generated `hashCode` and
  `equals` walk all fields, and `copy` allocates. Hash the fields you need
  once, or use a smaller key.
- Mistake: `lazy val` in hot objects. Fix: a `lazy val` uses a synchronized
  bitmap check on every read in Scala 2; Scala 3 uses a different
  scheme, so check the compiler. Initialize eagerly when cheap.
- Mistake: `implicit class` and extension methods in inner loops. Fix: an
  `implicit class` allocates a wrapper unless it `extends AnyVal` (2.x)
  and the wrapper does not escape; Scala 3 extension methods do not
  allocate.
- Mistake: `AnyVal` value classes treated as free. Fix: they box when used
  as a generic, in collections, in `Option`, or as a `Seq` element, and
  in `equals` through interfaces. In Scala 3, opaque types have no
  runtime wrapper at all, but boxing still applies when used generically.
- Mistake: Scala 3 `inline` def or `inline` parameters for speed. Fix:
  `inline` is a guaranteed compile-time expansion and can bloat code; use
  it for constant folding and avoiding closure allocation with
  small bodies, then read the bytecode. `@inline` in Scala 2 is only a
  hint honored with `-opt:inline`.
- Mistake: pattern matching on `Any` with type tests in a hot path. Fix:
  sealed ADTs compile to `instanceof` chains or a tag switch; put the
  most frequent case first and check that no default allocates an
  extractor object (`Some(x)` extractor patterns for `unapply`
  allocate).
- Mistake: `@tailrec` omitted on a loop-shaped recursion. Fix: the
  annotation makes the compiler fail instead of silently not optimizing.
  Mutual and non-final recursion are not optimized.
- Mistake: by-name parameters (`=> A`) on hot functions. Fix: each one
  allocates a `Function0` unless inlined; pass a value, or use `inline`.
- Mistake: `Try`, `Either`, and `Future` per item. Fix: they allocate on
  every step; use exceptions only for the rare path, and batch `Future`
  work, since every `map` schedules a task on the execution context.

## Concurrency

- Mistake: blocking inside `Future.apply` on the global
  `ExecutionContext`. Fix: wrap blocking in `scala.concurrent.blocking`
  or use a dedicated bounded executor; the global pool is sized to the
  cores, so blocked threads starve all other work.
- Mistake: a fresh `ExecutionContext` or `Promise` per call. Fix: create
  executors once; per-call pools leak threads.
- Mistake: `synchronized` on shared collections that are read heavily.
  Fix: an immutable structure behind an `AtomicReference` (copy on
  write) for read-mostly data, or `TrieMap`/`ConcurrentHashMap`; a
  `TrieMap` snapshot is O(1) but its updates allocate.
- Mistake: Akka or effect-system micro-optimizations before checking
  thread-pool configuration. Fix: read the dispatcher or runtime
  configuration and scheduler settings, and profile with JFR.
