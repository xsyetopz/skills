---
name: debug-software-failures
description: >-
  Finds the root cause of crashes, wrong output, flaky tests, and
  regressions by reproducing, bisecting, and shrinking inputs. Use when the
  cause of a failure is unknown.
---

# Debug Software Failures

Find the demonstrated cause of one failure before changing code to make it go away, and end with a
regression test. One oracle, a command that recognizes exactly this failure, judges reproduction,
reduction, and bisection.

## Rules

- Reproduce before diagnosing. Write the oracle first: a command that exits as expected only for the
  exact reported signature (first error, exception type and message, input, revision). Check it
  reports the failure on the original case and not on a hand-fixed copy; a looser oracle lets
  reducers and bisect chase a different failure.
- Setup errors, missing tools, timeouts, other crashes, and unrelated test failures are not the
  failure: a reducer treats them as passing, and a bisect maps them to skip (125) or abort (128),
  never bad.
- Read the first error in the log, not the wrapper's summary line at the end:
  `grep -m1 -B2 -A8 '^error' run.log` (PowerShell:
  `sls -CaseSensitive '^error' run.log -Context 2,8 | select -First 1`).
- Isolate one stage at a time: check state at the midpoint of the failing path and continue in the
  half where it first goes wrong, instead of reading the whole pipeline.
- Change one thing per run, with a written prediction before it runs. A result that contradicts the
  prediction changes the hypothesis, not the expected result.
- Experiment, reduce, and bisect in a disposable copy or `git worktree add --detach ../REPO-wt REV`.
  Never undo experiments with `git checkout .`, `git reset --hard`, or `git stash` in a tree holding
  the user's work, because each also discards their changes. Remove the worktree and run
  `git bisect reset` at the end.
- `git bisect run` exit codes: 0 good, 1-127 except 125 bad, 125 skip, above 127 abort. Test scripts
  return 127 for "command not found", which would be marked bad, so map statuses with
  `scripts/bisect_oracle.py`. `git bisect start` and `git bisect reset` take no `-q`; `start -q`
  ignores both revisions.
- Never report one culprit from a bisect that ended with `only 'skip'ped commits left`; report the
  candidate set. Verify a culprit: parent passes, culprit fails, reverting it on the bad endpoint
  passes.
- One passing run of an intermittent failure proves nothing. Report failures over N runs, and force
  the original interleaving instead of turning the race into a different failure.
- Fix the cause, not the test or the symptom: no swallowed exceptions, longer timeouts, retries,
  deleted caches, random dependency upgrades, or edited expected output, unless the cause shows that
  is the correct fix. Put the fix at the component that owns the violated invariant, and show that
  removing only the cause removes the failure. Time or history correlation is not a cause.
- The regression test is converted from the reproduction and must be seen failing without the fix.
  For test design use `$write-behavior-tests`.
- Report partial conclusions as partial ("reproduces only with these bytes on this revision")
  instead of inventing a cause. Keep credentials and private data out of shared reproductions.

## Scripts

- `python3 scripts/ddmin.py [--fail-status N] [--fail-text TEXT] [--unit line|char] [--output FILE]
  [--json] INPUT -- CMD ARGS {}`: 1-minimal reduction, with the oracle as argv and `{}` for the
  candidate path; prints `units N -> M, oracle runs K`. Exit 0 on success, 1 when the input does not
  fail the oracle, 2 on usage errors.
- `python3 scripts/bisect_oracle.py [--bad-exit N]... [--skip-exit N]... [--timeout S] -- CMD ARGS`:
  maps a test's statuses to bisect's contract (0 good, 1 bad, 125 skip, 128 abort) without a shell.

On Windows, use `py -3` for `python3`. Run `python3 scripts/test_ddmin.py`, `test_bisect_oracle.py`,
and `test_bisect_integration.py` after changing either script.

## References

- Read [reduction](references/reduction.md) when shrinking an input, config, or program, measuring
  or forcing an intermittent failure, running sanitizers, or packaging a reproduction for someone
  else.
- Read [bisect](references/bisect.md) before starting `git bisect`, when a search skips commits or
  hits flaky or performance tests, and before reporting a culprit.
- Read [instruments](references/instruments.md) when several causes are plausible, for hangs, native
  crashes, file, network, or build errors, failures after running a while, or a limit the tool
  should not have.
