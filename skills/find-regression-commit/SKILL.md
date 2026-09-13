---
name: find-regression-commit
description: >-
  Find and verify the first Git commit that introduced a reproducible failure
  with an isolated worktree and trustworthy bisect oracle. Not for general
  debugging or lost-commit recovery.
---

# Find Regression Commit

Find the first change that violates a defined, reproducible condition. Preserve
the caller's workspace: use a separate worktree, keep existing checks, and do
not install hooks or edit historical candidates.

Define one good/bad test command (the oracle) for the target: a failure,
build error, or performance threshold. Verify both boundary commits with that
command and the same environment. Resolve unreliable timing, flaky results, or
moving services before using them to label revisions.

In the disposable worktree, run `git bisect start BAD GOOD`, then
`git bisect run /absolute/path/to/oracle`. Keep the oracle outside the changing
checkout if revisions could remove it. Reuse the existing test runner. Interpret
its exit status as follows:

- `0`: the target regression is absent.
- `1–127` except `125`: the target regression is present.
- `125`: the revision cannot be evaluated.
- Any other status: abort the search.

Separate setup failure from the target symptom. A missing dependency is not a
bad revision; a compiler failure is bad when compilation is the target. Handle
shell failures explicitly so a missing command's `127` does not label the
revision bad. Consult the [Git bisect manual][bisect] when choosing search
options; path-limited and first-parent searches change the question.

Save `git bisect log` and oracle output. Read the reported first-bad object or
resolved `refs/bisect/bad`, not merely HEAD, which may remain at the last good
revision tested. Re-run the candidate and relevant predecessor before naming a
first-bad commit. For a merge, inspect its parents and establish whether the
question concerns integration history or an individual branch.

If skips leave several candidates, report the set and missing evidence. Finish
with `git bisect reset`, check that the caller's worktree is unchanged, and
remove only the clean disposable worktree after saving evidence. Report the
verified commit and boundary results, or the unresolved candidates. Localization
does not establish root cause or authorize a revert.

[bisect]: https://git-scm.com/docs/git-bisect
