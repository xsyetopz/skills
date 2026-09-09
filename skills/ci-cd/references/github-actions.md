# GitHub Actions events, jobs and credentials

Research: 2026-09-09; current GitHub Actions documentation. Replace action
placeholders with verified full commit SHAs and scripts with project commands.
`CHECKOUT_REF` and `UPLOAD_REF` are explicit placeholders, not installable
action versions.

## Event semantics

`pull_request` commonly tests a synthetic merge ref; its head SHA identifies the
contributor revision. `push` runs for pushed refs. `pull_request_target` runs in
the base repository's context and can have privileged credentials: never combine
it with executing contributor code. `workflow_dispatch` requires an eligible
workflow on the default branch; `schedule` runs from the default branch and can
be delayed. Add `merge_group` when required checks must run in a merge queue.
Branch/path filters can prevent an entire workflow, leaving a required check
pending. [Events][ref-1].

## Dependencies and artifacts

```yaml
name: verify
on:
  pull_request:
  push:
    branches: [main]
permissions:
  contents: read
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@CHECKOUT_REF
      - run: ./scripts/build-and-test
      - uses: actions/upload-artifact@UPLOAD_REF
        with:
          name: build-${{ github.sha }}
          path: dist/
          if-no-files-found: error
  report:
    needs: build
    if: ${{ always() && !cancelled() }}
    runs-on: ubuntu-latest
    steps:
      - env:
          BUILD_RESULT: ${{ needs.build.result }}
        run: printf '%s\n' "$BUILD_RESULT"
```

The report job observes failure/skips without changing build's outcome. A normal
`needs` consumer runs only after successful dependencies unless its condition
changes that behavior. Define step IDs and job `outputs` when passing small
values through `$GITHUB_OUTPUT`; artifacts carry files across jobs. Matrix
producers need unique artifact names and explicit aggregation. Fail consumers
when required artifacts are absent. [Workflow syntax][ref-2],
[artifacts][ref-3].

## Reuse and trust

Reusable workflows use `workflow_call`; declare typed inputs, outputs and
secrets and call them at job level. Keep reusable-workflow token permissions
within the caller’s grants. Prefer explicit secret mapping over inheriting
unrelated secrets. `workflow_run` can grant privileges despite an unprivileged
upstream run; validate the source run and artifact before privileged
consumption.

Keep shell source literal: put `${{ github.event.pull_request.title }}` in an
environment value, then quote its shell expansion. Set
`persist-credentials: false` for checkout jobs that do not push. Pin actions to
verified full commit SHAs. Check runner requirements when updating actions.
[Secure use][ref-4].

## Deployment and cancellation

Use job `environment` for the intended deployment target and its existing
approvals. Grant `id-token: write` only to the job exchanging OIDC tokens; this
permission alone grants no cloud role. Restrict the cloud trust policy to the
repository, ref/environment and audience. [OIDC][ref-5].

Set concurrency groups according to resource ownership: canceling outdated PR
checks is often useful, while canceling a production deployment mid-migration
can leave partial state. Define an explicit final status job only when
required-check policy needs aggregation, and make it fail when any required
dependency failed. Verify fork PR, branch push, tag/dispatch and cancellation
paths affected by the edit; a local command pass cannot prove those hosted
transitions.

[ref-1]:
  https://docs.github.com/en/actions/reference/events-that-trigger-workflows
[ref-2]:
  https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
[ref-3]:
  https://docs.github.com/en/actions/using-workflows/storing-workflow-data-as-artifacts
[ref-4]:
  https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions
[ref-5]:
  https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/about-security-hardening-with-openid-connect
