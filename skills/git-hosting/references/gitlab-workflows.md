# GitLab issues, MRs, releases and settings

Research: 2026-09-09; current GitLab REST v4 documentation. Use the selected
server's supported fields; SaaS docs can include newer Self-Managed features.
Authentication can use configured `glab`, OAuth or an existing scoped token;
never include a token in printed command arguments.

## Issues and notes

`POST /projects/123/issues` accepts `title` and `description`; success returns
201 with global `id`, project-local `iid` and `web_url`. Update with
`PUT /projects/123/issues/7`, using `state_event:"close"` or `"reopen"` for
transitions. GitHub's `body` and `state:"closed"` are not equivalent GitLab
input fields. Add a note with `POST /projects/123/issues/7/notes` and `body`;
note editing requires the note ID.
[Issues](https://docs.gitlab.com/api/issues/),
[notes](https://docs.gitlab.com/api/notes/).

For pagination or confidential issues, distinguish “not returned” from “does not
exist.” Visibility depends on account access. Editing assignees, labels or
milestones is an explicit field change; preserve omitted values.

## Merge requests

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

Merge with `PUT /projects/123/merge_requests/7/merge`, with `sha` equal to the
reviewed source head and optional supported merge choices such as `squash`. A
SHA mismatch returns 409; re-read instead of silently merging the changed
branch. Auto-merge fields vary by server version; do not send deprecated
`merge_when_pipeline_succeeds` merely because an old example did. After merge,
read `state`, merge commit and source-removal result. Select source-branch
deletion explicitly and satisfy required approvals.

## Release content and assets

`POST /projects/123/releases` accepts `tag_name`, `name`, `description`, and
`ref` when a missing tag must be created. Assets can include links with `name`
and `url`; these are references, not proof that binary bytes were uploaded.
Upload release binaries through the package/upload endpoint before linking them.
`released_at` controls release timing metadata; it is not a generic GitHub-style
draft toggle. [Releases](https://docs.gitlab.com/api/releases/).

Read back by URL-encoded tag at `/projects/123/releases/TAG`. Compare notes,
tag, asset links and timing. Treat tag deletion and release deletion as separate
operations. Finalize local notes and artifact identity before release creation;
verify each external asset URL after release creation.

## Project settings and authority

`GET /projects/123` establishes current visibility, default branch, enabled
features and merge settings. `PUT /projects/123` edits selected supported
fields, for example `{"description":"Documented project purpose"}`. Do not copy
a GET object wholesale into PUT: response fields include read-only and unrelated
policy values. Project role, token scopes and protected resources jointly
constrain authority; an `api` scope does not grant a role the user lacks. CI job
tokens support only specific APIs, not arbitrary administrative operations.
[Projects](https://docs.gitlab.com/api/projects/), [authentication][ref-1].

For 400 field errors, inspect `message`; for 401/403 stop and report the exact
missing access; for 429 follow rate-limit headers. A failed creation can have an
uncertain result after transport loss, so reconcile before retrying. Read
[transport and recovery](provider-semantics.md) for shared rules.

## Approval and protected branches

Submit an approval with `POST /projects/123/merge_requests/7/approve` with the
reviewed `sha`. The caller must be an eligible approver; SHA mismatch
returns 409. Read the resulting approval state and rules rather than assuming
one approval satisfies every rule. Required reauthentication is a separate
account policy and must not be bypassed or logged. Wait for the MR's
diff/approval processing when a new push is still being processed, so an
approval is not immediately reset. [Approval API][ref-2].

Read `/projects/123/protected_branches` and the named branch before changing
protection. Creating a policy uses `POST /projects/123/protected_branches` with
`name` and intended access settings. A structural policy for a new branch could
use this payload for no direct pushes, Maintainer merges, and no force push:

```json
{
  "name": "release",
  "push_access_level": 0,
  "merge_access_level": 40,
  "allow_force_push": false
}
```

Set access fields from the intended branch policy. Access levels include 0 for
no push/merge access, 30 Developer and 40 Maintainer; 0 is not valid as an
unprotect access level. User/group/deploy-key and custom-role selectors have
tier/server constraints. Updating existing access entries requires their IDs and
supported update fields; do not delete/recreate protection merely to avoid
understanding them. [Protected branches][ref-3].

Wildcard policies can overlap. Check effective permission and inherited/group
rules after a change, not only the one returned object.

[ref-1]: https://docs.gitlab.com/api/rest/authentication/
[ref-2]: https://docs.gitlab.com/api/merge_request_approvals/
[ref-3]: https://docs.gitlab.com/api/protected_branches/
