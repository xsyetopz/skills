# Review method

How to find, prove, and report plan flaws, in someone else's plan or in
your own draft before handing it over. The worked output is
[`review.md`](../assets/examples/config-edits/review.md).

## Contents

- Inputs to collect
- Walk the plan as an execution
- Claims audit
- Counterexample as a test
- Finding format
- Severity
- Minimal correction
- What not to report as a flaw

## Inputs to collect

**Definition.** The plan, its requirements and constraints, the relevant
code and tests, the deployment model (who runs which version when), and
the repository's commands.

**Use when.** Always, before reviewing.

**Do not use when.** Never skip it by reviewing the plan in isolation while
the repository is available.

**Example.** For `config-plan.md`: the goal's two constraints,
`config_store.py`, whether another tool writes `settings.json`.

**Cost removed.** Findings that are wrong for lack of context.

**Verify.**

1. The review names each input it used.

## Walk the plan as an execution

**Definition.** Execute each step in order and track state (files, data,
running versions, flags). At each step, ask what happens on failure,
under concurrency, on retry, and at rollout.

**Use when.** Every review.

**Do not use when.** Never substitute length, diagram count, or stage
labels for the walk; they say nothing about correctness.

**Example.** At T1: "state = A; another writer makes B; T1 writes A+edits;
B's change is lost."

**Cost removed.** Flaws hidden in the step order.

**Verify.**

1. Each finding cites the step where the state goes wrong.

## Claims audit

**Definition.** `scripts/audit_plan_claims.py PLAN.md REPO` extracts named
files, `Verify:` commands, fenced shell commands, and tool invocations,
and checks them against the repository (files, justfile recipes,
`package.json` scripts, Makefile targets, Python modules, programs on
`PATH`).

**Use when.** The repository is available.

**Do not use when.** You would read OK as proof the command is correct;
it only proves the thing exists.

**Example.**

```sh
python3 scripts/audit_plan_claims.py config-plan.md repo/
# MISSING  line 11 path: src/config_cli.py (not in repo)
# MISSING  line 12 command: just test-config (recipe 'test-config')
```

**Cost removed.** Plans referring to things that do not exist.

**Verify.**

1. `python3 scripts/test_audit_plan_claims.py` passes; MISSING items
   appear as findings.

## Counterexample as a test

**Definition.** For a behavioral flaw, a small test that drives the exact
interleaving or input. It shows the bad outcome with the plan's design
and the good outcome with the correction.

**Use when.** The flaw involves concurrency, failure ordering, or retries,
and the code (or a faithful model of the step) can run.

**Do not use when.** Sleeps would be needed to order events; use a
callback or barrier instead.

**Example.**

```python
def test_lost_update(self) -> None:
    naive_update(self.path, {"theme": "light"}, between=self.other_writer)
    self.assertNotIn("font", json.loads(self.path.read_text()))
```

**Cost removed.** Arguments about whether a flaw is real.

**Verify.**

1. `python3 -m unittest tests.test_config_store` in
   `assets/examples/config-edits/repo` passes: the naive tests show the
   flaws, the corrected tests show they are fixed.

## Finding format

**Definition.** Each finding states: ID and severity, the step, the
constraint violated (quoted), a concrete counterexample, the smallest
correction, and the check that proves the correction.

**Use when.** Every finding.

**Do not use when.** Never report "consider concurrency" without a
counterexample.

**Example.**

```markdown
## F1 blocker: T1 loses concurrent edits

- Step: T1 "Read `settings.json`, merge the edits, and write the file
  back."
- Constraint violated: "Another tool may edit the same file at the same
  time" (goal).
- Counterexample: ... `test_lost_update` reproduces it.
- Correction: detect a change between read and publication and re-read.
- Verify: `python3 -m unittest tests.test_config_store`.
```

**Cost removed.** Findings the author cannot act on.

**Verify.**

1. Every finding in the report has all six parts.

## Severity

**Definition.** Blocker: the plan cannot meet a stated requirement or
loses data. Major: the plan will likely fail in execution or rollout.
Minor: the plan is executable but weaker than it should be (vague done
conditions, missing optional checks).

**Use when.** Ordering findings.

**Do not use when.** Never raise a style preference to major.

**Example.** F1 and F2 blockers, F3 and F4 major, F5 minor.

**Cost removed.** Authors fixing minor issues first.

**Verify.**

1. Findings are ordered blocker, major, minor.

## Minimal correction

**Definition.** The smallest change to the plan that removes the
counterexample, stated as a task edit.

**Use when.** Every finding.

**Do not use when.** Do not replace the user's plan with a larger
architecture unless the counterexample requires it.

**Example.** F2: "serialize fully, write a temporary file, then
`os.replace`" instead of "introduce a configuration service".

**Cost removed.** Reviews that turn into redesigns.

**Verify.**

1. The corrected step makes the counterexample test pass.

## What not to report as a flaw

**Definition.** Differences of taste, unrequested improvements, and
missing ceremony (no Gantt chart, no RACI) are not flaws. List optional
suggestions separately.

**Use when.** Before finalizing the review.

**Do not use when.** The "taste" issue violates a repository convention
the plan must follow.

**Example.** "Could use a dataclass for the config" is a suggestion, not
a finding.

**Cost removed.** Noise that hides real defects.

**Verify.**

1. Every finding cites a violated constraint or a failing
   counterexample.
