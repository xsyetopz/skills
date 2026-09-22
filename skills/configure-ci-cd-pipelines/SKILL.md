---
name: configure-ci-cd-pipelines
description: >-
  Use when creating or repairing GitHub Actions, GitLab CI, or Bitbucket
  Pipelines jobs for builds, tests, packaging, releases, or deployment. Preserve
  native events, permissions, and controls. Not for local commands alone or
  changing repository approval policy.
---

# Configure CI/CD Pipelines

Implement provider-native automation that executes the project's established
build, test, packaging, release, or deployment commands with explicit trust
boundaries, immutable artifact identity, least privilege, and auditable failure
propagation.

## Operating contract

- Preserve the selected provider and repository policy. Do not introduce a
  cross-provider abstraction or new deployment system unless requested.
- Treat pull-request content, fork code, generated metadata, caches, and
  artifacts as untrusted until their producer, revision, and integrity are
  established.
- Use least-privilege job and token permissions. A later privileged job must not
  execute untrusted code or consume unauthenticated instructions from an earlier
  job.
- Pin or otherwise govern third-party actions/images/includes according to
  repository policy; tags alone may move.
- Deployment, release publication, environment approval, and secret access
  remain separate authorized operations.

## Pipeline execution contract

- Treat the user goal, scope, approval boundary, and required evidence as
  controlling. This skill narrows how to produce a CI/CD workflow change; it
  MUST NOT broaden authority or override repository instructions.
- For GPT-5.6 and GPT-6, provide provider events, trust boundaries, permissions,
  artifacts, and deployment controls, hard constraints, available tools, and the
  finish condition once. Remove repeated directions and examples unless a
  recorded evaluation shows that they prevent a real failure.
- Infer routine, reversible steps from inspected evidence. Ask only when an
  unresolved choice changes an external contract. Stop before an external write,
  destructive action, credential use, or material scope expansion that the user
  did not authorize.
- Load a linked reference only when its subject affects the current decision.
  Use scripts for deterministic mechanics; use model judgment for semantic
  decisions. Inspect tool output before relying on it.
- Validate at the boundary of the claim with provider lint, fork-path tests,
  artifact identity, and deployment dry runs. Report commands, observed results,
  and gaps. A parser, build, or single green test proves only the property that
  it can discriminate.
- Use **MUST** only for an absolute safety or interoperability requirement,
  **SHOULD** for a default with valid exceptions, and **MAY** for an option.
  Write short active sentences and use one stable term for each concept. This
  style is STE-inspired; it is not a claim of formal ASD-STE100 conformance.

## Workflow

```mermaid
flowchart LR
    E[Provider event] --> T{Trust class}
    T -->|Untrusted change| B[Build and test without secrets]
    T -->|Trusted branch/tag| V[Verify revision and policy]
    B --> A[Produce immutable artifact + provenance]
    V --> A
    A --> G{Approval / environment gate}
    G -->|Authorized| D[Deploy or publish exact artifact]
    G -->|Not authorized| R[Retain verification result only]
```

## Procedure

1. Inspect the existing provider files, reusable workflows/includes, project
   commands, runner requirements, protected environments, secrets, permissions,
   and artifact consumers. Identify the exact event and trust class.
1. Define the job graph before editing: inputs, outputs, dependencies,
   concurrency/cancellation behavior, revision identity, artifact identity, and
   failure propagation. Use provider-native needs/dependencies rather than
   hidden ordering by job names.
1. Implement the smallest provider-native change. Reuse project scripts instead
   of duplicating build logic in YAML. Quote shell inputs, avoid evaluating
   branch or issue text as code, and prevent secrets from reaching untrusted
   jobs or logs.
1. Make caches performance-only. Keys must include material dependency/tool
   inputs; cache misses must not change correctness. Artifacts used across jobs
   or deployment must be immutable, scoped, and associated with the verified
   source revision.
1. Separate verification from release/deployment. Use OIDC or the repository's
   approved short-lived credential mechanism where available. Preserve
   environment approvals, branch/ruleset controls, and manual promotion
   boundaries.
