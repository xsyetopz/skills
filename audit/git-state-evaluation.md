# Git capability consolidation and evaluation

Evaluated 2026-09-11–12 with Git 2.55.0. This records local Git behavior, not
hosted repository administration or acceptance of the full suite.

## Cohesion decision

Combine the inherited commit, integration, and recovery micro-skills into
`manage-git-state`. They all transform Git refs/index/worktree state, preserve
unrelated content, and verify resulting objects. Their references duplicated
state inspection and fragmented short procedures behind extra routing files. Two
references now keep snapshot/ref operations and integration/recovery separate
without making users choose among three closely coupled skills. Local annotated
tags have an explicit owner, resolving a catalog coverage gap.

Keep `find-regression-commit` separate: its outcome is evidence locating a
regression, not a requested state mutation, and it needs a deterministic oracle,
known endpoints, skip semantics, and candidate verification. The resulting
catalog has 38 skills, not as a target count but as a consequence of this merge.
Historical catalog reports retain their original skill names.

The original `git-operations` files are retired with the new packages. Their
useful commands and safety contracts remain; no compatibility alias or custom
Git wrapper is introduced.

## Sources and corrections

Reopened the official manuals for [commit](https://git-scm.com/docs/git-commit),
[tag](https://git-scm.com/docs/git-tag),
[stash](https://git-scm.com/docs/git-stash),
[rebase](https://git-scm.com/docs/git-rebase),
[reset](https://git-scm.com/docs/git-reset),
[revert](https://git-scm.com/docs/git-revert),
[Git environment](https://git-scm.com/docs/git),
[path parsing](https://git-scm.com/docs/git-rev-parse), and
[bisect](https://git-scm.com/docs/git-bisect).

Guidance distinguishes worktree-path commits from staged-hunk commits, preserves
both staged identity and unsaved bytes, verifies annotated tag targets, and does
not treat local tagging as publication. It avoids inventing serialization for
Git state. Bisect guidance distinguishes unavailable prerequisites from the
actual target regression and does not claim a candidate is a root cause.

## Independent scoped-commit and tag task

A fresh-context evaluator received a copied dirty repository and a request to
commit only the staged `settings.txt` change, preserve its additional unstaged
edit plus staged/unstaged `notes.txt` and untracked `scratch.txt`, then create
local annotated tag `trial-1`. No push was authorized.

The final commit `60a534b17c2d28076b584ada239c7a357921b744` changes only
`limit=10` to `limit=20`; it does not include `mode=experimental` or notes. The
evaluator used an isolated index and normal `git commit`, then created the
annotated tag. Integration independently compared original/final staged blobs,
all three worktree files, commit contents, tag object type, and peeled target.
All required content and staging distinctions are preserved. No remote write
occurred.

The first attempt failed because the evaluator copied the wrong repository's
index: `git -C repo rev-parse --git-path index` returned relative `.git/index`,
which a later shell command resolved against the coordinator workspace. The
initial report incorrectly blamed fixture cache-tree corruption. Integration
reproduced correct copying from the fixture and successfully wrote its intended
tree; command-history review confirmed the path mistake. The report attribution
was corrected, not retained as an invented Git defect.

The skill now uses the documented absolute-path option when resolving an index
outside the current shell directory, also avoiding a hard-coded linked-worktree
`.git/index` assumption. This change follows a demonstrated failure rather than
adding another fallback around Git errors.

Seven reviewer routing cases covered explicit commit/tag use, paraphrased scoped
commit, an incomplete local-tag request, adjacent hosted PR work, a read-only
negative request, ambiguous Git cleanup, and commit/tag plus hosted PR
composition. Known-domain requests can select the skill before details are
available; a keyword alone does not authorize mutation.

## Real bisect execution

A disposable repository has a Python price-minus-discount implementation and a
known commit that changes subtraction to addition. Unrelated commits surround
the regression. An external executable oracle returns 0 for the correct total
and 1 for the changed result. Git bisect ran in a detached worktree while the
original retained dirty notes.

Git found `e17a7e042b820719973628f7f71b60540ed8db28`, the actual change. A
verification assumption failed: HEAD remained at the last-tested good revision
rather than the reported candidate. Guidance now records the reported object or
successful-search `refs/bisect/bad`, not merely HEAD. The bisect log was saved,
bisect reset completed, and explicit checkouts reproduced candidate failure (1)
and parent success (0). The clean disposable worktree was removed; the original
dirty file remained.

No claim is made for skipped-candidate ambiguity, performance/flaky oracles,
merge topology, signed tags, remote leases, conflicting rebases, or reflog
recovery in these executions. Those workflows retain source-backed guidance but
need task-specific runtime evidence.

## Gates

Both packages pass official skills-ref, the bundled quick validator, YAML-field
checks, Markdown, and relative links. Retired names are absent from live skill
Markdown/YAML; historical audits intentionally retain them. `git diff --check`
passes. Test repositories and generated indexes remain outside the skill tree;
no hooks, signing rules, or test diagnostics were disabled.
