# Pipeline diagnosis and provider routes

Examples below illustrate provider contracts. Resolve repository commands,
images, action revisions, and server support before applying them.

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

## Build, promotion and provenance

Build once for a release candidate and promote the same digest through the
required checks and environments. An artifact name or tag can be reused; record
its immutable identity, source revision, producer workflow and dependencies. If
retention expires, rebuild and revalidate under the release procedure rather
than silently replacing the approved bytes. Define rollback for both application
and data changes; redeploying an older binary cannot reverse every migration.

When supply-chain evidence is required, use existing platform attestation tools
and standard [SLSA provenance](https://slsa.dev/spec/v1.2/provenance), not a
custom signed JSON envelope. Produce an SPDX or CycloneDX SBOM with maintained
tooling when the project's delivery contract requires one. An SBOM inventories
components; it is neither a vulnerability-free guarantee nor proof of build
provenance.

Verify attestations against expected artifact digest and producer identity at
the consuming boundary. A signature alone does not establish that its builder
was authorized or isolated. GitHub's [artifact attestations][attestations] are
one provider implementation; check access, runner and repository support instead
of assuming every pipeline can emit or verify them identically.

Partition tests only when each required test has an identified shard and results
are aggregated without hiding failures. Measure critical-path time, queue time
and cache hit/miss behavior before expanding runner matrices or parallelism. Do
not let a cache hit skip a required verification unless the cached result's
identity and the existing policy explicitly justify reuse.

[attestations]:
  https://docs.github.com/en/actions/concepts/security/artifact-attestations
