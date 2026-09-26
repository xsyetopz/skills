# Diagnosis method

Find a failure's cause with hypotheses and experiments that tell them
apart. The hypothesis log template is
[`hypothesis-log.md`](../assets/hypothesis-log.md).

## Contents

- Failure signature and first error
- Hypothesis log with predictions
- Discriminating experiment
- Differential diagnosis
- Bisecting the execution path
- Worktree isolation
- Root cause at the owning boundary

## Failure signature and first error

**Definition.** The exact observation that identifies this failure: the
first error (not a wrapper's summary), its stack, the input, revision,
environment, and the expected behavior.

**Use when.** Starting any investigation.

**Do not use when.** Working from "the build failed" or the last line of a
log; scroll to the first error.

**Example.**

```sh
cargo build 2>&1 | grep -m1 -B2 -A8 '^error'
python3 -X faulthandler app.py 2>&1 | tee run.log
```

**Cost removed.** Chasing errors that are consequences of the first one.

**Verify.**

1. One command reproduces the signature
   ([failure oracle](reduction.md#failure-oracle)).

## Hypothesis log with predictions

**Definition.** For each candidate cause, write the hypothesis, the
experiment, and the predicted outcome before running it; record the actual
outcome and the conclusion.

**Use when.** The cause is not obvious after reading the first error.

**Do not use when.** You would change code "to see what happens" without a
prediction; an unpredicted result tells you nothing.

**Example.**

```text
H1 lock-order deadlock between transfer_a_to_b and transfer_b_to_a
   Experiment: faulthandler dump after 2 s
   Predicted: both threads blocked at their second `with lock_x`
   Actual: line 20 in transfer_a_to_b, line 27 in transfer_b_to_a
   Conclusion: supported
```

**Cost removed.** Piled-up speculative edits that obscure causality and
rollback.

**Verify.**

1. Every code change during the investigation maps to a log entry.

## Discriminating experiment

**Definition.** An observation whose possible outcomes point to different
hypotheses.

| Competing explanations | Discriminating observation | Misleading substitute |
| --- | --- | --- |
| Bad input vs parser regression | same bytes on good and bad revisions | retyping "equivalent" input |
| Allocation vs retention | allocation trace plus live-object retainers | one RSS reading |
| Deadlock vs slow I/O | thread stacks and wait graph with I/O state | raising the timeout |
| Race vs ordering bug | controlled schedule with barriers | sleeps and retries |
| Cache vs source error | named cold and warm runs | deleting every cache |
| Missing dependency vs code | the loader or import error of the real binary | bypassing initialization |

**Use when.** Two or more hypotheses remain.

**Do not use when.** The experiment's result would not change your next
step.

**Example.** A thread dump separates "deadlock" (threads wait on locks
each other holds) from "slow I/O" (threads sit in socket reads).
`assets/examples/instruments/verify.sh` dumps the stacks of
`py_deadlock.py` and
states the deadlock outcome in advance: both threads stop inside their
`transfer_*` function.

```sh
status=0
"$PY" "$ROOT/py_deadlock.py" 2 >"$WORK/py.log" 2>&1 || status=$?
grep -o 'line [0-9]* in transfer_[a-z_]*' "$WORK/py.log"
for name in transfer_a_to_b transfer_b_to_a; do
    grep -q "in $name" "$WORK/py.log" ||
        { echo "FAIL faulthandler did not show $name" >&2; exit 1; }
done
```

Measured output:

```text
line 27 in transfer_b_to_a
line 20 in transfer_a_to_b
```

Line 20 is `with lock_b:` and line 27 is `with lock_a:`, each thread's
second lock: the threads wait on locks, not I/O.

**Cost removed.** Experiments that only confirm what you already believed.

**Verify.**

1. Before running, write which outcome supports which hypothesis.

## Differential diagnosis

**Definition.** Compare a working and a failing setup factor by factor
(revision, input, environment variables, dependency versions, config,
machine) and change one factor at a time toward the failing side.

**Use when.** "It works on my machine" or "it worked yesterday".

**Do not use when.** Many factors change together and cannot be isolated;
bisect instead: [git bisect run](bisect.md#git-bisect-run) for revisions,
[halving](reduction.md#manual-halving-of-code-config-and-dependencies)
for configuration and dependencies.

**Example.**

```sh
diff <(env | sort) failing-env.txt
diff <(python3 -m pip freeze) failing-freeze.txt
git diff good-sha bad-sha --stat
```

**Cost removed.** Guessing which of many differences matters.

**Verify.**

1. Changing only the identified factor flips the outcome in both
   directions.

## Bisecting the execution path

**Definition.** Check state at the midpoint of the failing path (log a
value, assert an invariant, or break in a debugger), then continue in the
half where state first goes wrong.

**Use when.** The failure appears far from its cause (wrong output after a
long pipeline).

**Do not use when.** The first error already names the faulty state.

**Example.** The output total is wrong. Assert the intermediate list
after parsing (correct) and after filtering (wrong): the defect is in the
filter stage.

```python
def parse(text):
    return [int(field) for field in text.split(",")]


def keep_positive(values):
    return [v for v in values if v > 1]  # defect: should be v > 0


def total(text):
    parsed = parse(text)
    assert parsed == [3, 1, -2, 4], parsed  # midpoint: correct
    kept = keep_positive(parsed)
    assert kept == [3, 1, 4], kept  # first wrong value
    return sum(kept)


print(total("3,1,-2,4"))
```

Measured: the first assertion passes and the second fails with
`AssertionError: [3, 4]` at the `kept` line, so the defect is in
`keep_positive`.

**Cost removed.** Reading the whole pipeline.

**Verify.**

1. The first wrong intermediate value is recorded with its location.

## Worktree isolation

**Definition.** A separate checkout of the same repository,
`git worktree add --detach PATH REV`, for bisecting, reducing, and
experimental edits. The user's branch, index, and untracked files stay
untouched, and undoing a refuted experiment means discarding the
worktree, not resetting the user's tree ([git-worktree][git-worktree]).

**Use when.** Any investigation that checks out old revisions or edits
code or config, and always when the user's checkout has local changes or
the search runs alongside other work.

**Do not use when.** The build depends on absolute paths into the main
checkout, or on untracked files only it has; copy those explicitly. The
isolation itself has no exception: never undo experiments with
`git checkout .`, `git reset --hard`, or `git stash` in a tree with the
user's work, because each also takes the user's changes.

**Example.** A bisect in a worktree:

```sh
git worktree add --detach /tmp/bisect-wt "$BAD"
git -C /tmp/bisect-wt bisect start "$BAD" "$GOOD"
(cd /tmp/bisect-wt && git bisect run /abs/path/oracle.sh)
git -C /tmp/bisect-wt rev-parse refs/bisect/bad
git -C /tmp/bisect-wt bisect reset
git worktree remove /tmp/bisect-wt
```

Experiments follow the same shape: `git worktree add ../investigate HEAD`,
edit and run there, record each edit in the hypothesis log, then
`git worktree remove ../investigate` (it refuses to drop uncommitted
changes unless given `--force`).

**Cost removed.** Lost or stashed user work, and confusion about which
edit mattered.

**Verify.**

1. `assets/examples/bisect/verify.sh` records HEAD and an untracked file
   before a worktree search and asserts both are unchanged after it.
1. `git status` in the user's checkout is unchanged at the end.

## Root cause at the owning boundary

**Definition.** The root cause is the demonstrated violation at the
component that owns the invariant, not the last frame in the stack or the
first place a guard could hide it.

**Use when.** Writing the conclusion and choosing the fix.

**Do not use when.** Claiming a cause from temporal correlation, or
"fixing" by catching the exception, raising a timeout, deleting a cache,
upgrading dependencies at random, or editing the expected output.

**Example.** The report writer raises `KeyError`. The root cause is the
importer, which drops the `price` field for one supplier format, so the
fix and its test belong in the importer.

```python
def import_row(row, supplier_format):
    if supplier_format == "legacy":
        return {"sku": row["sku"]}  # defect: drops "price"
    return {"sku": row["sku"], "price": row["price"]}


def write_report(items):
    return sum(item["price"] for item in items)


row = {"sku": "A1", "price": 5}
try:
    write_report([import_row(row, "legacy")])
except KeyError as error:
    print("report writer: KeyError", error)
# Test at the owning boundary, which fails before the importer fix:
assert "price" in import_row(row, "legacy"), "importer dropped price"
```

Measured: it prints `report writer: KeyError 'price'`, then fails with
`AssertionError: importer dropped price`. Catching the `KeyError` in the
writer would hide the symptom and leave the importer wrong.

**Cost removed.** Symptoms suppressed while the defect remains.

**Verify.**

1. Removing only the cause removes the failure, and a test at the owning
   boundary fails before the fix.

[git-worktree]: https://git-scm.com/docs/git-worktree
