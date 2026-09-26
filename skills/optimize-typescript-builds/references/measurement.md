# Measurement

These tools attribute TypeScript cost before a construct is chosen and
confirm the change afterwards. Compile-time and runtime cost are separate
claims: measure each with its own tool and never report one as the other.

Local environment: tsc 7.0.2, Node 26.8.2, Bun 1.4.2, Go 1.27.1, Apple M1
Max, macOS.

Tier: Executed for counters, traces with analyze-trace (`verify.sh
trace`, network needed on the first `bunx` fetch), pprof with `go tool
pprof`, file listings, emitted diffs, and timing. Not verified: loading
traces in `about://tracing` and profiles in SpeedScope.

## Contents

- Compiler counters
- Check-phase trace
- Go pprof profiles
- File inclusion diagnostics
- Emitted JavaScript diff
- Runtime timing of emitted code

## Compiler counters

**Definition.** `--extendedDiagnostics` prints program counters (`Files`,
`Lines`, `Identifiers`, `Symbols`, `Types`, `Instantiations`,
`Memory used`, `Memory allocs`) and phase times (`Parse time`,
`Bind time`, `Check time`, `Emit time`, `Total time`) after a build
([Performance wiki][wiki], "extendedDiagnostics"). tsc 7.0.2 prints the
names above; the wiki's `Program time` and `I/O Read time` lines do not
appear.

**Use when.**

- Before any compile-time claim: record the baseline counters.
- Deciding between checker, program-size, and emit work: compare
  `Check time` with `Parse time` and `Emit time`.

**Do not use when.**

- Comparing counters across different `--checkers` values or tsc
  versions: `Types` and `Memory used` change with the worker count (see
  [single-threaded mode][single]).

**Example.**

```sh
tsc -p tsconfig.json --noEmit --singleThreaded --extendedDiagnostics
```

```text
Types:            3094
Instantiations:      1
Memory used:    52261K
Check time:     1.227s
```

**Cost removed.** Guessing which phase dominates. `Types`,
`Instantiations`, and `Symbols` repeated exactly across local runs;
`Check time` varied by 2x or more on the shared machine.

**Verify.**

1. Behavior: the run reports the same error list as the normal build.
1. Benefit: `lib.ts` `diag()` parses these lines; every checker oracle
   prints them as `DIAG name: Types=... Check=...`.

## Check-phase trace

