# Code generation constructs

Each card changes what C2 can compile: call dispatch, library intrinsics,
or SIMD. Runnable pairs are in
[`Codegen.java`](../assets/examples/jmh/src/main/java/example/Codegen.java),
measured by `CodegenBench` and checked by `Verify.codegen()`.

Measured on: Apple M1 Max, macOS arm64, OpenJDK 25.0.4.1, JMH 1.37 (`-wi
3 -i 5`, 1 s iterations, 1 to 5 forks as stated), shared machine (load
average 4 to 91). Timings are machine-specific; overlapping error bars
mean **no measurable difference**. `final` showed none, and error bars
did not establish the sealed switch: either the JIT already handles the
baseline, or the machine was too noisy to tell.

## Contents

- Final classes and class hierarchy analysis
- Pattern switch over a sealed hierarchy
- Array intrinsics in java.util.Arrays
- Vector API for floating-point reductions

## Final classes and class hierarchy analysis

**Definition.** A `final` class (or `sealed` hierarchy, [JEP 409][jep409])
cannot gain subclasses. HotSpot already demotes virtual calls to direct
calls "if the class hierarchy permits it", registering a dependency "in
case further class loading spoils things". It compiles call sites with a
lopsided type profile with "an optimistic check in favor of the
historically common type (or two types)"
([HotSpot performance techniques][hotspot-perf]).

**Use when.**

- For design: the type is not meant to be extended. Performance alone is
  not a reason; see the measurement below.

**Do not use when.**

