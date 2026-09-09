# Hosted requests, identity and recovery

Research: 2026-09-09. GitHub REST examples use the current documented
**2026-03-10** API version; GitLab uses REST **v4**. SaaS behavior is
continuously released.

## Resolve the request

Read the configured CLI host and repository identity without printing tokens.
GitHub REST uses owner/repository and an issue/PR number; GraphQL uses opaque
node IDs. GitLab uses a project ID or URL-encoded full path
(`group%2Fsubgroup%2Frepo`), plus project-local issue/MR `iid`. A global MR `id`
is not the URL IID. Prefer resolving a numeric project ID once to avoid repeated
path encoding. [GitLab REST conventions][ref-1].

Distinguish local drafts, hosted creation, merge, publication, and policy
changes. Reuse authorization for the requested effect.

## Pagination and transport

GitHub REST lists commonly default to 30 items; request `per_page=100` where
supported and follow the response `Link` relation `next` until absent.
`gh api --paginate 'repos/OWNER/REPO/issues?state=all&per_page=100'` retrieves
all pages; this endpoint includes PR-like issues, so filter the `pull_request`
field when counting ordinary issues. A page array is not necessarily a single
aggregate JSON array. [Pagination][ref-2].

For GraphQL, request `first`/`after` and `pageInfo { hasNextPage endCursor }`,
then feed the cursor back. Inspect `errors` even on HTTP 200, including partial
`data`; an errored field is not evidence of absence. POST `/graphql` can be a
read-only query. [GraphQL limits][ref-3].

GitLab offset lists use `page`/`per_page`, `Link` and `X-Next-Page`; follow
keyset URLs unchanged when the endpoint uses keyset pagination. Total-count
headers may be absent for large collections. Use
`glab api --paginate 'projects/123/merge_requests?state=opened&per_page=100'`
for all open MR pages. Do not change host to work around a permission failure.

## Errors and ambiguous writes

- **401 or inaccessible integration** Response: Check existing credential
  identity, expiry and target access; stop rather than broadening privileges.

- **403/429 with rate-limit evidence** Response: Honor `Retry-After`; for GitHub
  exhausted quota use `X-RateLimit-Reset`. Bound retries and back off for
  secondary limits.

- **404 on a known private resource** Response: Check host, encoding and access.
  It can conceal an authorization failure.

- **400/422 validation body** Response: Inspect field errors and endpoint types.
  Correct the request; do not retry unchanged.

- **409/head mismatch** Response: Re-read the current revision and reassess the
  authorized change.

- **Timeout/5xx after creation** Response: Treat outcome as unknown. Search by
  exact target and stable identity before creating again.

GitHub's `X-Accepted-GitHub-Permissions` can identify the endpoint's permission
requirements. Error bodies may contain sensitive user content; summarize
narrowly. [GitHub troubleshooting][ref-4].

After a write, independently GET the resource and compare changed fields, state
and revision. For creations compare author, head/base or tag, full content and
timestamp; title similarity alone is insufficient. Use an idempotency key only
when the endpoint documents it. For concurrent edits, use endpoint-supported
preconditions or re-read immediately before a narrowly scoped patch.

Use [GitHub operations](github-workflows.md) or
[GitLab operations](gitlab-workflows.md) for concrete resource workflows.

[ref-1]: https://docs.gitlab.com/api/rest/
[ref-2]:
  https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api
[ref-3]: https://docs.github.com/en/graphql/overview/resource-limitations
[ref-4]:
  https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api
