# Isolate subagent software edits and Git operations

Parallel agents must not coordinate by destructively rewriting one shared
working tree.

## Workspace choices

Use the lightest mechanism the project can sustain:

- isolated worktrees/checkouts per work partition;
- isolated agent host workspaces with patch/commit handoff;
- one shared checkout with disjoint write ownership and serialized integration.

Large repositories may make one worktree per worker impractical. Use a small
fixed number of worktrees and schedule multiple non-overlapping workers within
each only if writes remain isolated.

## Worker Git policy

Workers may inspect Git status, diffs, and history within their assigned scope.
Create commits only when the user or applicable repository instructions
explicitly authorize them. File patches are sufficient otherwise. Workers must
not use broad destructive commands to coordinate their changes:

- `git reset --hard`;
- `git clean -fdx` or equivalent mass deletion;
- stash push/pop shared across workers;
- force push or history rewrite;
- checkout/restore of paths they do not own;
- blanket conflict resolution that chooses one side without review.

The integrator owns merges/rebases/cherry-picks according to project policy.

## Transfer changes by commit when authorized

When commits are used, prefer one work item or coherent reviewed unit per
commit. Record base and result hashes. Do not claim a commit is verified merely
because it is atomic.

## Existing user state

Never destroy or overwrite unrelated local changes. Before any operation that
can affect the worktree, inspect state and preserve out-of-scope files.
