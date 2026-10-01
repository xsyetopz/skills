# GitHub with gh

Commands are POSIX sh; on Windows run them in Git Bash or WSL.

## Contents

- [Create a pull request](#create-a-pull-request)
- [Review a pull request](#review-a-pull-request)
- [Merge and checks](#merge-and-checks)
- [Issues and labels](#issues-and-labels)
- [Releases](#releases)
- [Branch rules and settings](#branch-rules-and-settings)
- [CI evidence](#ci-evidence)
- [Pagination and GraphQL](#pagination-and-graphql)

## Create a pull request

Creating a PR does not push. Push first, as its own authorized step:
`git push -u origin HEAD`.

```sh
gh pr create -R owner/repo --base main --head fix-empty --draft \
  --title "Handle empty input" --body-file pr-body.md
gh pr view N -R owner/repo --json baseRefName,headRefName,isDraft,url
```

From a fork, pass `--head user:branch`. A draft stays a draft until the
user asks to publish: `gh pr ready N`.

## Review a pull request

```sh
gh pr view 42 -R owner/repo --json headRefOid --jq .headRefOid
gh api repos/owner/repo/pulls/42/reviews --method POST \
  -f commit_id=SHA -f event=COMMENT -F body=@review.md
```

SHA is the head printed by the first command.

`event` is `COMMENT`, `APPROVE`, or `REQUEST_CHANGES`; omitting it leaves
a pending review. Inline comments need a `path` and a `line` that exist
in the current diff, sent as a `comments` array with `--input`. If the
user asked only for a draft review, keep it local.

## Merge and checks

```sh
gh pr view 42 -R owner/repo \
  --json headRefOid,reviewDecision,mergeStateStatus,mergeable
gh pr checks 42 -R owner/repo --required
gh pr merge 42 -R owner/repo --squash --match-head-commit "$head"
```

- `gh pr checks --required` lists only required checks. Quote their
  conclusions and `reviewDecision` when reporting readiness.
- `--auto` merges after the requirements pass; the repository must allow
  auto-merge. Combine it with `--match-head-commit`. Read
  `gh pr view 42 --json autoMergeRequest` afterward.
- Afterward, `gh pr view 42 --json state,mergeCommit` shows `MERGED`.
- If a merge times out, read the PR state before retrying.

## Issues and labels

```sh
gh issue list -R owner/repo --state all --search 'in:title "flaky: test_x"' \
  --json number,title,state
gh issue create -R owner/repo --title "flaky: test_x" --label flaky \
  --body-file /tmp/issue.md
gh label list -R owner/repo --limit 200 --json name,color,description
gh label edit NAME -R owner/repo --color RRGGBB
```

- `gh label list` returns 30 labels unless `--limit` is raised.
- Do not delete a label to "sync" it; deletion removes it from every
  issue. Edit it, and delete only when the user asked.
- When the user asked for a new issue and a similar one exists, create
  it and link the existing one.

## Releases

Create a draft and verify the assets. Publish (`--draft=false`, visible to
all users) only when the user asked to publish:

```sh
gh release create v1.4.0 -R owner/repo --draft --verify-tag \
  --title v1.4.0 --notes-file CHANGES.md dist/*.tar.gz
gh release view v1.4.0 -R owner/repo --json assets \
  --jq '.assets[] | [.name, .size]'
gh release edit v1.4.0 -R owner/repo --draft=false
```

`--verify-tag` aborts when the tag is missing instead of creating one at
the default branch head. `--latest=false` keeps a backport from becoming
"Latest". Publishing and deleting need the user's explicit request.

## Branch rules and settings

Read before changing: `gh api repos/owner/repo/branches/main/protection`
and `gh api repos/owner/repo/rulesets`. Changing protection, visibility,
or transferring a repository needs the user to name that exact effect.
Send only the changed fields, and read back afterward.

## CI evidence

CI evidence belongs to one head SHA and run. Write failed logs to a file
and search it; do not load whole logs into context.

```sh
gh pr checks 42 -R owner/repo --json name,state,link
gh run view RUN_ID -R owner/repo --log-failed > failed.log
grep -n -m 20 -E 'error|FAIL' failed.log
```

A run for an older head says nothing about the current commit. Report
the run ID, head SHA, failing step, and quoted error lines.

## Pagination and GraphQL

`gh api --paginate --slurp PATH` returns one array of pages; flatten it
with `jq '[.[][]]'`. For review threads and resolved state use GraphQL:

```sh
gh api graphql -f query='query($o:String!,$r:String!,$n:Int!){
  repository(owner:$o,name:$r){pullRequest(number:$n){
    reviewThreads(first:100){nodes{id isResolved path
    comments(first:1){nodes{body}}}}}}}' \
  -f o=owner -f r=repo -F n=42
```

GraphQL connections cap at 100 nodes per page; follow `pageInfo` for more.
