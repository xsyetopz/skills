# Classify software failures during git bisect

git bisect classifies revisions against one software-failure condition. The test
oracle is the command that classifies that condition as working, defective, or
untestable; an unrelated command failure must not be classified as the defect.

For `git bisect run`, status 0 means good; statuses 1 through 127 except 125
mean bad; 125 means skip. A status greater than 127 aborts. Consequently, shell
statuses 126 and 127 for command/invocation failure can accidentally label a
revision bad. Validate required tooling before the run and translate
infrastructure failures to an abort status, not to “bad.” Use only a documented
predicate for skip.

Keep the failure-classification command at an absolute path outside the bisected
checkout. It should build the selected revision, execute the same fixture, and
classify the **target** symptom. Store raw output per revision so that a
classification can be reviewed. Do not classify every nonzero exit from a
complex test command as the regression without checking what that exit means.

Illustrative command sequence; replace the uppercase values with verified
values, not literal strings:

```sh
git worktree add --detach "$CASE_WORKTREE" "$BAD_COMMIT"
git -C "$CASE_WORKTREE" bisect start "$BAD_COMMIT" "$GOOD_COMMIT"
git -C "$CASE_WORKTREE" bisect run "$ABSOLUTE_ORACLE"
git -C "$CASE_WORKTREE" bisect log > "$EVIDENCE_DIR/bisect.log"
git -C "$CASE_WORKTREE" rev-parse refs/bisect/bad
# Save the final output and independently verify candidate and parent(s).
git -C "$CASE_WORKTREE" bisect reset
git worktree remove "$CASE_WORKTREE"
```

Inspect every command's status; this sequence is not an unattended script. The
final bad ref alone does not prove a unique answer when skips remain. Do not
remove a worktree with unpreserved changes, and do not add `--force` to hide
that condition.

A performance predicate needs a sufficiently stable workload and threshold to
separate endpoints. If the noise overlaps the distinction, improve measurement
before automating the search. A flaky predicate can steer binary search into the
wrong half of history.

A path-limited or first-parent search asks a narrower question than searching
the full ancestry. Use it only when that is the intended question and describe
the limitation. Verify historical submodule versions, generated code, and
toolchains; a contemporary environment can introduce failures that did not exist
at the time.

Source: [git-bisect manual][ref-git-bisect-manual].

[ref-git-bisect-manual]: https://git-scm.com/docs/git-bisect
