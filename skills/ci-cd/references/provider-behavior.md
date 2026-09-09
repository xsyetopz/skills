# Pipeline diagnosis and provider routes

Research: 2026-09-09. GitHub Actions and Bitbucket Cloud are continuously
released services; GitLab examples use current CI YAML documentation, with
server-version compatibility required for Self-Managed installations.

## Trace the failing path

Start with event type, source repository/ref/SHA, selected workflow, job
dependencies and runner image. For each edge, identify what travels across it:
status, an output value, artifact bytes, credentials or a deployment identity.
Compare the actual failing command and working directory with local execution.
Read the exit status and logs of the failing command.

Diagnose selection before execution: a workflow that was never created differs
from a skipped job; a skipped dependency differs from a successful producer with
no artifact. Follow the provider's rules in [GitHub](github-actions.md),
[GitLab](gitlab-ci.md), or [Bitbucket](bitbucket-pipelines.md).

## Trust and failure propagation

Treat branch names, PR titles, repository content and downloaded artifacts as
data controlled by their producer. Pass expression values through environment
variables/structured inputs rather than constructing shell source. A privileged
workflow must not execute an untrusted checkout or artifact just because a
previous job uploaded it. Self-hosted runners can retain state across jobs;
isolation assumptions must match their provisioning.

Cache only recomputable inputs/outputs. Key dependencies by OS, architecture,
runtime and lockfile where those affect compatibility. Validate cached input
identity before privileged use. Transfer build outputs as artifacts with an
identified producer run and revision; publish/deploy the tested artifact rather
than rebuilding an untracked variant.

Retain required failure propagation. `continue-on-error`, `allow_failure`,
unconditional shell success and pipeline commands without suitable pipe failure
handling can hide a real failed gate. Cleanup can run after failure without
making the failed work successful.

Deployment credentials belong only to the deployment job, after its source and
artifact are established. Restrict OIDC issuer, audience, subject/ref, and
environment at the cloud role. Configure approval policy in provider settings.

Validate the changed YAML and event/dependency cases, then the commands changed
by the patch. Static validation cannot establish hosted secrets, permissions,
approvals or runner availability. Check deployment and branch controls at the
provider settings boundary.
