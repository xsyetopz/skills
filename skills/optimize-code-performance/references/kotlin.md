# Kotlin performance gotchas

Read [jvm](jvm.md) for JMH, JIT, GC, and JFR. Measure with `kotlinx-benchmark` (JMH underneath) and
inspect bytecode with `javap -c -p` on the compiled classes or Tools > Kotlin > Show Kotlin
Bytecode. Kotlin/Native and Kotlin/JS are out of scope.

## Collections and sequences

- Mistake: chaining `map`, `filter`, and `flatMap` on a `List` in a hot path. Fix: each step builds
  an intermediate list. Use a single loop or `asSequence()` for long chains over large inputs, but
  do not use sequences for short lists: they allocate iterators and lambdas, and measure slower on
  small collections. Sequences are lazy, so side effects and exceptions change order; evaluate the
  terminal operation once.
- Mistake: `list.size` and `first()` inside a loop condition on a lazy view. Fix: hoist to a `val`;
  some `Iterable` operations re-evaluate.
- Mistake: `list.toMutableList()` or `+` to append in a loop. Fix: `+` on a `List` copies the whole
  list each time (quadratic). Use an `ArrayList`/`buildList`, preallocated with a capacity when
  known.
- Mistake: `Map<Int, V>` and `List<Int>` in hot code. Fix: `IntArray` and primitive-specialized
  structures; `List<Int>` boxes every element. `Array<Int>` also boxes; `IntArray` does not.
- Mistake: `mapOf`/`setOf` per call in a function. Fix: hoist to a `private val` (or
  `companion object` constant); they allocate on every call.
- Mistake: `String` building with `+` in loops and `String.format`. Fix: `buildString { }` (a
  `StringBuilder`); a single template `"$a$b"` is compiled to a `StringBuilder` (or `invokedynamic`
  on newer targets), which is fine.
- Mistake: `Regex("...")` constructed in a function. Fix: a top-level `private val`; `toRegex()`
  compiles each time it runs.

## Representation and inline

- Mistake: nullable primitives (`Int?`) and generics boxing in hot code. Fix: `Int` (non-null) is a
  JVM `int`; `Int?`, `List<Int>`, and generic type parameters use `Integer`. Use a sentinel value or
  a specialized class for the hot path.
- Mistake: `value class` (inline class) assumed to be free. Fix: it is unboxed in most positions but
  boxes when used as a generic, nullable, or interface type; check the bytecode. Value classes with
  a `List<MyId>` box each element.
- Mistake: `inline` on every function taking a lambda. Fix: `inline` helps higher-order functions
  called with lambdas (it removes the lambda object) and bloats code for large bodies; use
  `noinline`/`crossinline` deliberately, and never mark a function with no function parameters
  `inline` for speed (the compiler warns).
- Mistake: `data class` copy in a tight loop. Fix: `copy()` allocates; mutate a local `var` or a
  builder in private code, and keep the public type immutable.
- Mistake: `lazy { }` on a hot field. Fix: default `lazy` is synchronized with a double check on
  every read; use `lazy(LazyThreadSafetyMode.NONE)` only when single-threaded is guaranteed, or
  `lateinit`/initialization at construction.
- Mistake: delegated properties (`by`) and `Delegates.observable` in hot objects. Fix: each delegate
  is an extra object plus an indirect call; use plain properties where profiling shows the cost.
- Mistake: `when` on strings in a hot path assumed slow. Fix: Kotlin compiles it to a hash `switch`;
  leave it unless the profile says so. Enums give `ordinal`-based tables, while `values()` copies
  its array on each call (use `entries` from Kotlin 1.9).
- Mistake: `!!`, `as`, and `require` removed for speed. Fix: they are cheap checks; keep them unless
  the profile shows them.

## Coroutines

- Mistake: launching a coroutine per item for CPU work. Fix: coroutines give concurrency, not
  parallelism; CPU-bound work needs `Dispatchers.Default` (sized to the core count), batching, and a
  bounded degree of concurrency (`Semaphore`, `limitedParallelism`, or a `Channel` with worker
  count).
- Mistake: blocking calls (`Thread.sleep`, JDBC, `runBlocking`) on `Dispatchers.Default` or `Main`.
  Fix: wrap blocking work in `withContext(Dispatchers.IO)`; `IO` and `Default` share a pool, so
  blocking calls on `Default` starve CPU work. Use `Dispatchers.IO.limitedParallelism(n)` to bound
  one resource.
- Mistake: `runBlocking` inside a coroutine or request handler. Fix: suspend all the way; it blocks
  a thread and can deadlock a single-threaded dispatcher.
- Mistake: `Flow` operators per item on a hot stream, or `Flow` where a suspend function returns a
  `List`. Fix: a `Flow` adds a coroutine and per-emission state machine cost; use `buffer()` or
  `conflate()` to decouple a slow collector, and batch items before emitting them.
- Mistake: `suspend` functions that never suspend in a hot loop. Fix: each call allocates a
  continuation only when it actually suspends, so check the profile; making a function `suspend` for
  no reason still costs a state machine in the bytecode.
- Mistake: `async { }.await()` immediately. Fix: call the function directly, or `coroutineScope`
  with parallel `async`s that are awaited together (`awaitAll`).
- Mistake: `GlobalScope` and unstructured launches for throughput. Fix: structured scopes; leaked
  coroutines show up as growing heap and thread counts, and a cancelled parent should cancel
  children.
