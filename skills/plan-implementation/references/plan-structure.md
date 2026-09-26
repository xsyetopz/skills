# Plan structure

The parts of a plan that an agent or engineer can execute without
guessing. Each card says how to write the part and what its absence looks
like in a plan under review. `scripts/check_plan.py` checks the task
format and dependency graph. The worked plan is
[`delimiter-plan.md`](../assets/examples/count-delimiters/delimiter-plan.md);
its demo project sits next to it so `verify.sh` can run every Verify
command.

## Contents

- Goal and acceptance
- Out of scope and scope creep
- Task line format
- Verify command per task
- Done condition per task
- Dependencies in executable order
- Tests before the change they protect
- Vertical slices
- Spikes with a decision rule

## Goal and acceptance

**Definition.** One or two sentences that name the observable outcome,
what must stay the same, and where the requirement is specified
(requirement IDs, issue).

**Use when.** Every plan.

**Do not use when.** It would only restate the task title; the goal says
how success is recognized.

**Example.** "`count_delimiters` returns the same results and raises the
same errors as the current implementation, with less peak memory on
large inputs. Requirement source: issue 318."

**Cost removed.** Tasks that are complete but do not add up to the goal.

**Verify.**

1. Each task's done condition contributes to the goal; the final task's
   done condition demonstrates it.

## Out of scope and scope creep

**Definition.** One sentence naming adjacent changes the plan deliberately
leaves out. Scope creep is its absence: tasks that go beyond the requested
change (rewrites, upgrades, new frameworks) although the change does not
require them.

**Use when.** Writing: a neighboring improvement is tempting or was
discussed. Reviewing: a task does not trace to the goal.

**Do not use when.** It would list everything imaginable; name only the
likely temptations. In review, the extra work is a prerequisite and the
plan says why.

**Example.** "Out of scope: changing the delimiter definition, other
callers of `split`." Scope creep: "Also migrate the config format to
TOML" in a plan to fix lost updates.

**Cost removed.** Bigger, riskier changes than requested.

**Verify.**

1. No task touches the out-of-scope items (check each task's
   `[files: ...]`).
1. Each task traces to the goal or a stated prerequisite.

## Task line format

**Definition.** Each task is a list item: `T<n> [depends: ...] [files:
...] [estimate: ...] <imperative summary>`, followed by indented
`Verify:` and `Done when:` lines.

**Use when.** An agent will execute the plan or a reviewer will check it,
and the repository has no template of its own.

**Do not use when.** The team's tracker requires another format; carry
the same fields there.

**Example.**

```markdown
- T2 [depends: T1] [files: counter.py] [estimate: 1h] Replace the body
  with `str.count` behind an empty-delimiter guard, keeping the old
  function as the test oracle.
  Verify: `python3 -m unittest tests.test_counter`
  Done when: every case still passes, including the ValueError case.
```

**Cost removed.** Tasks without scope, order, or completion criteria.

**Verify.**

1. `python3 scripts/check_plan.py PLAN.md` reports no defects.

## Verify command per task

**Definition.** A backticked command that exits 0 only when the task's
change is correct. It runs from the repository root unless the plan names
another directory.

**Use when.** Every task, including documentation and configuration tasks
(link checkers, `--check` modes, dry runs).

**Do not use when.** The line would say "run the tests" without naming
them, or name a command that does not exist in the repository.

**Example.** ``Verify: `python3 -m unittest tests.test_counter` ``

**Cost removed.** "Done" without evidence.

**Verify.**

1. `python3 scripts/check_plan.py --commands PLAN.md` lists the commands;
   run each once before handing the plan over (`verify.sh` does this).

## Done condition per task

**Definition.** `Done when:` names what the task's command proves: the
new cases, the expected output. A done condition that no command or
observation can decide ("works", "is fast", "edits appear") is a flaw.

**Use when.** Every task, written or reviewed.

**Do not use when.** It would repeat "the command passes".

**Example.** "Done when: all cases pass against the split-based
implementation." Flawed: F5 in the worked review, "the CLI works".

**Cost removed.** Tasks marked done with weaker tests than intended, or
without evidence.

**Verify.**

1. For a task without one, the checker reports `no 'Done when:'`.
1. In review, replace each undecidable condition with a test name or a
   command and its expected output.

## Dependencies in executable order

**Definition.** `[depends: T1, T2]` names a task's prerequisites. Every
dependency is listed earlier (a topological order) and the graph has no
cycles. The flaw is a task that uses an artifact (table, flag, API,
fixture) that no earlier task creates, or that depends on a later task.

**Use when.** Any plan with more than one task.

**Do not use when.** The dependency is only a preference; it lengthens the
critical path. In review, the claims audit confirms that the artifact
already exists in the repository.

**Example.** T2 depends on T1 (tests first), T3 on T2. Flawed: "T2 Switch
reads to `username`" before any task adds the column.

**Cost removed.** Blocked work and impossible orders. The vague example
plan contains `T2 -> T3 -> T2`; the checker reports the cycle.

**Verify.**

1. The checker reports `depends on later task`, `depends on unknown`, and
   `cycle:` defects, and prints the critical path.
1. For each task input, name the task or repository file that provides
   it.

## Tests before the change they protect

**Definition.** A task that pins current behavior with tests precedes
the task that changes the implementation, and its tests pass on the old
code.

**Use when.** Changing code whose behavior must stay the same
(refactors, optimizations, migrations).

**Do not use when.** The behavior changes on purpose; then the new tests
describe the new behavior and fail first.

**Example.** T1 pins the empty-delimiter `ValueError`; `str.count` alone
would silently return `len(text) + 1`.

**Cost removed.** Silent contract changes.

**Verify.**

1. Run T1's command on the base revision; it passes.

## Vertical slices

**Definition.** Each task delivers one testable case end to end (API +
storage + UI) instead of one layer for all cases.

**Use when.** Features spanning several layers.

**Do not use when.** A shared prerequisite (a schema, a library upgrade)
must exist first; make it its own task.

**Example.** "T2 Cancel a running export end to end for the owner" before
"T3 Admin cancellation", instead of "T2 All API endpoints", "T3 All UI".

**Cost removed.** Integration problems found only at the end.

**Verify.**

1. Each slice task's Verify runs an end-to-end or integration test.

## Spikes with a decision rule

**Definition.** A time-boxed task that answers one question with an
experiment and states in advance which result leads to which decision.

**Use when.** Feasibility or performance is unknown and determines later
tasks.

**Do not use when.** The spike's code would ship to production without
review.

**Example.**

```markdown
- T1 [depends: -] [files: spike/bench_copy.py] [estimate: 4h] Measure
  S3 server-side copy latency for 1 GB objects.
  Verify: `python3 spike/bench_copy.py --size 1GB --runs 5`
  Done when: median recorded; under 10 s means T2 uses copy, otherwise
  T2 uses multipart upload.
```

**Cost removed.** Plans built on untested assumptions.

**Verify.**

1. Later tasks name the spike's outcome.
