# Performance change: <one-line summary>

## Target

- Claim type: <compile time / declaration output / emitted size / runtime>
- Metric and goal: <for example, CI type-check wall time under 60 s>
- Workload: <project, file count, input, runtime workload>
- Environment: <OS, CPU, tsc version, Node/Bun versions, transpiler>
- Effective options: <tsc --showConfig excerpt: target, module, types,
  isolatedModules, verbatimModuleSyntax, skipLibCheck>

## Attribution

- Tool and command: <--extendedDiagnostics / --generateTrace / emitted
  diff / runtime profiler>
- Finding: <counter, hot file, helper, or frame and its share before>

## Change

- Construct: <card name from the skill>
- Preconditions checked: <each "Use when" item and how it was confirmed>
- Counter-indications ruled out: <each "Do not use when" item>

## Correctness

- Type oracle: <tsc command, type tests, Eq probe>
- Runtime oracle: <test command, cases including error paths>
- Result: <pass/fail output>

## Measurement

| Metric | Baseline | Candidate | Command |
| --- | --- | --- | --- |
| <Types / Check time / .d.ts bytes / median ms> | <value> | <value> | <exact command and flags> |

- Repetitions and machine load: <runs, quiet or shared>
- End-to-end result: <full build or application result before/after>

## Decision and limits

- Keep, revert, or inconclusive: <decision and why>
- Not verified: <other tsc versions, runtimes, bundlers>
