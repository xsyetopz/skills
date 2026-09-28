# Batch 1 findings

Skills audited: optimize-c-code, optimize-cpp-code,
optimize-csharp-code, optimize-go-code, optimize-java-code,
optimize-javascript-code, optimize-kotlin-code.

## optimize-c-code

No findings.

## optimize-cpp-code

No findings.

## optimize-csharp-code

No findings.

## optimize-go-code

No findings.

## optimize-java-code

No findings.

## optimize-javascript-code

No findings.

## optimize-kotlin-code

No findings.

## Batch patterns

- All seven `SKILL.md` files fold reference-file conditions into the
  numbered Workflow steps (for example "CPU on macOS: `sample`...; on
  Linux, `perf`" linking straight to a reference anchor) instead of
  writing a separate "Read X when ..." sentence per FL-03's example
  phrasing. The trailing `## References` list is a topic index, not a
  second load condition. Judged compliant: the condition is the step
  itself, and every reference file is reachable from `SKILL.md`
  (checked, no orphans in any of the seven skills).
- `evals/evals.json` in every skill mixes plain-string assertions
  (qualitative, human-graded) with object assertions carrying an
  executable `check` script (id 1 and id 6 in each file). This is
  consistent across the whole catalog and gives at least one
  objectively checkable assertion per eval, so it reads as a
  deliberate convention rather than a defect.
- The two skills with real bundled scripts
  (`optimize-csharp-code/scripts/compare_benchmarks.py`,
  `optimize-java-code/scripts/jmh_compare.py`) both produced a clear,
  specific error and exit code 2 on a missing file and on
  unclassified/invalid CSV or JSON input; no SC-03/SC-04 gaps found.
- Every `assets/examples/verify.sh` across the seven skills fails
  loudly (non-zero exit, a stated reason) when given a bad compiler or
  toolchain override; none silently reported success on setup failure.
- `evals/eval_queries.json` is a fixed 10/10 split with near-miss
  negatives naming an adjacent skill (`expected_skill`) in every file
  checked, matching the catalog's EV-05 convention.
