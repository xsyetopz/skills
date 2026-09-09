---
name: git-hosting
description:
  Perform GitHub or GitLab hosted repository operations, including issues, pull
  requests, merge requests, releases, and settings. Excludes local Git changes
  and pipeline-file implementation.
---

# Git Hosting

Resolve provider, host, repository/project, resource identity, and requested
effect. Use an authenticated connector or provider CLI. Keep credentials out of
output and command arguments.

Read [provider semantics](references/provider-semantics.md) for IDs, pagination,
API versions, errors, and ambiguous writes. Read
[GitHub workflows](references/github-workflows.md) or
[GitLab workflows](references/gitlab-workflows.md) for endpoint payloads and
operation-specific permissions.

Use native request schemas. Send only intended fields. Preserve literal
multiline content through structured arguments or body files. Refresh the
affected endpoint for a different server/API version or an uncovered field.

Reuse authorization for the requested effect. Prepare concrete content before
requesting a missing target or decision. After a mutation, independently read
the resource and compare fields and state. Reconcile unknown outcomes before
retrying creation. Report the resource URL/ID and observed result.
