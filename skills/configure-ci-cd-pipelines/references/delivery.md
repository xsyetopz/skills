# Delivery across providers

Rules for every provider: why a job did not run, building once,
provenance, caching, and secrets. Provider syntax is in
[GitHub Actions](github-actions.md) and
[GitLab and Bitbucket](gitlab-and-bitbucket.md).

## Contents

- Selection before execution
- Build once, promote the same artifact
- Provenance and SBOM
- Cache keys and cache trust
- Secrets reach only the job that needs them
- Local reproduction of a failing step

## Selection before execution

**Definition.** A missing result has one of four causes, each with a
different fix:

- the pipeline was never created (event, filter, or `workflow:rules`);
- the job was not selected (`if`, `rules`);
- the job was skipped because a dependency failed;
- the job ran and failed.

**Use when.** A required check is "pending" or "missing", or a job did
not run.

**Do not use when.** The job ran and its log shows a command failure;
debug the command.

**Example.** GitHub: a workflow with `paths: [src/**]` is never created
for a docs-only PR, so its required check waits forever. Re-running does
not help. Remove the filter from required workflows, or report through
an aggregator.

The aggregator job in
`assets/examples/github/good/.github/workflows/ci.yml` always runs and
folds each `needs` result into one required status:

```yaml
  all-green:
    if: ${{ always() }}
    needs: [test, pr-title]
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - name: Require success or an intended skip
        env:
          TEST: ${{ needs.test.result }}
          TITLE: ${{ needs.pr-title.result }}
          EVENT: ${{ github.event_name }}
        run: ./ci/all-green.sh "$EVENT" "$TEST" "$TITLE"
```

**Cost removed.** Re-running pipelines that will never be created.

**Verify.**

1. The report names which of the four causes applied, with evidence:
   the run list, the rules evaluation, or the `needs` result.

## Build once, promote the same artifact

**Definition.** Build the release artifact once, record its digest,
source SHA, and producer run, and deploy those same bytes to every
environment. Never rebuild for production.

**Use when.** Any pipeline deploys.

**Do not use when.** Environments need different builds, such as debug
builds. Each build is then its own artifact with its own tests.

**Example.** GitLab `deploy` takes `dist/*.whl` from the `build` job
through `needs`. Bitbucket's deploy step uses the same run's `dist/**`
artifact.

From `assets/examples/gitlab/.gitlab-ci.yml`:

```yaml
deploy:
  stage: deploy
  needs: [build, test]
  id_tokens:
    CLOUD_ID_TOKEN:
      aud: https://cloud.example.test
  environment:
    name: production
  resource_group: production
  interruptible: false
  script:
    - ./ci/deploy.sh dist/*.whl
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      when: manual
      allow_failure: false
```

From `assets/examples/bitbucket/bitbucket-pipelines.yml`, the shared
build step declares the artifact:

```yaml
    - step: &build-and-test
        name: Build and test
        script:
          - python -m pip wheel --no-deps -w dist .
          - python -m pip install dist/*.whl
          - python -m unittest discover -s tests
        artifacts:
          - dist/**
```

The deploy step in the same file deploys that wheel without
rebuilding:

```yaml
      - step:
          name: Deploy tested wheel
          deployment: production
          trigger: manual
          oidc: true
          script:
            - ./ci/deploy.sh dist/*.whl
```

**Cost removed.** Deploying untested bytes; a rebuild can pick up new
dependency versions.

**Verify.**

1. The deploy log prints the artifact digest
   (`sha256sum dist/*.whl`), and it equals the digest in the test job's
   log.

## Provenance and SBOM

**Definition.** Provenance states which builder produced an artifact
from which source ([SLSA provenance][slsa]). An SBOM lists its
components in SPDX or CycloneDX format. Neither proves the artifact is
free of vulnerabilities, and a signature alone does not prove who built
it.

**Use when.** The delivery contract requires attestations, such as those
GitHub's `actions/attest-build-provenance` produces
([artifact attestations][attest]).

**Do not use when.** Never invent a custom signed JSON format; use the
provider's attestation tooling.

**Example.** Consumers verify the downloaded artifact against the
repository that built it:

```sh
gh attestation verify "$FILE" --repo "$OWNER/$REPO"
```

Not runnable here: it needs an artifact with a published GitHub
attestation and network access.

**Cost removed.** Artifacts from unknown builders reaching production.

**Verify.**

1. The consumer checks the digest and the builder identity, not only
   that a signature exists.

## Cache keys and cache trust

**Definition.** A cache speeds a job up and never replaces a check. The
key includes everything that changes the cached content: OS,
architecture, tool version, and lockfile hash.

**Use when.** Measured dependency downloads dominate job time.

**Do not use when.** A privileged job could read an entry written by an
untrusted run (a fork PR). GitHub warns that `pull_request_target` can
lead to cache poisoning.

**Example.** GitHub, the `with:` block of an `actions/cache` step
(pin the action to a full SHA, as
`assets/examples/github/good/.github/workflows/ci.yml` does):

```yaml
with:
  path: ~/.cache/pip
  key: pip-${{ runner.os }}-${{ hashFiles('requirements.lock') }}
```

**Cost removed.** Stale dependencies after a lockfile change, and
poisoned caches.

**Verify.**

1. After a lockfile change, the next run logs a cache miss.

## Secrets reach only the job that needs them

**Definition.** Every command in a job can read the secrets that job
receives; masking hides them from logs, not from code. Scope secrets to
the deploy job or environment, never to jobs that run PR code.

**Use when.** Wiring any secret or cloud credential.

**Do not use when.** No exception.

**Example.** GitHub: `id-token: write` only on `deploy`. GitLab:
`id_tokens` only on `deploy`. Bitbucket: `oidc: true` only on the
deployment step.

From `assets/examples/github/good/.github/workflows/ci.yml`, the
workflow default is `contents: read`, and only `deploy` widens it:

```yaml
    permissions:
      contents: read
      id-token: write
```

From `assets/examples/gitlab/.gitlab-ci.yml`, inside `deploy`:

```yaml
  id_tokens:
    CLOUD_ID_TOKEN:
      aud: https://cloud.example.test
```

From `assets/examples/bitbucket/bitbucket-pipelines.yml`:

```yaml
      - step:
          name: Deploy tested wheel
          deployment: production
          trigger: manual
          oidc: true
```

Measured: the Verify command printed one hit per file, all in deploy
jobs: `.gitlab-ci.yml:44`, `bitbucket-pipelines.yml:28`, and
`ci.yml:69`.

**Cost removed.** Secret exfiltration through a test dependency or a PR.

**Verify.**

1. Every hit of
   `rg -n 'secrets\.|id-token|id_tokens|oidc:' <pipeline files>` is in a
   deploy job.

## Local reproduction of a failing step

**Definition.** Run the failing step's exact command locally with the
runner's shell flags, image, and working directory. On GitHub,
`shell: bash` runs `bash --noprofile --norc -eo pipefail`.

**Use when.** A step fails in CI but passes locally.

**Do not use when.** The failure depends on hosted state: secrets,
permissions, or the runner's network.

**Example.**

```sh
docker run --rm -v "$PWD:/src" -w /src python:3.14-slim \
  bash --noprofile --norc -eo pipefail -c './ci/test.sh 3.14 | tee log'
```

**Cost removed.** Guessing at environment differences.

**Verify.**

1. The local run reproduces the CI exit status, or the report names the
   difference found (image, shell, or working directory).

[slsa]: https://slsa.dev/spec/v1.2/provenance
[attest]: https://docs.github.com/en/actions/concepts/security/artifact-attestations
