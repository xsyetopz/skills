# CI pipeline evaluation

Evaluated 2026-09-12. Integrated explicit-only `develop-ci-pipelines`, replacing
`ci-cd`. Consolidated seventeen fragments into four shared/provider references.
The workflow remains diagnosis-first: event selection, job dependencies,
commands, artifacts, credentials and deployment are distinct boundaries.

## Source review

Rechecked official GitHub workflow/security/artifact documentation, GitLab YAML,
workflow and ID-token contracts, and Bitbucket start/step/artifact
documentation. Added standard SLSA provenance and platform attestations as
alternatives to custom signed metadata, with explicit consumer verification and
no security guarantee from a signature alone. SBOMs, provenance, promotion and
rollback serve different purposes; no new framework or mandatory signing policy
was introduced.

GitHub example action placeholders were replaced by verified upstream v6 commit
SHAs. The pinned action READMEs establish Node24/runner requirements and GHES
artifact limitations. The example keeps its repository-specific build command
explicitly identified as an integration point, not a supplied executable.
GitLab/Bitbucket command/image examples likewise require the target project.

## Independent failure-propagation repair

A fresh-context evaluator received an isolated workflow where a failing test
piped into tee under `sh`, and the only required job printed its dependency
result but always succeeded. The contract required preserving the test command,
job identities and logging, without fixing the deliberately failing application
script or changing hosted policy.

The evaluator changed the test shell to explicit Bash and made the required job
reject every result except success. Only the workflow changed. Actionlint
passed; local success, failure and skipped-result checks passed.

Integration reproduced the critical distinction using actual shell invocations:

- Original `sh -e`: producer exit 7 was hidden; pipeline exit was 0.
- Runner-equivalent Bash with `-e -o pipefail`: pipeline exit was 7.
- Required gate: success exited 0; failure, skipped and cancelled exited 1.

This proves shell failure propagation and gate-command behavior, not execution
of GitHub's scheduler. Guidance now explicitly distinguishes an observation job
from a required-check aggregator and requires testing the runner's shell flags.
The original test script and contract remain byte-identical.

Raw report: `/tmp/ci-forward-result.md`. Output:
`/tmp/ci-forward-output.cJooB2`. The command checks and inputs stayed outside
the repository; no deployment credentials or hosted settings were touched.

## Validation and limits

Actionlint 1.7.12 passes the actual extracted GitHub example and repaired
fixture. Both skill validators, strict Markdown, local links, metadata and YAML
example parsing pass. Actionlint does not execute referenced project scripts or
prove provider authorization. No warnings or errors were suppressed.

Hosted fork/merge-queue scheduling, OIDC exchanges, deployment approvals,
artifact upload/download, GitLab merged-config simulation and Bitbucket runner
execution remain untested. The linked provider contracts and conditional
examples are not represented as a deployed, fully executable starter project.
