# GitHub issues, PRs, releases and settings

Research: 2026-09-09; REST 2026-03-10, authenticated `gh` request examples.
Substitute known owner/repository and IDs. The configured account must already
have the operation's repository access.

## Issues and comments

`POST /repos/OWNER/REPO/issues` accepts `title`, `body`, and optional
labels/assignees. A successful creation returns 201 with `number`, `html_url`
and state. Update selected fields with `PATCH .../issues/NUMBER`; close using
`{"state":"closed"}`. `POST .../issues/NUMBER/comments` takes `{"body":"..."}`;
editing uses `/issues/comments/COMMENT_ID`, not the issue number. PR
conversation comments share these endpoints; inline review comments have
different position/diff contracts. Use Issues write permission for issue
mutations. [Issues](https://docs.github.com/en/rest/issues/issues),
[comments][ref-1].

For literal multiline content, prepare a UTF-8 body file and run the command
below:

```sh
gh issue create --repo OWNER/REPO --title 'Concrete defect' \
  --body-file /tmp/issue-body.md
```

Shell interpolation is not a serialization method.

## Pull request lifecycle

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

## Releases

Create `POST .../releases` with `tag_name`, `name`, `body`, `draft` and
`prerelease`. `target_commitish` matters when creating a missing tag, so resolve
the intended commit first. Publication can make both release content and
artifacts visible. A draft release is still a hosted mutation. Upload assets to
the returned `upload_url` after removing its URI template, supplying asset name,
binary bytes and content type. Inspect returned asset ID/size and the release
afterward. [Releases][ref-2], [assets][ref-3].

Prepare notes and artifact hashes. Create the release, upload assets, and verify
them. Set `draft:false` to publish. Define “latest” explicitly: release
publication order, semantic version precedence and prerelease eligibility
differ. Deleting a release is not the same as deleting its Git tag; verify each
requested effect separately.

## Repository settings

Read `GET /repos/OWNER/REPO`, then `PATCH` only the requested fields, for
example `{"has_wiki":false}`. Settings commonly require Administration write
permission, while release creation uses Contents write. Visibility, archiving,
transfer and deletion have broader consequences than editing metadata; resolve
the exact effect before issuing those requests. Branch protection and rulesets
have their own endpoints and schemas. [Repository endpoints][ref-4].

Patch intended settings only. Verify changed values with an independent GET. For
unsupported Enterprise fields or a new endpoint, refresh that endpoint's schema
and permission block; the procedures here do not imply all GitHub servers have
SaaS parity.

## Reviews and protected-branch changes

To submit a review, `POST .../pulls/NUMBER/reviews` accepts `commit_id`, `body`
and `event` (`COMMENT`, `APPROVE` or `REQUEST_CHANGES`). Omit `event` to create
a pending review, then submit it through
`POST .../pulls/NUMBER/reviews/REVIEW_ID/events`. Omit API submission when
producing only a local review draft. Bind the review to the examined commit and
verify returned state/URL. Inline comments additionally require the actual diff
path and supported line/side or position fields; re-read the diff after a head
change instead of guessing an old location. Pull Requests write access is
required for these mutations. [Reviews][ref-5].

To change branch protection, read `/repos/OWNER/REPO/branches/BRANCH/protection`
first. The full `PUT` endpoint requires a complete intended configuration for
required checks, administrator enforcement, review requirements and
restrictions; null can disable a protection. Do not send a small
repository-metadata patch to this endpoint. Prefer its narrower subresource
endpoint when changing one supported protection. Arrays of allowed users/teams
replace previous arrays, so preserve existing entries unless removal was
requested. Branch names need URL encoding; wildcard policy belongs to the
appropriate ruleset/GraphQL contract rather than assuming this REST path accepts
a pattern. Read back the changed protection and applicable rules; verify that
unrelated protections remain effective. [Branch protection contract][ref-6].

[ref-1]: https://docs.github.com/en/rest/issues/comments
[ref-2]: https://docs.github.com/en/rest/releases/releases
[ref-3]: https://docs.github.com/en/rest/releases/assets
[ref-4]: https://docs.github.com/en/rest/repos/repos
[ref-5]: https://docs.github.com/en/rest/pulls/reviews
[ref-6]: https://docs.github.com/en/rest/branches/branch-protection
