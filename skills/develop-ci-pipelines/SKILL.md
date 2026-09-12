---
name: develop-ci-pipelines
description: >-
  Use only when explicitly invoked by name. Create, repair, or review GitHub
  Actions, GitLab CI, or Bitbucket pipeline behavior. Excludes hosted settings
  operations and application bugs unrelated to CI.
---

# Develop CI Pipelines

Run this workflow only when the user explicitly invokes this skill by name. A
related keyword or an ordinary implementation request is not an invocation.

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
