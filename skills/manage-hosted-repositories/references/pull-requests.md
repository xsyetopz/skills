# Pull Requests

## GitHub

Create via `POST .../pulls` with:

```json
{
  "title": "Handle empty input",
  "head": "fix-empty",
  "base": "main",
  "body": "Preserves the documented empty-input result.",
  "draft": true
}
```

The head must exist remotely; creation does not push local commits. The 201
result includes `number`, `html_url`, `head.sha` and `base.ref`. Updating
title/body/base uses `PATCH .../pulls/NUMBER`; labels use the issues endpoint.
Read both the diff and current head before review or merge.
[PR API](https://docs.github.com/en/rest/pulls/pulls).

To merge, `PUT .../pulls/NUMBER/merge` can include
`{"sha":"EXPECTED_HEAD","merge_method":"squash"}`. The expected SHA protects
against merging a new head unseen by the reviewer. Inspect `merged`, `sha` and
`message`, then independently read the PR. Mergeability can initially be unknown
while GitHub calculates it; wait/re-read rather than interpreting null as true.
Branch rules, checks, approvals and enabled merge methods remain constraints; do
not disable them to complete a merge.

To submit a review, `POST .../pulls/NUMBER/reviews` accepts `commit_id`, `body`
and `event` (`COMMENT`, `APPROVE` or `REQUEST_CHANGES`). Omit `event` to create
a pending review, then submit it through
`POST .../pulls/NUMBER/reviews/REVIEW_ID/events`. Omit API submission when
producing only a local review draft. Bind the review to the examined commit and
verify returned state/URL. Inline comments additionally require the actual diff
path and supported line/side or position fields; re-read the diff after a head
change instead of guessing an old location. Fine-grained tokens need Pull
Requests write permission for submitting reviews; the merge endpoint instead
requires Contents write. Verify each endpoint's permission block rather than
inferring it from the resource name.
[Reviews](https://docs.github.com/en/rest/pulls/reviews).

Read effective branch rules and required checks before review or merge. Changing
those repository settings belongs to [the settings workflow](settings.md).

## GitLab

Create `POST /projects/123/merge_requests` with:

```json
{
  "source_branch": "fix-empty",
  "target_branch": "main",
  "title": "Draft: Handle empty input",
  "description": "Preserves empty-input behavior."
}
```

A 201 response includes `iid`, `web_url`, `sha` and merge status fields. Draft
status can be expressed by the documented title prefix. For forks, resolve
source and target project IDs explicitly. Update using
`PUT /projects/123/merge_requests/7`; notes use `/merge_requests/7/notes`.
`detailed_merge_status` is more informative than assuming the older broad merge
status alone proves readiness.
[MR API](https://docs.gitlab.com/api/merge_requests/).

Read current diffs with `GET /projects/123/merge_requests/7/diffs`, following
pagination and inspecting truncation/size limits. Do not use the deprecated
`/changes` endpoint for new workflows. Missing or collapsed diff content is not
proof that the corresponding changes are harmless.

Merge with `PUT /projects/123/merge_requests/7/merge`, with `sha` equal to the
reviewed source head and optional supported merge choices such as `squash`. A
SHA mismatch returns 409; re-read instead of silently merging the changed
branch. Auto-merge fields vary by server version; do not send deprecated
`merge_when_pipeline_succeeds` merely because an old example did. After merge,
read `state`, merge commit and source-removal result. Select source-branch
deletion explicitly and satisfy required approvals.

Submit an approval with `POST /projects/123/merge_requests/7/approve` with the
reviewed `sha`. The caller must be an eligible approver; SHA mismatch
returns 409. Read `/projects/123/merge_requests/7/approval_state` for rule
satisfaction; `/approvals` alone does not establish which required rules are
satisfied. Do not assume one approval satisfies every rule. Required
reauthentication is a separate account policy and must not be bypassed or
logged. Wait for the MR's diff/approval processing when a new push is still
being processed, so an approval is not immediately reset.
[Approval API](https://docs.gitlab.com/api/merge_request_approvals/).

Read effective protected-branch and approval rules before review or merge.
Changing those project settings belongs to
`the settings workflow in this skill`.
