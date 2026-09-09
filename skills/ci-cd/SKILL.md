---
name: ci-cd
description:
  Create, repair, or review GitHub Actions, GitLab CI, or Bitbucket pipeline
  behavior. Excludes hosted settings operations and application bugs unrelated
  to CI.
---

# CI/CD

Trace the affected event through workflow creation, job selection, dependencies,
commands, artifacts, and deployment. Diagnose the first failing transition from
its configuration and run evidence.

Read [provider behavior](references/provider-behavior.md), then the affected
provider: [GitHub Actions](references/github-actions.md),
[GitLab CI](references/gitlab-ci.md), or [Bitbucket Pipelines][ref-1].

Use provider-native YAML. Keep required failures visible. Pin executable
dependencies and identify artifact producer revisions. Trace control of checkout
content, interpolated inputs, caches, artifacts, runners, and credentials before
privileged execution.

Validate changed syntax, event selection, dependency flow, and commands. Use
hosted run evidence for trigger, permission, runner, and approval behavior. A
pipeline repair must not bypass a failing gate or deploy an unverified artifact.

[ref-1]: references/bitbucket-pipelines.md
