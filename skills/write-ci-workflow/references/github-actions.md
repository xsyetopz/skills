# GitHub Actions

Facts from GitHub's [workflow syntax][syntax], [events][events], and [secure use][secure] pages,
fetched 2026-09-25. No workflow was run.

## Contents

- [Which Commit Each Event Tests](#which-commit-each-event-tests)
- [pull_request_target and workflow_run](#pull_request_target-and-workflow_run)
- [Shell and pipefail](#shell-and-pipefail)
- [Required-Check Aggregator](#required-check-aggregator)
- [OIDC Deploy Job](#oidc-deploy-job)
- [Artifacts and Job Outputs](#artifacts-and-job-outputs)

## Which Commit Each Event Tests

- `pull_request` runs the merge commit of the PR with its base (`GITHUB_SHA`). The PR head is
  `github.event.pull_request.head.sha`.
- `push` runs the pushed ref. `merge_group` runs the merge-queue commit.
- `schedule` and `workflow_dispatch` use the workflow on the default branch.

```yaml
on:
  pull_request:
  push:
    branches: [main]
  merge_group:
```

A required check stuck at "Expected - Waiting" means the workflow was never created: check the
event, `paths`/`branches` filters, and whether the check name matches the job name.

## pull_request_target and workflow_run

These run in the context of the base repository with its token and secrets. GitHub warns that
untrusted code there can poison caches and leak write access. `actions/checkout` v7 refuses fork PR
code on these events unless `allow-unsafe-pr-checkout: true`; do not set it. Use these events only
to label or comment, never to build or test the PR.

```yaml
# defect: PR head checked out with base-repo secrets
on:
  pull_request_target:
steps:
  - uses: actions/checkout@v7
    with:
      ref: ${{ github.event.pull_request.head.sha }}
```

To act on results of untrusted code, run it under `pull_request`, upload an artifact, and let a
separate `workflow_run` job read it as data only.

## Shell and pipefail

| Invocation | `false \| tee /dev/null` |
| --- | --- |
| `shell: bash` = `bash --noprofile --norc -eo pipefail {0}` | exit 1 |
| no `shell:` = `bash -e {0}` | exit 0 |
| `shell: sh` = `sh -e {0}` | exit 0 |

If the image has no bash, write `set -o pipefail` first (if the shell supports it) or avoid pipes.

## Required-Check Aggregator

```yaml
all-green:
  if: ${{ always() }}
  needs: [test, pr-title]
  runs-on: ubuntu-latest
  timeout-minutes: 5
  steps:
    - env:
        TEST: ${{ needs.test.result }}
        TITLE: ${{ needs.pr-title.result }}
        EVENT: ${{ github.event_name }}
      run: |
        [ "$TEST" = success ] || { echo "test: $TEST"; exit 1; }
        if [ "$EVENT" = pull_request ]; then want=success; else want=skipped; fi
        [ "$TITLE" = "$want" ] || { echo "pr-title: $TITLE"; exit 1; }
```

Branch protection then requires only `all-green`. Check the settings; a workflow cannot show them.

## OIDC Deploy Job

```yaml
deploy:
  needs: [all-green]
  if: ${{ github.ref == 'refs/heads/main' }}
  environment: production
  permissions:
    contents: read
    id-token: write
  runs-on: ubuntu-latest
  timeout-minutes: 20
  steps:
    - run: ./ci/deploy.sh
```

`environment` also applies its approval rules. The cloud role's trust condition should name
`repo:OWNER/REPO:environment:production` (or the ref) and the audience ([OIDC hardening][oidc]).
Replace long-lived cloud keys in secrets with this.

## Artifacts and Job Outputs

```yaml
- uses: actions/upload-artifact@<SHA> # vX.Y.Z
  if: ${{ always() }}
  with:
    name: test-log-${{ matrix.python }}
    path: test-${{ matrix.python }}.log
    if-no-files-found: error
```

Pass small values between jobs through `outputs` and `$GITHUB_OUTPUT`, not artifacts. When bumping a
pin, read the release notes for runner requirements: checkout v5 and later use node24 and need
runner v2.327.1 or later.

[syntax]: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
[events]: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
[secure]: https://docs.github.com/en/actions/reference/security/secure-use
[oidc]: https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/about-security-hardening-with-openid-connect
