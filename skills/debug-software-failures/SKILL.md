---
name: debug-software-failures
description: >-
  Finds root causes of crashes, hangs, wrong results, flaky tests, and
  regressions via repro oracles, reduction, git bisect, and hypotheses tested
  with debuggers. Use when something fails for an unknown reason. Not for
  known fixes or history browsing.
---

# Debug Software Failures

Find the demonstrated cause of one failure before changing code to make it
go away, and end with a regression test. One oracle, a command that
recognizes exactly this failure, judges every phase: reproduce and
minimize, bisect to the commit when it worked at an earlier revision, and
diagnose with discriminating experiments and instruments. Run only the
phases the failure needs.

## Workflow

1. Capture the failure signature: the exact command, input, revision,
   environment, and the first error with its stack ([signature][signature]).
1. Write the oracle, a command that recognizes exactly that signature
   ([oracle][oracle]). It must pass on the original case and fail on a
   hand-fixed copy; tighten it until both hold.
1. Choose the phases with the [table](#choose-the-phases). Skip the ones
   that do not apply and record why, but never the oracle, the root-cause
   demonstration, or the regression test.
1. Reproduce, when the phase applies. Work in a disposable copy or a
   [worktree][worktree]. For an intermittent failure, measure the rate over
   N runs, pin seeds and environment, and force a suspected interleaving
   ([nondeterminism][nondeterminism]). Shrink inputs with
   `scripts/ddmin.py`, and code, configuration, and dependencies by
   halving, with a reduction log ([reduction][reduction]). Re-run the
   oracle on the minimal case alone; if it now shows a different trigger,
   tighten the oracle and reduce again ([strictness][strictness]).
1. Bisect, when it worked at a known revision and the cause is not
   evident. Put the check at an absolute path outside the checkout
   ([outside][outside]), make it exit non-zero on the failure
   ([polarity][oracle]), and map it through `scripts/bisect_oracle.py`;
   the good endpoint must exit 0 and the bad one 1 ([endpoints][endpoints]).
   Run `git bisect run` in a worktree and save `git bisect log`; if only
   skipped commits remain, report the candidate set ([ambiguity][ambiguity]).
   Verify the culprit: parent passes, culprit fails, reverting it on the bad
   endpoint passes; for a merge, test both parents
   ([verification][verification]). Its diff is the first hypothesis.
1. Diagnose. Start a hypothesis log from `assets/hypothesis-log.md`; each
   hypothesis gets an experiment and a predicted outcome before it runs.
   Pick the instrument that observes the disputed state: stack or thread
   dump for hangs, debugger backtrace for crashes, differential comparison
   for "works elsewhere", midpoint checks for wrong results
   ([instruments][instruments]). Run one experiment at a time in the
   worktree and discard each refuted one. Repeat until one hypothesis
   survives an experiment that could have refuted it.
1. Name the root cause at the component that owns the violated invariant,
   and show that removing only it removes the failure
   ([root cause][root-cause]).
1. Fix there, with a test converted from the reproduction that fails
   before the fix and passes after ([regression test][regression-test]);
   for test design beyond that, use `$write-behavior-tests`. For a
   defect in an upstream dependency, deliver the packaged reproduction and
   its delivery record instead.
1. Leave the repository as found: `git bisect reset`, remove worktrees
   (without `--force` over unsaved changes), delete temporary branches,
   and check that the user's `git status` is unchanged. Then report.

## Choose the phases

| Situation | Phases to run |
| --- | --- |
| Crash or exception whose backtrace names the faulting state | Signature, root cause, regression test; no reduction, bisect, or full hypothesis log |
| Worked at a known revision, fails now, cause not evident | Oracle, bisect, then diagnose the culprit's diff |
| Large failing input, or the repro goes to a maintainer | Reproduce with reduction and packaging |
| Fails only sometimes | Failure rate and forced interleaving first; majority vote if bisecting |
| Hang, deadlock, or stuck service | Instrument (stack or thread dump) before any hypothesis |
| Works on one machine, input, or revision only | Differential diagnosis; bisect for revisions |
| Several plausible causes and no telling first error | Full hypothesis log with discriminating experiments |

## Route the situation to a card

| Situation | Card |
| --- | --- |
| Starting a reproduction or a search | [Failure oracle](references/reduction.md#failure-oracle) |
| Large failing input file | [ddmin](references/reduction.md#delta-debugging-with-ddmin), [strictness](references/reduction.md#oracle-strictness) |
| Many files, config keys, dependencies, or a C/C++ program | [Halving](references/reduction.md#manual-halving-of-code-config-and-dependencies), [log](references/reduction.md#reduction-log), [language reducers](references/reduction.md#language-specific-reducers) |
| Fails sometimes, or a suspected race | [Failure rate](references/nondeterminism-and-packaging.md#failure-rate-over-repeated-runs), [seeds and env](references/nondeterminism-and-packaging.md#fixed-seeds-and-environment), [forced interleaving](references/nondeterminism-and-packaging.md#forced-interleaving), [race detectors](references/nondeterminism-and-packaging.md#race-detectors) |
| Crash or corruption in C/C++ | [AddressSanitizer](references/nondeterminism-and-packaging.md#addresssanitizer) |
| Sharing the reproduction | [Artifact shape](references/nondeterminism-and-packaging.md#artifact-shape-per-ecosystem), [delivery record](references/nondeterminism-and-packaging.md#delivery-record) |
| Starting a bisect | [Endpoints](references/bisect.md#verified-endpoints), [bisect run](references/bisect.md#git-bisect-run) |
| Test can fail for unrelated reasons | [Exit-code mapping](references/bisect-oracles.md#exit-code-mapping-oracle) |
| Test script changes across history | [Oracle outside checkout](references/bisect-oracles.md#oracle-outside-the-checkout) |
| Some commits do not build | [Skipping](references/bisect.md#skipping-untestable-commits), [historical environment](references/bisect-oracles.md#historical-build-environment) |
| Bisect lists several possible commits | [Ambiguity](references/bisect.md#ambiguity-when-skipped-commits-remain) |
| When it was fixed; which merge; only known files | [Custom terms](references/bisect.md#custom-terms), [first parent](references/bisect.md#first-parent-search), [path-limited](references/bisect.md#path-limited-search) |
| A manual bisect mark was wrong | [Log and replay](references/bisect.md#bisect-log-and-replay) |
| Intermittent test during a bisect | [Majority vote](references/bisect-oracles.md#majority-vote-for-flaky-tests) |
| Slowdown or size growth | [Threshold oracle](references/bisect-oracles.md#threshold-oracle-for-performance-regressions) |
| No runnable test, text change suspected | [Pickaxe](references/bisect.md#pickaxe-search-instead-of-bisect) |
| Culprit found | [Verification](references/bisect-oracles.md#culprit-verification-parent-culprit-revert), [merge culprits](references/bisect-oracles.md#merge-culprits) |
| Long log, unclear error | [First error](references/method.md#failure-signature-and-first-error) |
| Several plausible causes | [Hypothesis log](references/method.md#hypothesis-log-with-predictions), [discriminating experiment](references/method.md#discriminating-experiment) |
| Works on one machine, revision, or input | [Differential diagnosis](references/method.md#differential-diagnosis) |
| Wrong output after a long pipeline | [Bisect the path](references/method.md#bisecting-the-execution-path) |
| Python, Go, or JVM process hangs | [faulthandler](references/instruments.md#python-stack-dumps-with-faulthandler), [goroutine dumps](references/instruments.md#go-deadlock-detection-and-goroutine-dumps), [jcmd Thread.print](references/instruments.md#jvm-thread-dump-with-jcmd) |
| Segfault or native crash | [lldb backtrace](references/instruments.md#native-crash-backtrace-with-lldb) |
| "Cannot open", permission, network errors | [System call tracing](references/instruments.md#system-call-tracing) |
| Build fails, or only on some machines | [Verbose and clean builds](references/instruments.md#verbose-and-clean-builds) |
| Fails after running for a while | [Resource limits](references/instruments.md#resource-limits-and-open-files) |
| User has local changes; experimental edits | [Worktree isolation](references/method.md#worktree-isolation) |
| Choosing where to fix | [Root cause](references/method.md#root-cause-at-the-owning-boundary), [regression test](references/nondeterminism-and-packaging.md#regression-test-from-the-reproduction) |

## Rules

- The oracle matches the one reported failure. Setup errors, missing
  tools, timeouts, other crashes, and unrelated test failures are not the
  failure: a reducer treats them as passing, and a bisect maps them to
  skip (125) or abort (128), never bad.
- Reduce, bisect, and experiment in a disposable copy or worktree. Never
  undo experiments with `git checkout .`, `git reset --hard`, or
  `git stash` in a tree that holds the user's work.
- Every experiment has a written prediction; a result that contradicts it
  changes the hypothesis, not the expected result.
- One passing run of an intermittent failure proves nothing; report N and
  the failure count. Do not turn a race into a different sequential
  failure; force the original interleaving or report the measured rate.
- No fixes by suppression: no catching and ignoring the exception, raising
  timeouts, adding retries, deleting caches, upgrading dependencies at
  random, or editing expected output, unless the cause shows that is the
  correct fix.
- Correlation in time or history is not a root cause. Show that removing
  the cause removes the failure; the revert check catches a culprit commit
  that only exposed an older defect.
- `git bisect start` and `git bisect reset` have no `-q` option;
  `start -q` ignores both revisions ([card][bisect-run]). Redirect output.
- No credentials or private data in a shared reproduction; use synthetic
  values that keep the condition.
- Report partial conclusions as partial ("reproduces only with these bytes
  on this revision") rather than inventing a cause.

## Bundled tools

- `scripts/ddmin.py INPUT --oracle 'cmd {}' [--fail-status N]
  [--fail-text TEXT] [--unit line|char] [--output FILE] [--json]`: 1-minimal
  reduction; prints `units N -> M, oracle runs K`.
- `scripts/bisect_oracle.py [--bad-exit N]... [--skip-exit N]...
  [--timeout S] -- CMD ARGS`: maps a test's statuses to bisect's contract
  (0 good, 1 bad, 125 skip, 128 abort) without a shell.
- `assets/hypothesis-log.md`: the hypothesis log template.
- `assets/examples/{reproduce,bisect,instruments}/verify.sh`: run the
  worked case behind each card: reductions with loose and strict oracles,
  ASan, a forced race; one disposable Git history per bisect technique;
  and each instrument locating a known deadlock or crash.

## References

- [Oracle and reduction](references/reduction.md): read when writing the
  oracle or shrinking an input, program, or configuration.
- [Nondeterminism, tools, and packaging][nondeterminism]: read for flaky,
  racy, or C/C++ memory failures, and to package or test a reproduction.
- [Bisect search techniques](references/bisect.md): read before starting
  `git bisect` and when its result needs interpreting.
- [Bisect oracles and culprit verification][bisect-oracles]: read when
  the bisect oracle faces flaky tests, performance, or old builds, and
  before reporting a culprit.
- [Diagnosis method](references/method.md): read when the first error
  does not name the cause, before editing code to experiment, and before
  naming the root cause.
- [Instruments][instruments]: read for hangs, native crashes, file,
  network, or build errors, and failures after running a while.

## Completion evidence

Every report states the failure signature, the oracle command and its
result on the original case, which phases ran and why the others were
skipped, the root cause at its owning boundary with the experiment that
demonstrated it, the fix with a regression test that failed before it,
and that the user's checkout is unchanged. Each phase that ran adds:

- Reproduce: the oracle result on the minimal case, the reduction numbers
  (for example `units 401 -> 2`), the failure rate over N runs for an
  intermittent failure, the environment, the artifact's files and run
  command, and a run from an empty directory.
- Bisect: the oracle status on both endpoints, the search command with
  its options, the `git bisect log`, the culprit hash and subject (or the
  candidate set if skips remained), and the parent, culprit, and revert
  results.
- Diagnose: the hypothesis log with predictions and outcomes, and the
  instrument output that located the fault. Open questions are listed as
  open.

[signature]: references/method.md#failure-signature-and-first-error
[oracle]: references/reduction.md#failure-oracle
[strictness]: references/reduction.md#oracle-strictness
[reduction]: references/reduction.md
[nondeterminism]: references/nondeterminism-and-packaging.md
[regression-test]:
references/nondeterminism-and-packaging.md#regression-test-from-the-reproduction
[endpoints]: references/bisect.md#verified-endpoints
[outside]: references/bisect-oracles.md#oracle-outside-the-checkout
[bisect-run]: references/bisect.md#git-bisect-run
[ambiguity]: references/bisect.md#ambiguity-when-skipped-commits-remain
[bisect-oracles]: references/bisect-oracles.md
[verification]:
references/bisect-oracles.md#culprit-verification-parent-culprit-revert
[worktree]: references/method.md#worktree-isolation
[root-cause]: references/method.md#root-cause-at-the-owning-boundary
[instruments]: references/instruments.md
