# Retain, rewrite, consolidate, or remove tests

Load this reference when maintaining an existing suite, especially tests that
repeatedly break during behavior-preserving refactors. Retirement is a scoped
engineering decision, not a way to make an unexplained failure disappear.

## Establish what the test protects

For each affected test, record its consumer, starting conditions, required
consequence, independent authority, target action, and observation boundary.
Name a plausible meaningful fault it detects. Ask whether replacing a helper,
type, collection, algorithm, or control-flow arrangement preserves the contract
but breaks the test. Justify every interaction, order, type, or structural
assertion against the requirement rather than current code.

Use requirements, supported consumer behavior, incident evidence, and agreed
architecture constraints. A snapshot or existing test can suggest a contract,
but its existence alone does not settle a disputed requirement. Investigate
unknown authority and consult the responsible owner when it cannot be found.

Google's [Change-Detector Tests][detectors] describes mechanically reproducing
implementation information instead of independently checking correctness. A test
that fails after a change is not automatically a change detector: it may be the
only warning of a real regression. Repeated synchronized production/test edits
are a reason to investigate, not proof that deletion is safe.

## Choose the disposition

| Decision | Deciding evidence | Action |
| --- | --- | --- |
| Retain | Detects a meaningful contractual defect at a needed boundary | Keep it, even if it uses a mock or structural assertion |
| Rewrite | Requirement matters, but current assertions couple to replaceable details | Preserve protection through an independent consequence |
| Consolidate | Several cases cover the same requirement and failure mode | Keep the clearest sufficient cases without dropping distinct boundaries |
| Remove | Obsolete requirement, genuine redundancy, or negative value with no unique useful protection | Delete in the authorized slice; name retained coverage or why none is needed |
| Unresolved | Contract, consumers, or replacement evidence remain uncertain | Investigate; do not delete on speculation |

Negative value means the test's maintenance/diagnosis costs outweigh its useful
evidence under the established requirements, for example a declaration snapshot
that repeatedly rejects allowed refactors and misses the relevant defect.
Runtime cost alone does not justify removing a unique integration check. A flaky
test may expose a race; first distinguish test defects, environment failures,
and production nondeterminism. Quarantine or retry policy is a separate decision
requiring authorization, not a substitute for repair.

Do not replace every removed test mechanically. Rewrite if a meaningful
requirement would otherwise lose its only useful protection. Consolidating
parameterized equivalents can help, but visually similar tests may observe
different risks: mocked persistence and a real-store restart test are not
redundant. Preserve representative boundaries, errors, and forbidden effects.

## Stop repeatedly repairing an implementation mirror

**Deciding condition:** `delivery_fee(10)` must return 5 under an independently
agreed flat-fee rule. `_fees` is private storage; an existing public test
protects the fee. A refactor replaces the one-element list with a tuple.

### Defect: update the mirror to match each representation

```python
assert _fees == (5,)
assert delivery_fee(10) == 5
```

The first assertion changed from `[5]` to `(5,)` merely to follow production. It
will break again if storage becomes a scalar and adds no protection against the
public operation returning the wrong fee.

### Correction: remove the mirror and retain useful coverage

```python
assert delivery_fee(10) == 5
```

Disposition: **remove** the private-storage assertion, **retain** the public fee
test. No replacement is needed for a representation that is not promised. This
is a test retirement, not assertion weakening to excuse a changed fee.

Check: list-, tuple-, and scalar-backed implementations returning 5 all pass
corrected example. defective example rejects the list and scalar. Change the
public fee to 6 without changing storage: retained corrected example fails.
Review the requirement and other cases before concluding this test is redundant;
a single example does not prove the entire fee schedule.

## Execute the decision safely

1. Restrict review to the requested tests or authorized refactoring slice.
1. Inventory the meaningful requirements currently protected at each boundary.
1. Batch removal with any necessary rewritten tests and explanatory changes.
1. Run retained/replacement tests on correct code and a behavior-preserving
   alternative when practical. Use disposable copies, never reset user work.
1. Introduce a controlled meaningful fault or replay the relevant historical
   defect; confirm retained tests fail for the intended consequence, not setup.
1. Run the scoped suite and required repository checks. Separate unrelated
   baseline failures from failures caused by the retirement.

Use the repository's existing change description or review record for the
decision; do not introduce production state or a new tracking system. A useful
record names the test, contract authority, disposition, retained coverage, and
actual check result. For obsolete requirements, name the evidence that support
ended instead of inventing a replacement scenario.

## Review the result, not a metric

Before finishing, ask whether any meaningful requirement lost its only useful
protection. Test count and line coverage can fall after justified removal;
neither is an expected-result check. Conversely, unchanged coverage does not
prove preservation: assertions may have lost the only check of a required
effect.

Report executed defect checks separately from manual contract judgments. When
the fault cannot be replayed or a host is unavailable, identify the remaining
uncertainty. Never describe uncertain deletion as verified, nor claim better
agent behavior from documentation review without agent trials.

[detectors]:
https://testing.googleblog.com/2015/01/testing-on-toilet-change-detector-tests.html
