# Bisect

Commands are POSIX sh; on Windows run them in Git Bash or WSL.

Command semantics come from the [git-bisect manual][git-bisect].

## Contents

- [Endpoints and run](#endpoints-and-run)
- [Oracle wrapper](#oracle-wrapper)
- [Skipped commits](#skipped-commits)
- [Variants](#variants)
- [Flaky and performance oracles](#flaky-and-performance-oracles)
- [Verify the culprit](#verify-the-culprit)

## Endpoints and run

Run the exact check on the good commit (must exit 0) and on the bad commit (must fail with the
target symptom) before searching. Bisect assumes one good-to-bad transition between them.

```sh
git worktree add --detach /tmp/bisect-wt "$BAD"
cd /tmp/bisect-wt
W="python3 /abs/skills/debug-software-failures/scripts/bisect_oracle.py \
  --bad-exit 1 --skip-exit 3 --timeout 300 --"
git checkout -q "$GOOD" && $W python3 /abs/check.py; echo "good: $?"  # 0
git checkout -q "$BAD"  && $W python3 /abs/check.py; echo "bad: $?"   # 1
git bisect start "$BAD" "$GOOD" >/dev/null
git bisect run $W python3 /abs/check.py
git rev-parse refs/bisect/bad
git bisect log > /tmp/bisect.log
git bisect reset >/dev/null
```

- `git bisect run` exit codes: 0 good; 1-127 except 125 bad; 125 skip; above 127 aborts. A shell
  returns 126 and 127 for "not executable" and "command not found", which would be marked bad.
- `git bisect start` and `git bisect reset` take no `-q`: `start -q HEAD HEAD~1` ignores both
  revisions and waits for marks, and `reset -q` fails with `'-q' is not a valid commit`. Redirect
  output instead.
- Keep the check at an absolute path outside the repository, so every revision runs the same test.
  If the test must be the project's own file at each revision, say in the report that the question
  changes with it.

## Oracle wrapper

`scripts/bisect_oracle.py [--bad-exit N]... [--skip-exit N]... [--timeout S] -- CMD ARGS` runs the
test without a shell and maps its status: 0 to 0, `--bad-exit` statuses to 1, `--skip-exit` statuses
to 125, and everything else (missing command, signal, timeout, unexpected status) to 128, which
aborts. Skip the wrapper only when the command already returns just 0 or 1 for the target symptom.

## Skipped commits

Exit 125 or `git bisect skip [REV | RANGE]` marks a commit untestable; map "does not build" to skip
unless the build break is the regression. If the skipped commits sit next to the transition, bisect
prints `There are only 'skip'ped commits left to test` and lists possible first bad commits. Report
that candidate set, never one commit; test the candidates with a build fix applied.

For old revisions, restore what they need inside the check
(`git submodule update --init --recursive`, the pinned toolchain such as `rust-toolchain.toml`), and
report how many commits were skipped.

## Variants

| Question | Command |
| --- | --- |
| Which commit fixed it, or changed a property | `git bisect start --term-old broken --term-new fixed HEAD "$BROKEN"`; exit 0 means the old term (still broken), non-zero the new one (fixed), so invert a check that exits 0 on the fix |
| Which merge to main introduced it (Git 2.29+) | `git bisect start --first-parent HEAD "$BASE"`, then search inside that merge's branch for the exact commit |
| Defect lives only in known paths | `git bisect start BAD GOOD -- PATH...`; wrong if the cause could be a dependency, build config, or code elsewhere |
| A manual mark was wrong | `git bisect log > f`, delete the wrong `git bisect good/bad` line and the comment line above it, `git bisect reset`, `git bisect replay f` |
| No runnable test, a text change is suspected | `git log -S 'text' --format='%h %s' -- PATH` (count changes) or `-G REGEX` (diff lines); test the commit and its parent, since the commit that added the text need not be the harmful one |

## Flaky and performance oracles

- Flaky test: measure the failure rate on the good endpoint first, then mark bad only if M of K runs
  fail (for example 2 of 3). One spurious failure on a midpoint sends the search into the wrong half
  and names an unrelated commit.
- Slowdown or size growth: exit 1 when a metric crosses a threshold placed between the endpoints'
  measured distributions, and exit 125 when the measurement tool fails. Run the oracle 5 times on
  each endpoint first; if the distributions overlap, use an operation count or more runs. Start with
  `--term-old fast --term-new slow`.

## Verify the culprit

```sh
git checkout -q "$CULPRIT^" && /abs/oracle.sh   # expect 0
git checkout -q "$CULPRIT"  && /abs/oracle.sh   # expect 1
git checkout -q --detach "$BAD"
git revert --no-edit "$CULPRIT" && /abs/oracle.sh   # expect 0
```

- The revert check catches a culprit that only exposed an older defect. If the revert conflicts,
  report it and test the reversed diff by hand.
- When the culprit is a merge (`git log -1 --format=%P "$CULPRIT"` shows two parents), run the
  oracle on both parents. If both pass, the merge itself introduced the defect (a semantic
  conflict).

[git-bisect]: https://git-scm.com/docs/git-bisect