1. Validate syntax with the provider or established linter, inspect resolved
   conditions and permissions, and run the narrowest available test. For changed
   trust paths, test both authorized and unauthorized events.
1. Inspect the final job graph and package contents. Report provider-side checks
   not executed, especially protected-environment approval, hosted runner
   behavior, cloud identity exchange, or actual deployment.

## Choose the provider and trust reference

| Situation | Read or use |
| --- | --- |
| Implementing GitHub Actions events, permissions, artifacts, OIDC, or reusable workflows | [GitHub Actions](references/github-actions.md) |
| Implementing GitLab CI workflow rules, needs, artifacts, includes, or ID tokens | [GitLab CI](references/gitlab-ci.md) |
| Implementing Bitbucket Pipelines start conditions, artifacts, OIDC, or steps | [Bitbucket Pipelines](references/bitbucket-pipelines.md) |
| Reasoning about provider event and job behavior | [Provider behavior](references/provider-behavior.md) |
| Reviewing fork, token, artifact, cache, and deployment hazards | [Provider hazards](references/provider-hazards.md) |
| Choosing a trust and promotion design | [Operational decisions](references/delivery-pipeline-operational-decisions.md) |
| Using complete provider examples | [Worked scenarios](references/delivery-pipeline-worked-scenarios.md) |
| Matching claims to syntax, runner, and deployment evidence | [Verification and claim evidence](references/delivery-pipeline-verification-and-claim-evidence.md) |
| Checking current provider documentation | [Standards, APIs, and authorities](references/delivery-pipeline-standards-apis-and-authorities.md) |

## Delivery-control references

Read only the reference whose subject affects the current task.

| Reference | Use when |
| --- | --- |
| [Concepts, contracts, and invariants](references/delivery-pipeline-concepts-contracts-and-invariants.md) | Use when distinguishing the requested CI/CD workflow change from observed repository state. |
| [Enterprise operation and governance](references/delivery-pipeline-organizational-controls-and-scale.md) | Use when the CI/CD workflow change crosses ownership, data-handling, release, or audit boundaries. |
| [Failure modes and recovery](references/delivery-pipeline-failure-patterns-and-recovery.md) | Preserve the first useful error and the state that produced it. |
| [Bundled resource map](references/delivery-pipeline-bundled-resource-map.md) | Locate and apply complete native templates without treating them as universal defaults. |

## Behavioral evaluation

Run [the maintained Agent Skills evaluations](evals/evals.json) in clean
target-client contexts. Compare this revision with a no-skill or prior-skill
baseline. Review commands, diffs, and artifacts; do not grade prose alone. The
checked-in cases are test inputs, not claimed results.

## Bundled executable helpers

- No bundled script is mandatory. Use the target repository's established tools.

Run a helper only for the contract it documents. Inspect arguments and output; a
zero exit status proves only the checks implemented by that helper.

## Bundled output material

- `assets/github-actions/ci.reference.yml`
- `assets/gitlab/ci.reference.yml`
- `assets/bitbucket/bitbucket-pipelines.reference.yml`

Copy or adapt assets into the target workspace. Do not edit the installed skill
as a substitute for changing the requested repository.

## Completion evidence

- Updated provider configuration and any strictly necessary project script
  changes.
- Explicit event, trust, permission, artifact, and promotion model.
- Syntax/lint results and any provider-side run identifiers actually observed.
- Artifact/revision identity and deployment/publish boundary.
- Unexecuted hosted, secret, approval, or deployment checks.

## Stop or escalate

- The requested deployment target, environment, credential authority, or
  approval owner is materially undefined.
- The only available design would expose secrets or privileged tokens to
  untrusted code.
- A provider or repository policy blocks the requested operation and changing
  that policy was not authorized.
- The pipeline would need to publish or deploy when only verification was
  requested.

Do not claim completion while a required check is failed, unattempted, or
unavailable. State the exact evidence and the remaining boundary instead of
promoting a narrower result into a broader claim.
