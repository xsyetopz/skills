# Verification and evidence

Select evidence at the boundary of the claim. Run the smallest sufficient set
first, then broaden only when the change crosses another contract boundary.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Commit contains intended change | `git show`/tree diff of actual commit after hooks. | Pre-commit working-tree diff. |
| Unrelated state preserved | Before/after path- and index-aware status/diff comparison. | Repository appears clean. |
| Rebase/merge correct | Resulting graph, resolved diffs, tests, and intended parents/order. | Command exit 0. |
| Remote update succeeded | Fetched/queried remote ref matches intended commit and provider protection result. | Local branch moved. |
| Recovery is possible | Recorded original refs/reflog/tag/backup and object availability. | Belief that Git never loses data. |

## Command patterns

```sh
git status --short --branch
git diff --
git diff --cached --
git worktree list --porcelain
git rev-parse --show-toplevel HEAD
```

Inspect from the repository root. Add pathspecs and quote them; do not run
destructive commands from a generic recipe.

## Result reporting

Separate authored checks, executed checks, static analysis, simulation,
integration/host execution, production observations, skipped checks, and
unavailable checks. Include relevant failure output. A green check establishes
only the properties it can discriminate; a single flaky pass, successful parser,
or valid configuration file is not broad runtime proof.
