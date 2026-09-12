---
name: manage-hosted-repositories
description: >-
  Use only when explicitly invoked by name. Manage GitHub or GitLab issues,
  pull/merge requests, hosted releases, and repository settings using verified
  provider contracts. Excludes local Git operations, pipeline implementation,
  governance files, and changelog writing.
---

# Manage Hosted Repositories

Run this workflow only when the user explicitly invokes this skill by name. A
related keyword or an ordinary implementation request is not an invocation.

Resolve provider, host, repository/project, resource identity, and the requested
effect. Read [identity and recovery](references/provider-semantics.md), then
only the relevant resource workflow:

- [Issues](references/issues.md): content, comments, fields, and state changes.
- [Pull/merge requests](references/pull-requests.md): creation, review and
  merge.
- [Releases](references/releases.md): drafts, publication and artifact identity.
- [Settings](references/settings.md): metadata, protections and hosted policy.

For code PR/MR work, apply [mandatory local feedback][local-feedback]; read-only
reviews report gaps without installing hooks. For check failures, read
[bounded CI evidence](references/ci-evidence.md) before retrieving logs.

Selecting one operation does not authorize other operations. A local review
draft is not permission to submit it, and a merge request is not permission to
weaken branch policy. Preserve unrelated fields, permissions, and content.

Use native API contracts or an authenticated provider connector/CLI. Bind
reviews and merges to the examined head SHA. Preserve multiline bodies through
structured inputs or body files; do not interpolate untrusted text into shell
syntax. Reconcile uncertain writes before retries. Read back the changed
resource and report its URL/ID and observed state; distinguish publication,
tagging and upload.

[local-feedback]: ../manage-git-state/references/local-feedback.md
