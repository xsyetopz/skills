# Verification and claim evidence for Local Git State

Select evidence that can discriminate the claimed property of the local Git
operation. Run the smallest sufficient check first. Broaden only when another
contract boundary changed.

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

For the local Git operation, separate authored checks, executed checks, static
analysis, simulation, host/integration execution, production observations,
skips, and unavailable checks. Include useful failure output. A green check
establishes only the property that it can discriminate.
