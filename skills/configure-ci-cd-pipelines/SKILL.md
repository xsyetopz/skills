---
name: configure-ci-cd-pipelines
description: >-
  Writes, reviews, and debugs GitHub Actions, GitLab CI, and Bitbucket
  Pipelines: triggers, token permissions, script injection, pinned actions,
  required checks, deploys. Use when editing pipeline YAML or when CI
  misbehaves. Not for local build scripts.
---

# Configure CI/CD Pipelines

Change a pipeline so that it runs the right commit with the least
privilege. Required checks must fail when their jobs fail, and deploys
must use the artifact that was tested.

## Workflow

1. Read the existing pipeline files, the repository's build and test
   commands, and the branch protection or required checks if they are
   visible. Name the provider and, for GitHub Enterprise Server, its
   version.
1. Write down, for the change:
   - which events and refs run it, and which commit each one tests
     ([events][events]);
   - which jobs need which permissions and secrets;
   - which result gates the merge.
1. Edit, using the cards for:
   - workflow-level `permissions: contents: read`;
   - event data through `env:`;
   - actions pinned by SHA, with a version comment;
   - `persist-credentials: false`;
   - `shell: bash` for any pipe;
   - an aggregator for required checks;
   - `timeout-minutes` on every job;
   - OIDC only in the deploy job.
1. Run the linters: `actionlint`,
   `python3 scripts/check_action_pins.py .github`,
   `uvx zizmor@1.30.1 --offline .github/workflows`. For GitLab and
   Bitbucket, run `uvx check-jsonschema@0.38.2 --builtin-schema
   vendor.gitlab-ci|vendor.bitbucket-pipelines FILE`.
1. Run changed scripts locally with the runner's shell flags
   ([local reproduction][local]).
1. Report the lint output, the local runs, and what only a hosted run
   can show: secrets, approvals, required checks, and runner
   availability.

## Route the task to a card

| Task or symptom | Card |
| --- | --- |
| Required check stuck pending | [Events][events], [selection before execution][selection] |
| Fork PRs need labels or comments | [pull_request_target][prt] |
| Token can push or publish from tests | [Permissions][perms] |
| PR title or branch name in `run:` | [Injection][injection] |
| `uses: x@v1` | [Pinning][pinning] |
| Step green although tests failed | [Shell and pipefail][pipefail] |
| Many matrix jobs as required checks | [Aggregator][aggregator] |
| Superseded runs or overlapping deploys | [Concurrency][concurrency], [GitLab interruptible][gl-int] |
| Build output missing in the next job | [Artifacts][artifacts], [GitLab needs][gl-needs], [Bitbucket steps][bb-steps] |
| Cloud deploy credentials | [GitHub OIDC][oidc], [GitLab id_tokens][gl-deploy], [Bitbucket OIDC][bb-deploy] |
| Duplicate GitLab pipelines | [Workflow rules][gl-rules] |
| Manual job does not block | [allow_failure][gl-manual] |
| Branch not running in Bitbucket | [Start conditions][bb-start] |
| Deploy rebuilds the code | [Build once][build-once] |
| Attestations or SBOM requested | [Provenance][provenance] |
| Slow dependency installs | [Cache keys][cache] |

## Rules

- Never run PR code in a job that has secrets or write tokens:
  `pull_request_target`, `workflow_run`, or a protected-variable job.
- Pass attacker-controlled values through `env:` and quoted variables,
  never through `${{ }}` inside `run:`.
- Pin third-party actions to a commit SHA with a `# vX.Y.Z` comment,
  and check the comment with `check_action_pins.py --resolve`.
- Make workflow permissions read-only. Grant write or `id-token` scopes
  only to the job that needs them.
- Do not use `continue-on-error`, `allow_failure: true`, `|| true`, or
  a pipe without pipefail on a required check.
- A required-check aggregator fails on `failure`, `cancelled`, and
  unexpected `skipped`.
- Deploy the tested artifact, identified by its digest. Never rebuild
  for production.

## Bundled tools

- `scripts/check_action_pins.py PATH... [--resolve]` reports
  `uses:` references that are not SHA-pinned. `--resolve` checks
  version comments against `gh api`. `test_check_action_pins.py` holds
  its tests.
- `assets/examples/github/good/` is the reference workflow, with
  `ci/all-green.sh`, `ci/test.sh`, and `ci/deploy.sh`.
  `github/bad/` has one of each defect.
- `assets/examples/gitlab/.gitlab-ci.yml` and
  `bitbucket/bitbucket-pipelines.yml`, plus a deliberately broken
  variant of each.
- `sh assets/examples/verify.sh [network]` checks the reference
  workflows. Offline, it runs actionlint 1.7.12, the pin checker, the
  aggregator truth table, and the runner's shell flags. `network` adds
  zizmor 1.30.1, check-jsonschema 0.38.2, and SHA resolution with `gh`.

## References

- [GitHub Actions](references/github-actions.md)
- [GitLab CI and Bitbucket Pipelines](references/gitlab-and-bitbucket.md)
- [Delivery across providers](references/delivery.md)

## Completion evidence

- The changed files, with lint output: actionlint, the pin checker,
  zizmor, or check-jsonschema.
- The event-to-commit and job-to-permission table for the change.
- Local runs of changed scripts with the runner's shell flags, and the
  aggregator truth table if it changed.
- A list of what needs a hosted run, each marked not run: required
  checks, secrets, approvals, and OIDC trust. Linters and local runs do
  not verify hosted behavior.

## Stop and ask

- The change needs secrets or write permissions in a job that runs PR
  code.
- Branch protection or required-check names must change, and you
  cannot see the settings.
- The provider is GitHub Enterprise Server, where the v4+ artifact
  actions are not supported, and the server version is unknown.

[events]: references/github-actions.md#event-selection-and-the-tested-commit
[prt]: references/github-actions.md#pull_request_target-and-workflow_run
[perms]: references/github-actions.md#least-privilege-token-permissions
[injection]: references/github-actions.md#expression-injection
[pinning]: references/github-actions.md#action-pinning-to-commit-shas
[pipefail]: references/github-actions.md#runner-shell-and-pipefail
[aggregator]: references/github-actions.md#required-check-aggregator
[concurrency]: references/github-actions.md#concurrency-groups
[artifacts]: references/github-actions.md#artifacts-between-jobs
[oidc]: references/github-actions.md#oidc-deployment-job
[gl-rules]: references/gitlab-and-bitbucket.md#gitlab-one-pipeline-per-change-with-workflow-rules
[gl-needs]: references/gitlab-and-bitbucket.md#gitlab-needs-and-artifacts
[gl-manual]: references/gitlab-and-bitbucket.md#gitlab-manual-jobs-and-allow_failure
[gl-deploy]: references/gitlab-and-bitbucket.md#gitlab-deployment-with-id_tokens-and-resource_group
[gl-int]: references/gitlab-and-bitbucket.md#gitlab-interruptible-and-auto-cancel
[bb-start]: references/gitlab-and-bitbucket.md#bitbucket-start-conditions
[bb-steps]: references/gitlab-and-bitbucket.md#bitbucket-step-isolation-artifacts-and-anchors
[bb-deploy]: references/gitlab-and-bitbucket.md#bitbucket-manual-oidc-deployment
[selection]: references/delivery.md#selection-before-execution
[build-once]: references/delivery.md#build-once-promote-the-same-artifact
[provenance]: references/delivery.md#provenance-and-sbom
[cache]: references/delivery.md#cache-keys-and-cache-trust
[local]: references/delivery.md#local-reproduction-of-a-failing-step