**Definition.** `--generateTrace DIR` writes a Chrome trace-event file and
type dumps. tsc 7.0.2 writes `trace.json`, `legend.json`, and one
`types_N.json` per checker (4 by default, 1 with `--singleThreaded`);
`@typescript/analyze-trace` summarizes hot spots ([Performance
wiki][wiki], "Performance Tracing"; the wiki warns the format "is not
stable").

**Use when.**

- `Check time` dominates and you need the file or expression responsible.

**Do not use when.**

- The trace would be shared publicly without review: it contains file
  paths and source ([Performance wiki][wiki]).

**Example.**

```sh
tsc -p . --noEmit --singleThreaded --generateTrace trace-out
bunx --bun @typescript/analyze-trace@0.11.1 trace-out \
  --forceMillis 50 --skipMillis 5 --color false
```

Local output on the union fixture:

```text
Hot Spots
└─ Check file .../gen/union.ts (672ms)
```

analyze-trace 0.11.1 read both single- and multi-checker tsc 7 traces
locally. It exits 1 when nothing crosses the thresholds (default
`--forceMillis 500 --skipMillis 100`). Chrome or Edge `about://tracing`
also loads `trace.json`.

**Cost removed.** Search time for the costly file or type.

**Verify.**

1. Behavior: `trace-out/trace.json` and `legend.json` exist (asserted by
   `verify.sh checker`).
1. Benefit: `sh assets/examples/verify.sh trace` prints the hot spot
   (needs the network the first time `bunx` fetches the package).

## Go pprof profiles

**Definition.** tsc 7 accepts `--pprofDir DIR` and writes Go
`*-cpuprofile.pb.gz` and `*-memprofile.pb.gz` files for the compiler
itself (listed in `tsc --help --all`; behavior observed locally). The
wiki's `--generateCpuProfile` and pprof-it recipes target the JavaScript
compiler; on tsc 7.0.2 `--generateCpuProfile` wrote no file.

**Use when.**

- Reporting a compiler performance bug upstream, or a trace shows time
  outside checking (parse, emit, file system).

**Do not use when.**

- Attributing cost to your own types: compiler-internal frames
  (`checker.(*Checker).getObjectTypeInstantiation`) name algorithms, not
  your files. Use the trace for that.

**Example.**

```sh
tsc -p . --noEmit --pprofDir pprof-out
go tool pprof -top -nodecount=8 pprof-out/*-cpuprofile.pb.gz
```

**Cost removed.** Unexplained non-check time. Locally, `go tool pprof`
(Go 1.27.1) read the profile and listed `typescript-go/internal/checker`
frames.

**Verify.**

1. Behavior: tsc prints `CPU profile: <path>` and `Memory profile:
   <path>`; the oracle asserts the first line.
1. Benefit: `go tool pprof -top` lists frames; without Go installed, load
   the file in [SpeedScope][speedscope] instead (not verified locally).

## File inclusion diagnostics

**Definition.** `--listFilesOnly` prints the program's files without
checking; `--explainFiles` prints why each file is included (for example
`Entry point for implicit type library 'big'`); `--traceResolution` logs
each module resolution step ([Performance wiki][wiki], "listFilesOnly",
"explainFiles", "traceResolution").

**Use when.**

- `Files` in `--extendedDiagnostics` is larger than the source tree.
- Before applying [scoped include](build.md#scoped-include) or the
  [scoped types array](build.md#scoped-types-array).

**Do not use when.**

- The file count already matches the sources: the cost is elsewhere.

**Example.**

```sh
tsc -p . --listFilesOnly | wc -l
tsc -p . --explainFiles > files.txt
grep -B1 "implicit type library" files.txt
```

**Cost removed.** Files that should not be in the program. The oracle's
include case goes from 133 to 83 listed files.

**Verify.**

1. Behavior: every intended entry point still appears in the listing.
1. Benefit: the line count drops; `Files` drops in `--extendedDiagnostics`.

## Emitted JavaScript diff

**Definition.** Runtime cost from TypeScript syntax is visible only in the
emitted JavaScript: compile baseline and candidate with the project's
effective options (`tsc --showConfig`) to separate directories and diff
them.

**Use when.**

- Any runtime claim about an enum, namespace, decorator, class field,
  `target`, `importHelpers`, or import form (the [emit](emit.md) cards).
- Before and after changing `target`, `module`, `useDefineForClassFields`,
  `importHelpers`, or `verbatimModuleSyntax`.

**Do not use when.**

- The build uses another transpiler (Bun, esbuild, SWC, Babel): diff that
  tool's output instead; tsc output does not represent it.

**Example.**

```sh
tsc -p . --outDir /tmp/base
# apply the change
tsc -p . --outDir /tmp/cand
diff -ru /tmp/base /tmp/cand | head -80
grep -rc "__awaiter(" /tmp/base /tmp/cand
```

**Cost removed.** Benchmarks of changes that alter only types and have no
runtime effect.

**Verify.**

1. Behavior: the diff contains only the intended construct.
1. Benefit: helper counts, bytes, or retained imports move as the card
   predicts; the emit oracle prints them as `METRIC` lines.

## Runtime timing of emitted code

**Definition.** Time `run(N)` of the emitted module in the target runtime
after a warmup call, taking the median of several repetitions, with the
input built outside the timed region and the result consumed
(`assets/examples/time.ts`).

**Use when.**

- The emitted-code diff shows a runtime difference (helpers, `WeakMap`,
  generators) and the workload spends time there.

**Do not use when.**

- The only change is in types: there is nothing to time.
- The machine is loaded: rerun alone. Local runs here were made at load
  average 23-41, and differences below about 2x did not keep their
  direction between runs.

**Example.**

```sh
node time.ts out/es2016/async.js 1000000 7
bun time.ts out/es2016/async.js 1000000 7
```

**Cost removed.** Unverified speed claims. For stable numbers, use the
project's benchmark harness or `hyperfine` across processes.

**Verify.**

1. Behavior: `time.ts` prints the result (`sink`) so baseline and
   candidate can be compared for equality.
1. Benefit: `sh assets/examples/verify.sh measure` prints `TIME` lines and
   asserts direction only for the async and private-field lowering.

[wiki]: https://github.com/microsoft/TypeScript/wiki/Performance
[speedscope]: https://www.speedscope.app/
[single]: typescript-7.md#single-threaded-mode-for-comparable-counters
