# Build-setting constructs

A compiler mode changes every function in a module, so each card here
needs an application-level measurement, not only a microbenchmark.
Evidence comes from `sh assets/examples/verify.sh build|wmo|asm`, measured
on an Apple M1 Max, macOS 27.0, Apple Swift 6.3.3 through `xcrun`.

On this toolchain `xcrun swift build -c release -v` passes
`-O -whole-module-optimization -enable-default-cmo` to every module. Read
the same line for the project before changing flags.

## Contents

- Release builds with -O
- -Osize
- -Ounchecked
- Whole-module optimization
- Cross-module optimization and library evolution
- -enforce-exclusivity=unchecked

## Release builds with -O

**Definition.** `-Onone` is the development mode ("minimal optimizations
and preserves all debug info"); `-O` "prioritizes performance over code
size" ([Optimization tips][tips]). `swift build -c release` selects `-O`
plus WMO; the default `swift build` is a debug build, which the
[server build guide][server] calls "significantly slower".

**Use when.**

- Recording or comparing any performance number: build baseline and
  candidate with `-c release` (or the Xcode Release configuration) and
  identical flags.

**Do not use when.**

- Debugging a crash that the optimizer hides: use `-Onone` for the
  debugger, never for timing.

**Example.**

```sh
xcrun swift build -c release -v 2>&1 |
  grep -oE ' -O[a-z]*| -whole-module-optimization| -enable-default-cmo' |
  sort | uniq -c
```

**Cost removed.** Debug-build overhead in every function (no inlining,
no specialization, no ARC optimization). Every other card in this skill
was measured in release mode only.

**Verify.**

1. The command above lists `-O` and `-whole-module-optimization` for the
   targets you measure.
1. The benchmark or harness output states the configuration
   (package-benchmark always builds release).

## -Osize

**Definition.** `-Osize` optimizes like `-O` but "target[s] small code
size" (`swiftc -help`); the [Optimization tips][tips] describe it as
"meant for most production code". SwiftPM passes it with
`-Xswiftc -Osize` (it appears after `-O` on the command line and
wins).

**Use when.**

- Binary size, download size, or instruction-cache pressure is a stated
  goal (mobile apps, many small tools).
- Measurement shows the hot paths stay within the time budget.

**Do not use when.**

- A measured hot loop depends on inlining or unrolling that `-Osize`
  gives up. Time the application in both modes first.

**Example.**

```sh
xcrun swift build -c release -Xswiftc -Osize
xcrun size -m .build/release/Catalog | grep 'Segment __TEXT'
```

**Cost removed.** Code size. Measured: `Catalog __TEXT` is 131072 bytes
with `-O` and 114688 bytes with `-Osize`, and the `-Osize` build still
passes `verify`. No timing was recorded for this card.

**Verify.**

1. `sh assets/examples/verify.sh build` prints both sizes and runs the
   `-Osize` build's oracles.
1. Time the application workload under both modes before switching.

## -Ounchecked

**Definition.** `-Ounchecked` compiles "with optimizations and remove[s]
runtime safety checks" (`swiftc -help`): integer overflow traps and
preconditions that would trap under `-O` are removed, so a violated
check becomes undefined behavior instead of a crash.

**Use when.**

- Not for a whole module. Use the local, defined alternatives instead:
  wrapping operators (`&+`, `&*`) where overflow is proven impossible or
  wrapping is intended ([Wrapping arithmetic][wrapping]), and the
  unsafe-buffer cards with a written proof.

**Do not use when.**

- Any input can overflow or violate a precondition: the program keeps
  running with a wrong value. Measured: `Overflow.swift` exits with status
  133 (SIGTRAP) under `-O`, and exits 0 printing a wrapped value under
  `-Ounchecked`.

**Example.** Runnable: `assets/examples/overflow/Overflow.swift`.

```swift
@inline(never)
func addAll(_ values: [Int]) -> Int {
    var total = 0
    for v in values { total += v }  // traps on overflow under -O
    return total
}
```

**Cost removed.** The overflow branch: `sumChecked` has one `b.vs` under
`-O` and none under `-Ounchecked` (`sh verify.sh asm`). The safe
`&+` form removes the same branch in one function.

**Verify.**

1. `sh assets/examples/verify.sh build` asserts the `-O` binary traps
   (status 133). It deliberately does not check the `-Ounchecked` value.
1. `sh assets/examples/verify.sh asm` asserts the branch count.

## Whole-module optimization

**Definition.** `-whole-module-optimization` (`-wmo`) compiles all files
of a module as one unit, so the optimizer sees every use of `internal`
declarations: it can specialize generics defined in another file and
infer `final` for internal classes without subclasses
([WMO blog][wmo-blog], [Optimization tips][tips]). SwiftPM release
builds and Xcode's default Release setting use it.

**Use when.**

- A custom build (Makefile, Bazel, direct `swiftc`) compiles release
  files separately, and SIL shows `class_method` calls or unspecialized
  generic calls across files.

**Do not use when.**

- Debug builds: incremental per-file compilation iterates faster.
- The build already uses WMO (check `-v`).

**Example.** Runnable: `assets/examples/wmo/Counter.swift` and
`Use.swift`.

```swift
// Counter.swift
class Counter {
    var count = 0
    func bump(_ by: Int) { count &+= by }
}

// Use.swift
@inline(never)
public func countAll(_ values: [Int]) -> Int {
    let counter = Counter()
    for v in values { counter.bump(v) }
    return counter.count
}
```

**Cost removed.** Vtable calls and generic dictionaries across files.
Measured SIL: per-file compilation of `Use.swift` has 2 `class_method`
instructions and 1 unspecialized `sumMapped` reference; `-wmo` has 0 and
0. The WMO blog reports gains "up to two or even five times" for its
examples; this skill did not measure a speedup.

**Verify.**

1. `sh assets/examples/verify.sh wmo` prints both counts and `WMO PASSED`.
1. Run the project's tests with the WMO build; behavior must not change.

## Cross-module optimization and library evolution

**Definition.** Without help, a function body is invisible outside its
module. Cross-module optimization (CMO) serializes bodies into the
`.swiftmodule` automatically; SwiftPM passes `-enable-default-cmo`
(conservative CMO), and `-cross-module-optimization` serializes more
([server build guide][server]). `-enable-library-evolution` (resilient
modules, [SE-0260][se260]) disables that: only `@inlinable` bodies and
`@frozen` layouts cross the boundary.

**Use when.**

- A hot loop calls small functions from another module and the assembly
  shows `bl _$s6Helper...` calls. First check which of the two cases
  applies.

**Do not use when.**

- Both modules build from source in one SwiftPM graph: default CMO
  already inlines the call (measured: `scaleAllOpaque` has 0 calls to
  `helperScale`), so `@inlinable` changes nothing.
- Untested `-cross-module-optimization`: the server guide warns "it may
  sometimes cause performance regressions"; measure it.

**Example.** From `verify.sh asm`:

```sh
xcrun swiftc -O -wmo -parse-as-library -enable-library-evolution \
  -module-name Helper -emit-module \
  -emit-module-path evo/Helper.swiftmodule Helper.swift
xcrun swiftc -O -wmo -parse-as-library -module-name Constructs \
  -I evo -emit-assembly Sources/Constructs/*.swift -o evo.s
```

**Cost removed.** A call per element. Measured: with library evolution,
`scaleAllOpaque` calls `helperScale` (1 site) and `scaleAllInlinable`
calls nothing; with default CMO neither calls. SwiftPM build timing:
1180.8 ns versus 1194.8 ns, no difference, as expected for identical
bodies.

**Verify.**

1. `sh assets/examples/verify.sh asm` asserts all three cases.
1. For a real library, emit assembly of the client with the library's
   shipped `.swiftmodule`/`.swiftinterface`, not a source build.

## -enforce-exclusivity=unchecked

**Definition.** Swift 5 enforces exclusive access at run time in release
builds for "escaping closures, properties of class types, static
properties, and global variables"; `-enforce-exclusivity=unchecked`
removes those runtime checks ([exclusivity blog][excl], [SE-0176][se176]).

**Use when.**

- Not recommended. The blog says disabling run-time checks in Release
  builds "is strongly discouraged because, if the program violates
  exclusivity, then it could exhibit unpredictable behavior, including
  crashes or memory corruption."

**Do not use when.**

- Any code path might overlap accesses (re-entrant callbacks, `inout`
  of a class property passed to a closure that reads it).
- The profile does not show `swift_beginAccess`. Measured: `-O` already
  widened the access in `accumulateProperty` to one check for the whole
  loop, so the flag removes only two calls per invocation.

**Example.**

```sh
xcrun swiftc -O -wmo -enforce-exclusivity=unchecked -parse-as-library \
  -module-name Constructs -emit-assembly Sources/Constructs/*.swift \
  -o noexcl.s
```

**Cost removed.** `swift_beginAccess` calls: `accumulateProperty` 2 -> 0,
`countWithEscapingCapture` 2 -> 0 (static sites). Prefer the local fix in
[Exclusivity](memory.md#local-accumulator-instead-of-a-class-property).

**Verify.**

1. `sh assets/examples/verify.sh asm` asserts the counts in `noexcl.s`.
1. Run the full test suite with the flag; a passing suite does not prove
   the absence of overlapping accesses.

[tips]: https://github.com/swiftlang/swift/blob/main/docs/OptimizationTips.rst
[server]: https://www.swift.org/documentation/server/guides/building.html
[wmo-blog]: https://www.swift.org/blog/whole-module-optimizations/
[se260]: https://github.com/swiftlang/swift-evolution/blob/main/proposals/0260-library-evolution.md
[excl]: https://www.swift.org/blog/swift-5-exclusivity/
[se176]: https://github.com/swiftlang/swift-evolution/blob/main/proposals/0176-enforce-exclusive-access-to-memory.md
[wrapping]: memory.md#wrapping-arithmetic
