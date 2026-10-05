# Measurement

Commands are POSIX sh; on Windows run them in Git Bash or WSL.

Sources: [Performance wiki][1], [@typescript/analyze-trace][2], [Announcing TypeScript 7.0][3].

## Contents

- [Compiler Counters](#compiler-counters)
- [Check-Phase Trace](#check-phase-trace)
- [Compiler Profiles on tsc 7](#compiler-profiles-on-tsc-7)
- [Program Size](#program-size)

## Compiler Counters

```sh
tsc -p tsconfig.json --noEmit --singleThreaded --extendedDiagnostics
```

- Read `Check time` against `Parse time`, `Bind time`, and `Emit time` first; only a dominant
  `Check time` points at types.
- `Types`, `Instantiations`, `Symbols`, and `Memory used` are repeatable across runs with
  `--singleThreaded`; times are not. Compare counters for type changes and medians of at least 5
  runs for time.
- tsc 7 splits files over checker workers (default 4), so `Types` and `Memory used` change with
  `--checkers`. Compare only runs with the same flag and the same tsc version.
- A leftover `.tsbuildinfo` makes a run warm. Delete it before cold measurements.
- The wiki's `Program time` and `I/O Read time` lines may be absent on tsc 7.

## Check-Phase Trace

```sh
tsc -p . --noEmit --singleThreaded --generateTrace trace-out
bunx --bun @typescript/analyze-trace trace-out
```

- `trace.json` also opens in Chrome's `about://tracing`. The format is documented as unstable, so
  pin the analyze-trace version when scripting.
- analyze-trace exits 1 when nothing crosses its thresholds (defaults
  `--forceMillis 500 --skipMillis 100`). Lower them for small projects.
- A trace contains file paths and source. Do not upload or attach it outside the machine without the
  user's approval.
- The `types_N.json` files map the type ids named in the trace to declarations.

## Compiler Profiles on tsc 7

- Use `tsc -p . --noEmit --pprofDir pprof-out`, then
  `go tool pprof -top pprof-out/*-cpuprofile.pb.gz` (needs Go; PowerShell:
  `go tool pprof -top (Get-Item pprof-out/*-cpuprofile.pb.gz)`). `--generateCpuProfile` is still
  listed by `tsc --help --all` but wrote no file on tsc 7.0.2.
- The profile names compiler internals, not your files. Use it for non-check phases, or for an
  upstream report the user approves, and use the trace to blame your own types.

## Program Size

- `tsc --listFilesOnly | wc -l` (PowerShell: `| Measure-Object -Line`) and `tsc --explainFiles` show
  what a slow program loads. Fixtures, generated code, `dist/`, and automatically included `@types`
  packages are the usual surplus.
- `include` defaults to `**/*`. Narrow it (`"include": ["src"]`) and give tests their own project
  rather than dropping them from checking.
- `types` defaults to `[]` on tsc 7 and to every visible `@types` package on 5.x. A fix that lists
  `"types": ["node"]` must still cover every global the code uses, or builds fail with "Cannot find
  name".

[1]: https://github.com/microsoft/TypeScript/wiki/Performance
[2]: https://www.npmjs.com/package/@typescript/analyze-trace
[3]: https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/
