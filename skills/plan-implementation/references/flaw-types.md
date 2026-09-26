# Flaw types

Each card is a class of plan flaw, with an example and a way to prove it.
The worked review is
[`review.md`](../assets/examples/config-edits/review.md) on
[`config-plan.md`](../assets/examples/config-edits/config-plan.md); F1 and
F2 are reproduced by tests in `assets/examples/config-edits/repo/tests/`.

Five flaw classes live on the card for the construct that prevents them:

- Missing prerequisite or wrong order:
  [dependencies](plan-structure.md#dependencies-in-executable-order).
- Unverifiable done condition:
  [done condition](plan-structure.md#done-condition-per-task).
- Scope creep: [out of scope](plan-structure.md#out-of-scope-and-scope-creep).
- Irreversible step without recovery:
  [rollback](delivery.md#rollback-per-irreversible-step).
- Lockstep change to a shared interface:
  [expand and contract](delivery.md#expand-and-contract-migration).

## Contents

- Lost update between read and write
- Destructive failure ordering
- Non-idempotent retry
- Contradiction with a stated constraint
- Claims that do not match the repository
- Unsupported decision or invented number
- Missing failure and boundary cases

## Lost update between read and write

**Definition.** A step reads shared state, computes a change, and writes it
back without checking that the state is unchanged, so it overwrites a
concurrent writer's change.

**Use when.** The plan reads, then writes, a file, row, document, or cache
entry that anything else can modify.

**Do not use when.** The system guarantees a single writer (documented, or
enforced by a lock); cite the guarantee.

**Example.** F1: T1 reads `settings.json`, another tool adds `font`, T1
writes its merged copy, `font` is lost.

**Cost removed.** Data loss that appears only under concurrency.

**Verify.**

1. A test runs the other writer between the read and the write through a
   callback or barrier, as `test_lost_update` does.
1. The corrected design (compare-and-swap, version check, lock,
   transaction) makes the same test raise or retry instead of losing data
   (`test_stale_write_detected`).

## Destructive failure ordering

**Definition.** A step destroys or truncates the old state before the new
state is complete and validated, so a failure midway leaves neither.

**Use when.** The plan writes in place, deletes before copying, or drops
before migrating.

**Do not use when.** The old state is disposable (a cache) and the plan
says so.

**Example.** F2: `open(path, "w")` truncates before `json.dumps` raises on
an unserializable value; the file ends empty.

**Cost removed.** Corrupted data on the error path.

**Verify.**

1. Inject the failure (bad input, an exception in serialization) and
   assert the old state is intact (`test_unserializable_edit_leaves_file`).

## Non-idempotent retry

**Definition.** A retry repeats an operation that is unsafe to repeat, or
retries errors that cannot succeed.

**Use when.** The plan says "retry on failure" or relies on a client or
queue that retries.

**Do not use when.** The operation is idempotent by design and the plan
states which errors are retryable.

**Example.** F3: "Retry on any failure" re-runs the lost-update write and
retries a `TypeError` forever.

**Cost removed.** Duplicate side effects and infinite retry loops.

**Verify.**

1. List each error the step can raise and whether the retry re-reads
   state. The corrected plan names the retryable errors and the retry
   bound.

## Contradiction with a stated constraint

**Definition.** A step's behavior violates a requirement, constraint, or
earlier decision stated in the plan or its sources.

**Use when.** The plan or its requirements list constraints (compatibility,
concurrency, data retention, performance).

**Do not use when.** The constraint is your preference, not the user's.

**Example.** F1 and F2 each violate a sentence of the plan's own goal.

**Cost removed.** Plans that cannot meet their own goal.

**Verify.**

1. Quote the constraint and the step side by side in the finding.

## Claims that do not match the repository

**Definition.** The plan names files, commands, recipes, scripts, or
modules that do not exist and are not marked as new.

**Use when.** Every review.

**Do not use when.** The plan explicitly creates them ("Create
`src/x.py`"); the audit treats "new/create/add" before a path as new.

**Example.** F4: `src/config_cli.py` and `just test-config`.

**Cost removed.** Tasks that cannot start and verifications that cannot
run.

**Verify.**

1. `python3 scripts/audit_plan_claims.py PLAN.md REPO` lists each claim as
   OK, MISSING, or UNKNOWN; `verify.sh` asserts both MISSING items.

## Unsupported decision or invented number

**Definition.** A choice or number (timeout, batch size, percentage,
estimate) with no source, measurement, or stated reasoning.

**Use when.** The plan contains numbers or tool choices. For how to write
an estimate with its basis, see
[estimates](delivery.md#estimates-from-analogies-with-ranges).

**Do not use when.** The value comes from the requirements or a cited
measurement.

**Example.** "Batch size 10,000" for a backfill with no measurement of
lock time.

**Cost removed.** Values that fail in production because nobody chose
them.

**Verify.**

1. For each number, find its source or turn it into a spike task.

## Missing failure and boundary cases

**Definition.** The plan covers the happy path but not empty input, maximum
sizes, timeouts, partial failures, or cancellation.

**Use when.** Every plan that processes input or talks to other systems.

**Do not use when.** The requirements explicitly exclude the case.

**Example.** A migration plan with no step for rows that fail
validation.

**Cost removed.** Crashes on the first unusual input.

**Verify.**

1. List the boundary and failure cases per step; each has a task or an
   explicit exclusion.
