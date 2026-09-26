# Pull and merge requests

Creating, reviewing, and merging GitHub pull requests and GitLab merge
requests. The facts come from the [GitHub pulls][pulls],
[reviews][reviews], and [GitLab merge requests][gl-mr] APIs and from the
`gh`/`glab` help text. The merge commands were not measured because they
write to a hosted repository; the PR read ran against `cli/cli`.

## Contents

- Create a pull request
- Review bound to a commit
- Merge only the reviewed head
- Mergeability and required checks
- Auto-merge
- GitLab approvals

## Create a pull request

**Definition.** A pull request asks to merge a head branch that already
exists on the host into a base branch. Creating it does not push commits.
`--draft` marks it not ready for review.

**Use when.** The branch is pushed and the user asked for a PR.

**Do not use when.** The branch is not pushed yet. Push it first with
`git push -u origin HEAD`, a separate step that needs its own approval.

**Example.**

```sh
gh pr create -R owner/repo --base main --head fix-empty --draft \
  --title "Handle empty input" --body-file /tmp/pr-body.md
```

Use `--body-file` for multi-line text; shell quoting is not a
serialization format. The GitLab equivalent is
`POST /projects/:id/merge_requests` with `source_branch`,
`target_branch`, and `title`. Prefix the title with `Draft:` for a
draft.

**Cost removed.** PRs with empty or mis-quoted bodies or the wrong base.

**Verify.**

1. `gh pr view <n> -R owner/repo --json baseRefName,headRefName,isDraft,url`
   matches the request.

## Review bound to a commit

**Definition.** A review applies to the examined commit, given as
`commit_id` in `POST /pulls/{n}/reviews`. `event` is `COMMENT`,
`APPROVE`, or `REQUEST_CHANGES`; omitting it leaves a pending review.
Inline comments need a path and line that exist in the current diff.

**Use when.** Submitting a review the user asked for.

**Do not use when.** The user asked only for a review draft; keep it local
and unsubmitted.

**Example.**

```sh
head=$(gh pr view 42 -R owner/repo --json headRefOid --jq .headRefOid)
gh api repos/owner/repo/pulls/42/reviews --method POST \
  -f commit_id="$head" -f event=COMMENT -f body="$(cat /tmp/review.md)"
```

**Cost removed.** Approvals that silently cover commits pushed after
the review.

**Verify.**

1. `gh api repos/owner/repo/pulls/42/reviews --jq '.[-1].commit_id'`
   equals the SHA you read.

## Merge only the reviewed head

**Definition.** Guard the merge so it succeeds only while the PR head is
still the reviewed commit:

- GitHub: `gh pr merge --match-head-commit SHA`, or `sha` in
  `PUT /pulls/{n}/merge`;
- GitLab: `glab mr merge --sha SHA`, or `sha` in
  `PUT /merge_requests/:iid/merge`. A mismatch returns 409.

**Use when.** Any merge the user authorized.

**Do not use when.** Branch protection or required checks block the merge.
Do not disable them to finish the task.

**Example.** Read, then merge with the guard:

```sh
gh pr view 42 -R owner/repo --json headRefOid,reviewDecision,mergeStateStatus
head=362a5eb03dcc16af5e313ab8ae5a0cfdc4569e46   # the reviewed commit
gh pr merge 42 -R owner/repo --squash --match-head-commit "$head"
```

The read half ran on `cli/cli#14517`:
`MERGED head=362a5eb03dcc`.

**Cost removed.** Merged code that nobody reviewed, pushed in the seconds
between the review and the merge.

**Verify.**

1. After the merge, `gh pr view 42 --json state,mergeCommit` shows
   `MERGED`, and the merge commit contains the reviewed head.

## Mergeability and required checks

**Definition.** GitHub computes mergeability asynchronously: `null` or
`UNKNOWN` means "not computed yet", never "yes". `gh pr checks --required`
lists only the required checks; `mergeStateStatus` summarizes branch
protection.

**Use when.** Before merging, or when asked "is this ready?".

**Do not use when.** You would treat a single `UNKNOWN` read as final.
Read again after a short wait.

**Example.**

```sh
gh pr checks 42 -R owner/repo --required
gh pr view 42 -R owner/repo --json mergeable,mergeStateStatus,reviewDecision
```

**Cost removed.** Premature merge attempts, and "ready" reports that
missed a failing required check.

**Verify.**

1. The report quotes the required checks with their conclusions, and the
   `reviewDecision`.

## Auto-merge

**Definition.** `gh pr merge --auto` merges once the requirements are
met; the repository must allow auto-merge. GitLab's auto-merge fields
depend on the server version, and the old `merge_when_pipeline_succeeds`
flag is deprecated.

**Use when.** The user wants the merge to happen after checks that are
still running.

**Do not use when.** You cannot bind it to the reviewed head. Combine
`--auto` with `--match-head-commit` where the host supports it.

**Example.**

```sh
gh pr merge 42 -R owner/repo --auto --squash --match-head-commit "$head"
```

**Cost removed.** Hand-written polling loops that wait for checks.

**Verify.**

1. `gh pr view 42 --json autoMergeRequest` shows the request, with its
   merge method.

## GitLab approvals

**Definition.** `POST /projects/:id/merge_requests/:iid/approve` takes
the reviewed `sha`; a mismatch returns 409. `GET .../approval_state`
shows which approval rules are satisfied; `/approvals` alone does not.

**Use when.** Approving MRs on GitLab.

**Do not use when.** You would assume one approval satisfies every rule;
check `approval_state`.

**Example.**

```sh
glab api --method POST "projects/123/merge_requests/7/approve" -f sha="$head"
glab api "projects/123/merge_requests/7/approval_state"
```

**Cost removed.** MRs assumed approved while a required rule is unmet.

**Verify.**

1. `approval_state` shows each rule's `approved: true`.

[pulls]: https://docs.github.com/en/rest/pulls/pulls
[reviews]: https://docs.github.com/en/rest/pulls/reviews
[gl-mr]: https://docs.gitlab.com/api/merge_requests/
