---
name: diagnose-software-failures
description: >-
  Diagnose software bugs, crashes, incorrect results, and intermittent failures
  through discriminating experiments and causal evidence; verify authorized
  fixes. Not for specialized editor, emulator, CI, or security procedures,
  standalone reduction, or finding the first bad commit.
---

# Diagnose Software Failures

Produce a supported diagnosis or a verified authorized fix. Preserve unrelated
work and evidence. A diagnosis request does not authorize production changes,
dependency upgrades, broad refactoring, or a revert. Use specialized editor,
emulator, CI, and security workflows for their owned mechanisms rather than
replacing them with generic debugging.

## Capture the failure

State expected behavior and its source, actual result, affected operation,
severity/scope, and first known occurrence. Record the exact command/input,
diagnostic, revision and local changes, artifact/configuration identity,
runtime/platform, and relevant persisted state or dependencies. Protect secrets
and private data in captured logs and fixtures.

Re-run the reported path safely in isolated state where possible. Distinguish
setup failure from the target symptom. Preserve evidence before clearing caches,
restarting services, or rebuilding; these can remove the trigger. During an
incident, follow authorized recovery procedures first and record mitigation
separately from causal diagnosis. Do not experiment destructively on production.

For intermittent failures, record attempts, failures, workload, seeds, timing,
and instrumentation. Check whether logging or a debugger changes the schedule.
A single successful rerun neither disproves a race nor verifies its repair.
If reproduction is unavailable, use captured evidence and label conclusions
accordingly; do not manufacture a confirmed failure.

## Choose discriminating experiments

Trace the operation through input parsing, state/decisions, dependencies, and
effects. Locate the first observed divergence from the contract, not merely
the last error message. Use existing tests, debugger, traces, and logs before
adding instrumentation. Keep temporary diagnostics scoped and removable.

Maintain plausible competing hypotheses only while they affect the next test.
For each, state supporting evidence, contradicting evidence, and a predicted
observation that separates it from alternatives. Choose the lowest-risk test
with the highest useful discrimination; change one causal factor at a time or
explicitly account for coupled variables. Record the result and update the
hypotheses before trying another repair.

Example: stale output may come from a cache key collision or an old build.
First identify the executing artifact. Then vary only the relevant key input
against the same build and fixture. Rebuilding and flushing every cache at once
may remove the symptom but cannot distinguish those causes.

Use controlled input reduction or boundary substitution when it isolates the
failing layer without replacing the semantics under investigation. A mock
database cannot establish a real engine's transaction behavior. For an
independently distributable reproducer, use the minimal-reproduction workflow.
For a first-bad-commit question, establish a reliable good/bad oracle and use
the isolated bisection workflow; a suspicious recent commit is not proof.

## Establish cause and repair

Explain the causal chain: triggering input/state, violated assumption, failing
mechanism, and observed consequence. Distinguish proximate cause, contributing
conditions, and untested possibilities. A correlated change or disappearing
symptom is insufficient; seek a controlled intervention or trace that rules
out the consequential alternatives. Stop broad exploration once supported.

When a fix is authorized, change the owning mechanism with the narrowest repair
that preserves its contract. Do not swallow errors, add retries, weaken tests,
or change expected behavior just to hide the symptom. Preserve user changes;
remove only temporary artifacts introduced by the investigation.

Demonstrate the regression check failing on the faulty behavior when available
and passing on the repair. Check relevant neighboring valid, invalid, and
state-transition cases through the actual affected boundary. For flakes,
compare repeated trials under the same conditions and report residual
uncertainty, not “fixed” from a lone pass. Verify recovery behavior if changed.

Report diagnosis, causal evidence, experiments/commands and outcomes, repair if
authorized, regression results, and remaining uncertainty. If blocked, name the
missing artifact or experiment and what its possible results would distinguish.
Do not keep experimenting after completion or claim a verified fix from a
plausible patch that could not be run.

Source: [Google SRE troubleshooting][sre] motivates hypothesis-driven diagnosis
and separating mitigation from explanation; its production operations require
their own authorization.

[sre]: https://sre.google/sre-book/effective-troubleshooting/