- You expect a speedup at a call site with one receiver type: CHA and
  type profiles already inline it (this card's measurement).
- The class is proxied or mocked by subclassing (some frameworks generate
  subclasses at run time): `final` breaks them.

**Example.**

```java
public static class OpenScaler {        // not final, never subclassed
    private final int factor;
    public OpenScaler(int factor) { this.factor = factor; }
    public int apply(int x) { return x * factor + 1; }
}

public static final class FinalScaler { // same body, final
    private final int factor;
    public FinalScaler(int factor) { this.factor = factor; }
    public int apply(int x) { return x * factor + 1; }
}
```

Runnable: `Codegen.Leaf`, benchmarks `leafOpen` and `leafFinal`.

**Cost removed.** None measurable here. Measured, 1,000 calls:
`leafOpen` 681.7 ± 149.6 and 682.9 ± 30.1 ns/op; `leafFinal`
675.0 ± 97.8 and 868.1 ± 213.5 ns/op (two runs, intervals overlap).

**Verify.**

1. `sh assets/examples/verify.sh verify` checks that `open` and `closed`
   return the same sum for 0, 1, 5, and 1,000 elements.
1. `BENCH_FILTER='CodegenBench.leaf' sh assets/examples/verify.sh measure`.
   Treat overlapping error bars as no difference, and do not keep a
   `final`-only change as an optimization.

## Pattern switch over a sealed hierarchy

**Definition.** A `switch` with type patterns over a `sealed` interface
(final in JDK 21, [JEP 441][jep441]) is exhaustive without `default` and
replaces a virtual call with type tests. At a megamorphic call site
(three or more receiver types), C2 cannot inline the virtual call.
Whether the switch is faster is an empirical question.

**Use when.**

- The code benefits from exhaustiveness (the compiler flags a new
  subtype), and a profile shows the call site is megamorphic.

**Do not use when.**

- You expect a speedup without measuring it on the target machine: the
  local result below is suggestive, not established.
- New subtypes come from other modules or plugins: code outside the
  declared `permits` list cannot extend a sealed hierarchy.

**Example.**

```java
public static double switchSum(Shape[] shapes) {
    double sum = 0;
    for (Shape s : shapes) {
        sum += switch (s) {
            case Circle c -> Math.PI * c.r() * c.r();
            case Square q -> q.side() * q.side();
            case Rect r -> r.w() * r.h();
            case Triangle t -> 0.5 * t.b() * t.h();
        };
    }
    return sum;
}
```

Runnable: `Codegen.Shapes`, benchmarks `shapesVirtual` and `shapesSwitch`
over 1,000 shapes cycling through four record types.

**Cost removed.** Possibly the megamorphic dispatch. Means over four runs
flipped under load (`shapesSwitch` 2,593 ± 290, 4,415 ± 2,865,
20,132 ± 18,679, 14,928 ± 12,243 ns/op; `shapesVirtual` 4,243 ± 1,537,
9,208 ± 2,810, 8,767 ± 9,476, 26,564 ± 19,482 ns/op). The fastest
iteration was lower for the switch in every run (2,535 to 2,644 versus
3,709 to 4,090 ns/op), but the 99.9% intervals overlap, so the gain is
**not established**. Rerun on a quiet machine before relying on it.

**Verify.**

1. `sh assets/examples/verify.sh verify` requires bit-identical sums from
   both versions (same expression order per shape).
1. `BENCH_FILTER='CodegenBench.shapes' sh assets/examples/verify.sh
   measure`.

## Array intrinsics in java.util.Arrays

**Definition.** `Arrays.equals(byte[], byte[])` and `Arrays.mismatch`
call `ArraysSupport.mismatch`, which uses `vectorizedMismatch`, annotated
`@IntrinsicCandidate` in JDK 25 ([Arrays.java][arrays-src],
[ArraysSupport.java][arrays-support]). C2 replaces it with a hand-written
vector stub; it does not replace a hand-written early-exit loop.

**Use when.**

- A loop compares, searches, or copies primitive arrays element by
  element (`equals`, `mismatch`, `fill`, `System.arraycopy`,
  `Arrays.copyOf`).

**Do not use when.**

- The loop has extra per-element semantics (a tolerance, a mask, a
  transform): the library method would change the result.
- Arrays may be `null` and the hand-written loop throws on it:
  `Arrays.equals` returns `false` or `true` for `null` instead.

**Example.**

```java
public static boolean manualEquals(byte[] a, byte[] b) {
    if (a.length != b.length) {
        return false;
    }
    for (int i = 0; i < a.length; i++) {
        if (a[i] != b[i]) {
            return false;
        }
    }
    return true;
}

public static boolean libraryEquals(byte[] a, byte[] b) {
    return Arrays.equals(a, b);
}
```

Runnable: `Codegen.Intrinsics`.

**Cost removed.** Per-byte compares and branches. Measured, two equal
4,096-byte arrays: `equalsManual` 909.6 ± 37.8 ns/op, `equalsLibrary`
102.4 ± 62.1 ns/op.

**Verify.**

1. `sh assets/examples/verify.sh verify` compares `equals` and `mismatch`
   results for equal arrays, differences at 0, 17, and 4,095, and
   different lengths.
1. `BENCH_FILTER='CodegenBench.equals' sh assets/examples/verify.sh
   measure`.

## Vector API for floating-point reductions

**Definition.** The Vector API (`jdk.incubator.vector`, tenth incubator
in JDK 25, [JEP 508][jep508]) expresses SIMD explicitly: `FloatVector`
lanes of `SPECIES_PREFERRED`, `fromArray`, `fma`, `reduceLanes`, and
`loopBound` for the scalar tail. It needs `--add-modules
jdk.incubator.vector` at compile and run time and prints
`WARNING: Using incubator modules`.

**Use when.**

- A float/double reduction dominates a profile. C2 must keep the scalar
  sum in sequential order, because floating-point addition is not
  associative ([JLS 15.18.2][jls-add]). The explicitly reassociated
  Vector API version measured 3.4x faster (below).
- The contract tolerates a different rounding order, and the oracle uses
  a tolerance, not bit equality.

**Do not use when.**

- Results must be bit-identical to the scalar loop (checksums, golden
  files, cross-platform reproducibility): lane-wise partial sums change
  the result. The dot product of 1,027 elements measured `924.17865`
  scalar versus `924.17993` vector.
- The loop is integer element-wise work: C2's auto-vectorizer
  (`UseSuperWord = true` by default here) may already emit SIMD, so
  measure the scalar loop first.
- Production cannot ship incubator modules or their warning.

**Example.**

```java
private static final VectorSpecies<Float> SPECIES =
    FloatVector.SPECIES_PREFERRED;

public static float vectorDot(float[] a, float[] b) {
    FloatVector acc = FloatVector.zero(SPECIES);
    int i = 0;
    int bound = SPECIES.loopBound(a.length);
    for (; i < bound; i += SPECIES.length()) {
        FloatVector va = FloatVector.fromArray(SPECIES, a, i);
        FloatVector vb = FloatVector.fromArray(SPECIES, b, i);
        acc = va.fma(vb, acc);
    }
    float sum = acc.reduceLanes(VectorOperators.ADD);
    for (; i < a.length; i++) {
        sum += a[i] * b[i];                  // scalar tail
    }
    return sum;
}
```

Runnable: `Codegen.Simd`. `SPECIES_PREFERRED` had 4 float lanes (128-bit
NEON) on the M1 Max.

**Cost removed.** Scalar dependent adds. Measured, 4,096 floats:
`dotScalar` 4,077.1 ± 351.5 ns/op, `dotVector` 1,214.7 ± 84.3 ns/op.

**Verify.**

1. `sh assets/examples/verify.sh verify` checks
   `|scalar - vector| <= 1e-5 x |scalar|` and prints whether the results
   are bit-equal (they are not). It also checks the regrouping hazard:
   `(1e16 + -1e16) + 1.0 != 1e16 + (-1e16 + 1.0)`.
1. `BENCH_FILTER='CodegenBench.dot' sh assets/examples/verify.sh measure`.

[jep409]: https://openjdk.org/jeps/409
[jep441]: https://openjdk.org/jeps/441
[jep508]: https://openjdk.org/jeps/508
[arrays-src]: https://github.com/openjdk/jdk/blob/jdk-25%2B36/src/java.base/share/classes/java/util/Arrays.java
[arrays-support]: https://github.com/openjdk/jdk/blob/jdk-25%2B36/src/java.base/share/classes/jdk/internal/util/ArraysSupport.java
[hotspot-perf]: https://wiki.openjdk.org/display/HotSpot/PerformanceTechniques
[jls-add]: https://docs.oracle.com/javase/specs/jls/se25/html/jls-15.html#jls-15.18.2
