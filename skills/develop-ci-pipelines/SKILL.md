---
name: develop-ci-pipelines
description: >-
  Create, repair, or review GitHub Actions, GitLab CI, or Bitbucket pipeline
  behavior when CI configuration or execution is the requested task. Excludes
  hosted settings operations and application bugs unrelated to CI.
---

# Develop CI Pipelines

Apply this workflow when CI configuration or pipeline execution is the requested
work. Implicit activation selects guidance only; it does not authorize hosted
operations or mutations beyond the user's request.

Trace the affected event through workflow creation, job selection, dependencies,
commands, artifacts, and deployment. Diagnose the first failing transition from
its configuration and run evidence.

Read [provider behavior](references/provider-behavior.md), then the affected
provider: [GitHub Actions](references/github-actions.md),
[GitLab CI](references/gitlab-ci.md), or [Bitbucket Pipelines][ref-1].

Require [local pre-commit/pre-push feedback][local-feedback] using the same
underlying CI tasks, with documented hosted-only exceptions. Follow [bounded CI
evidence][ci-evidence] before fetching failure logs.

Use provider-native YAML. Keep required failures visible. Pin executable
dependencies and identify artifact producer revisions. Trace control of checkout
content, interpolated inputs, caches, artifacts, runners, and credentials before
privileged execution.

Validate changed syntax, event selection, dependency flow, and commands. Use
hosted run evidence for trigger, permission, runner, and approval behavior. A
pipeline repair must not bypass a failing gate or deploy an unverified artifact.

[ref-1]: references/bitbucket-pipelines.md
[local-feedback]: ../manage-git-state/references/local-feedback.md
[ci-evidence]: ../manage-hosted-repositories/references/ci-evidence.md
