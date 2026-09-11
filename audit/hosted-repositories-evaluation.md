# Hosted repository operations evaluation

Evaluated 2026-09-12. Replaced the inherited four hosted micro-skills with one
explicit-only `manage-hosted-repositories` package. Issues, PRs/MRs, releases
and settings share provider identity, transport, authorization and
reconciliation; resource-specific differences remain in four conditional
references. A fifth reference owns shared rules once. Retired the original
`git-hosting` package.

The resulting worktree contains 35 skills: 33 manual and two implicit planning
skills. Consolidation does not authorize additional operations: requesting a
review draft, merge, or release does not authorize submission, policy changes,
or publication outside that request.

## Source and command verification

Rechecked the linked official GitHub and GitLab documentation for issues,
comments/notes, PRs/MRs, reviews/approvals, releases/assets, repository/project
settings, protected branches, authentication and transport conventions. CLI help
was inspected with gh 2.100.0 and glab 1.117.0; their pagination options exist,
and gh emits separate page objects unless explicitly aggregated.

Material corrections:

- GitHub merge requires Contents write, whereas review submission requires Pull
  Requests write. Release targets changing workflows can need additional
  Workflows write; never expand privileges solely from a guessed status cause.
- Staged GitHub publication explicitly sets `draft:true`; the endpoint defaults
  to publication. GitLab asset links are not uploaded bytes and release timing
  is not a GitHub-style draft state.
- GitLab `/diffs` replaces deprecated `/changes`; pagination and diff-size
  limits constrain completeness. `/approval_state` establishes rule satisfaction
  rather than counting every entry in `/approvals`.
- A GET before PATCH is not atomic concurrency control. Missing search results
  or one empty page cannot establish that a timed-out creation failed.
- Reconciliation compares author and creation window as well as exact content; a
  preexisting identical issue must not be attributed to the timed-out request.

The package links endpoint-specific primary sources. No private schema, provider
wrapper, retry framework, or custom transport was added.

## Independent recovery scenario

A fresh-context evaluator received a timed-out issue creation, an empty first
page with a next-page link, an empty search result, a GitLab merge SHA conflict,
and a draft-release payload request. It proposed no duplicate creation, did not
substitute the changed MR head, and produced `draft:true` JSON without executing
it. This is independent decision evidence, not a live API transaction.

Integration rejected its deprecated `/changes` request and inadequate exact-body
identity test, then corrected the instructions above. Its proposed human
reauthorization is not a universal requirement for every new commit: assess the
actual request's authorization boundary and review the new head before acting.
The raw response remains `/tmp/hosted-recovery-forward-result.md` and is not
normative endpoint guidance.

## Validation and limits

Both skill validators, strict Markdown, local-link checks, JSON example parsing,
and metadata assertions pass. The current catalog policy count was checked.
Search found no live skill references to the retired names; historical routing
reports remain dated evidence, not current discovery telemetry.

No accounts were accessed and no issues, releases, reviews, settings or tags
were written. Hosted merge rejection, rate-limit timing, token permissions,
concurrent updates, uploads, and provider-side read-back were not executed.
Exact runtime behavior still requires the target account/server; source review
and scenario analysis are not reported as live integration tests.
