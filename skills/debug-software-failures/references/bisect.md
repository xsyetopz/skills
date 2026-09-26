# Bisect search techniques

Each card is a scenario in
[`assets/examples/bisect/verify.sh`](../assets/examples/bisect/verify.sh),
which builds disposable repositories with a known culprit and asserts that
the technique finds it (12 checks, measured with git 2.55.0; the worktree
scenario backs [worktree isolation](method.md#worktree-isolation)).
Command semantics come from the [git-bisect manual][git-bisect].

## Contents

- Verified endpoints
- git bisect run
- Skipping untestable commits
- Ambiguity when skipped commits remain
- Custom terms
- First-parent search
- Path-limited search
- Bisect log and replay
- Pickaxe search instead of bisect

## Verified endpoints

**Definition.** Before searching, run the exact test command on the known
good commit (it must pass) and on the known bad commit (it must fail with
the target symptom). Bisect assumes exactly one transition from good to
bad between them.

**Use when.** Before every `git bisect start`.

**Do not use when.** No exception. A "good" endpoint that fails for
another reason, or a "bad" endpoint that fails with a different error,
makes every later answer meaningless.

**Example.**

```sh
git checkout -q "$GOOD"
python3 scripts/bisect_oracle.py --bad-exit 1 --skip-exit 3 -- \
  python3 /abs/path/check.py; echo "good endpoint: $?"   # expect 0
git checkout -q "$BAD"
python3 scripts/bisect_oracle.py --bad-exit 1 --skip-exit 3 -- \
  python3 /abs/path/check.py; echo "bad endpoint: $?"    # expect 1
```

**Cost removed.** Searches built on a wrong premise.

**Verify.**

1. The report records both printed statuses.

## git bisect run

**Definition.** `git bisect start BAD GOOD` then `git bisect run CMD ARGS`
checks out midpoints and runs the command: exit 0 marks good, 1-127
except 125 marks bad, 125 skips, any other status aborts the search. The
result is left in `refs/bisect/bad` ([bisect run][git-bisect]).

**Use when.** A command can classify the target symptom without human
judgment.

**Do not use when.** The command's non-zero exits mix the target defect
with unrelated failures (build errors, missing tools), which become false
"bad" marks. Wrap the command first (see [bisect oracles](bisect-oracles.md)).

**Example.**

```sh
git bisect start bad-endpoint good-endpoint
git bisect run python3 scripts/bisect_oracle.py --bad-exit 1 \
  --skip-exit 3 -- python3 /abs/path/check.py
git rev-parse refs/bisect/bad
git bisect log > bisect.log
git bisect reset
```

`git bisect start` and `git bisect reset` take no `-q` option. Measured:
`git bisect start -q HEAD HEAD~1` ignored both revisions and waited for
marks, and `git bisect reset -q` failed with `'-q' is not a valid commit`.
Redirect output instead.

**Cost removed.** Manual checkout-and-test cycles. Binary search needs
about log2(N) tests; measured: 5 tests over 39 candidates.

**Verify.**

1. `verify.sh` asserts the culprit's subject is `commit 23: introduce
   regression`.
1. Save `git bisect log` output with the result.

## Skipping untestable commits

**Definition.** Exit 125 from the run command, or `git bisect skip [REV |
RANGE]`, marks a commit untestable; bisect tests a nearby commit instead
([bisect skip][git-bisect]).

**Use when.** Some commits cannot run the target test for a reason
unrelated to the defect (they do not build, a dependency is broken).

**Do not use when.** "Cannot build" is the regression you are looking for;
then a build failure is "bad".

**Example.** The oracle's `--skip-exit 3` maps the check script's "build
broken" status to 125. In `verify.sh`, commits 10-12 do not build, and the
search still finds commit 23.

The mapping, from `classify()` in `scripts/bisect_oracle.py`:

```python
def classify(code: int, bad: set[int], skip: set[int]) -> int:
    if code == 0:
        return 0
    if code in bad:
        return 1
    if code in skip:
        return 125
    return 128
```

The search, from `assets/examples/bisect/verify.sh` (it printed
`PASS bisect run found commit 23 in 5 steps over 39 candidates`):

```sh
git bisect start bad-endpoint good-endpoint >/dev/null
git bisect run "$PY" "$ORACLE" --bad-exit 1 --skip-exit 3 -- \
    "$PY" "$WORK/check.py" >"$WORK/run.log" 2>&1
culprit=$(git rev-parse refs/bisect/bad)
[ "$(subject_of . "$culprit")" = 'commit 23: introduce regression' ] ||
    fail bisect-run "found $(subject_of . "$culprit")"
steps=$(grep -c '^Bisecting' "$WORK/run.log" || true)
git bisect log >"$WORK/linear.bisect.log"
git bisect reset >/dev/null
pass "bisect run found commit 23 in $steps steps over 39 candidates"
```

**Cost removed.** Aborted searches and false "bad" marks on unbuildable
commits.

**Verify.**

1. `git bisect log` shows `git bisect skip` entries for the unbuildable
   commits and the correct culprit.

## Ambiguity when skipped commits remain

**Definition.** When skipped commits are adjacent to the transition,
bisect cannot name one commit. It prints `There are only 'skip'ped commits
left to test` with the possible first bad commits, and `bisect run` exits
non-zero.

**Use when.** Interpreting any search that used skips.

**Do not use when.** No exception: never report a single culprit from such
a run. Report the candidate set, then test the candidates with a build fix
applied or build them another way.

**Example.** In `verify.sh`, one commit introduces the defect and breaks
the build, and the next fixes the build. The run ends with the "only
'skip'ped commits left" message (measured exit status 2). From
`assets/examples/bisect/verify.sh`, which printed
`PASS skipped neighbors reported as ambiguous (bisect exit 2)`:

```sh
git init -q "$WORK/ambiguous"
cd "$WORK/ambiguous"
printf 'def add(a, b):\n    return a + b\n' >calc.py
commit 'base: good'
git tag base
printf 'def add(a, b):\n    return a - b\n' >calc.py
: >BROKEN_BUILD
commit 'defect introduced while build broken'
rm BROKEN_BUILD
commit 'build fixed'
git bisect start HEAD base >/dev/null
status=0
git bisect run "$PY" "$ORACLE" --bad-exit 1 --skip-exit 3 -- \
    "$PY" "$WORK/check.py" >"$WORK/amb.log" 2>&1 || status=$?
grep -q "only 'skip'ped commits left" "$WORK/amb.log" ||
    fail skip-ambiguity 'bisect did not report skipped candidates'
git bisect reset >/dev/null
pass "skipped neighbors reported as ambiguous (bisect exit $status)"
```

**Cost removed.** A confidently wrong culprit.

**Verify.**

1. `grep "only 'skip'ped commits left"` on the run output decides whether
   the result is a single commit or a set.

## Custom terms

**Definition.** `git bisect start --term-old OLD --term-new NEW` renames
the two states, so the search can find the commit that *fixed* something
or changed any property. With `bisect run`, exit 0 still means "old"
([alternate terms][git-bisect]).

**Use when.** Finding when a bug was fixed, when a behavior changed, or
when performance changed (`--term-old fast --term-new slow`).

**Do not use when.** Plain good/bad fits the question; renamed terms make
the exit semantics easy to invert by mistake.

**Example.**

```sh
git bisect start --term-old broken --term-new fixed HEAD "$BROKEN"
# exit 0 = still broken (old), non-zero = fixed (new)
git bisect run sh -c 'if python3 /abs/check.py; then exit 1; fi; exit 0'
git rev-parse refs/bisect/fixed
```

**Cost removed.** Hand-inverted logic ("mark fixed commits as bad").

**Verify.**

1. `verify.sh` finds the commit titled `fix add`.

## First-parent search

**Definition.** `git bisect start --first-parent` follows only the first
parent of merges, so it attributes a defect introduced inside a merged
branch to the merge commit (Git 2.29+).

**Use when.** The question is "which merge to main introduced this" (for
example, to revert a whole pull request), or branch commits do not build
individually.

**Do not use when.** You need the exact commit inside the branch. Run a
full search within the merged branch afterwards.

**Example.**

```sh
git bisect start --first-parent HEAD "$BASE"
git bisect run /abs/path/oracle.sh
git log -1 --format=%s refs/bisect/bad   # merge feature
```

**Cost removed.** Testing unbuildable intermediate branch commits.

**Verify.**

1. `verify.sh`: with `--first-parent` the result is `merge feature`;
   without it, `feature: step 2 breaks add`.

## Path-limited search

**Definition.** `git bisect start BAD GOOD -- PATH...` tests only commits
that touch the given paths.

**Use when.** The defect is known to live in specific files or
directories, and commits elsewhere cannot affect it.

**Do not use when.** The defect could come from a dependency, build
configuration, or code outside the paths; the search would skip the real
culprit.

**Example.**

```sh
git bisect start bad-endpoint good-endpoint -- calc.py
git bisect run /abs/path/oracle.sh
```

**Cost removed.** Tests on irrelevant commits. Measured: only commit 23
touched `calc.py`, so the result needed no test steps.

**Verify.**

1. `verify.sh` asserts the same culprit as the full search.

## Bisect log and replay

**Definition.** `git bisect log` prints the session as commands;
`git bisect replay FILE` restarts a session from such a file. Delete a
wrong manual mark from the file and replay to resume the search.

**Use when.** A manual `good`/`bad` mark was wrong, or a search must
resume on another machine.

**Do not use when.** Most marks are doubtful; restart with a better
oracle instead.

**Example.** The log records each mark as a `git bisect bad <hash>` line
after a `# bad: [hash] subject` comment:

```sh
git bisect log > mistake.log
git bisect reset
awk '/^git bisect start/{s=1} s && /^(git bisect bad |# bad:)/{next}
     {print}' mistake.log > fixed.log   # drop the wrong mark
git bisect replay fixed.log
git bisect run /abs/path/oracle.sh
```

**Cost removed.** Restarting a long manual search after one wrong answer.

**Verify.**

1. `verify.sh` makes a deliberate wrong mark, removes it, replays, and
   finds commit 23.

## Pickaxe search instead of bisect

**Definition.** `git log -S STRING` lists commits that change the number
of occurrences of `STRING`; `git log -G REGEX` lists commits whose diff
lines match `REGEX` ([git-log][git-log]).

**Use when.** The regression is tied to a specific text change (a
constant, a call, a config key) and no test can run.

**Do not use when.** The behavior change has no single textual signature.
Also, the commit that added the text need not be the one that made it
harmful.

**Example.**

```sh
git log -S 'a - b' --format='%h %s' -- calc.py
```

**Cost removed.** Building and testing historical revisions.

**Verify.**

1. `verify.sh` asserts the pickaxe returns the same commit as bisect.
   Confirm any pickaxe result by testing the commit and its parent.

[git-bisect]: https://git-scm.com/docs/git-bisect
[git-log]: https://git-scm.com/docs/git-log
