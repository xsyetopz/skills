# Bisect workflow

Define the target regression before labeling revisions: a behavioral failure,
build failure, performance threshold, or another observable contract. Verify
both supplied endpoints with the same oracle and environment. A flaky predicate
or moving external service is not a reliable binary-search criterion. Preserve
the caller's dirty workspace by running in a separate worktree.

Run `git bisect start BAD GOOD`, then `git bisect run /absolute/path/to/oracle`.
Keep the oracle outside the changing checkout when revisions might remove it.
Use an existing test runner or command; do not invent a bisection framework. Its
exit status means:

- 0: the target regression is absent;
- 1–127 except 125: the target regression is present;
- 125: this revision cannot be evaluated;
- another status: abort the search.

A missing test dependency is not the product regression. Conversely, if the
requested regression is failure to compile, the compiler failure is a relevant
bad result, not automatically a skip. Distinguish setup failures from the target
symptom. Check shell command failures explicitly: a missing command's 127 can
otherwise be interpreted as bad. See the current
[Git bisect manual](https://git-scm.com/docs/git-bisect).

Save `git bisect log` and the observed oracle output. Read the reported
first-bad object (or resolved `refs/bisect/bad` after a successful search), not
merely HEAD: HEAD can remain at the last tested good revision. Reproduce the
candidate and its relevant predecessor using the same command before concluding
that it introduced the regression. At merges, inspect the parent topology and
define whether the question concerns integration history or an individual
branch; do not assume every candidate has one parent. Path-limited or
first-parent search changes the question and needs justification.

Skipped commits can leave multiple possible first-bad candidates. Report that
set and the missing evidence rather than selecting one. Finish with
`git bisect reset`, verify the original worktree remains untouched, and remove
only the clean disposable worktree after preserving evidence. A first-bad commit
is localization evidence, not automatically a root-cause explanation or
permission to revert it.
