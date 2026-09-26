# GitLab CI and Bitbucket Pipelines

Cards for `.gitlab-ci.yml` and `bitbucket-pipelines.yml`. Facts come
from the [GitLab CI YAML reference][gl-yaml] (fetched 2026-09-25) and
the Atlassian Bitbucket Pipelines pages linked per card. Examples are in
`assets/examples/gitlab/` and `bitbucket/`; `verify.sh network`
validates them with the vendored schemas of `check-jsonschema` 0.38.2.
No pipeline ran on either service.

## Contents

- GitLab: one pipeline per change with workflow rules
- GitLab: needs and artifacts
- GitLab: manual jobs and allow_failure
- GitLab: deployment with id_tokens and resource_group
- GitLab: interruptible and auto-cancel
- Bitbucket: start conditions
- Bitbucket: step isolation, artifacts, and anchors
- Bitbucket: manual OIDC deployment
- Schema validation and its limits

## GitLab: one pipeline per change with workflow rules

**Definition.** `workflow:rules` decides whether a pipeline is created
at all; job `rules` pick jobs inside it. Rules evaluate in order, and
the first matching `if` wins.

**Use when.** A project runs both branch and merge request pipelines.
Without rules, a push to a branch with an open MR creates two
pipelines.

**Do not use when.** Never copy the `when: never` rule without its
`$CI_PIPELINE_SOURCE == "push"` condition; without it, the rule also
blocks scheduled and triggered pipelines.

**Example.** From [`.gitlab-ci.yml`][gl-asset]:

```yaml
workflow:
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: >-
        $CI_COMMIT_BRANCH && $CI_OPEN_MERGE_REQUESTS &&
        $CI_PIPELINE_SOURCE == "push"
      when: never
    - if: $CI_COMMIT_BRANCH
    - if: $CI_COMMIT_TAG
```

**Cost removed.** Duplicate pipelines, which double runner minutes and
show two statuses on the MR.

**Verify.**

1. The file passes `check-jsonschema --builtin-schema vendor.gitlab-ci`.
1. GitLab's CI Lint "simulate pipeline" for a push to a branch with an
   open MR shows only the MR pipeline. Not run here; it needs the
   project.

## GitLab: needs and artifacts

**Definition.** Stages run in order by default. `needs` builds a
dependency graph: a job starts as soon as its needed jobs finish and
downloads artifacts only from them (`artifacts: true`). A `needs` entry
naming a job absent from the pipeline fails pipeline creation unless it
sets `optional: true`.

**Use when.** Jobs depend on specific earlier jobs, not whole stages.

**Do not use when.** Never set `optional: true` just to silence the
error; the consumer must then handle a missing artifact.

**Example.**

```yaml
test:
  stage: test
  needs:
    - job: build
      artifacts: true
```

The broken fixture misspells `artifacts` as `artifact`, and the schema
rejects it: `$.test.needs[0] ... is not valid under any of the given
schemas`.

**Cost removed.** Jobs waiting on unrelated stages, and consumers
silently getting no build output.

**Verify.**

1. `verify.sh network` shows the valid file passing and the broken
   `needs` entry failing.

## GitLab: manual jobs and allow_failure

**Definition.** `allow_failure` defaults to `true` for manual jobs, so
an unstarted manual job does not block the pipeline. Inside `rules`,
`when: manual` switches the default to `false`. Set it explicitly
either way.

**Use when.** A deployment needs a click to approve, and the pipeline
must show as blocked until then.

**Do not use when.** Never set `allow_failure: true` on a required
check; its failures turn the pipeline green.

**Example.**

```yaml
rules:
  - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
    when: manual
    allow_failure: false
```

**Cost removed.** Pipelines marked passed although the deployment never
ran or a required job failed.

**Verify.**

1. Each hit of `rg -n 'allow_failure: true' .gitlab-ci.yml` is an
   optional job, and the report says why.

## GitLab: deployment with id_tokens and resource_group

**Definition.**

- `id_tokens` creates an OIDC JWT with the audience you name, for cloud
  federation ([ID tokens][gl-oidc]).
- `environment` tracks deployments.
- `resource_group` lets one job at a time deploy to that target.

Protected environments and approvals are project settings; the YAML
does not create them.

**Use when.** Deploying to a cloud from GitLab CI.

**Do not use when.** Never store long-lived cloud keys in CI variables.
Masking hides a variable from logs, not from the jobs that can read it.

**Example.** The whole job from `assets/examples/gitlab/.gitlab-ci.yml`:

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

**Cost removed.** Parallel deployments to one target, and static
credentials in variables.

**Verify.**

1. The cloud role trusts only this project and the protected branch or
   environment claim. Check it in the cloud console; not run here.

## GitLab: interruptible and auto-cancel

**Definition.** `interruptible: true` lets GitLab's "auto-cancel
redundant pipelines" setting cancel the job when a newer commit starts
a pipeline on the same ref. With that setting off, the keyword does
nothing.

**Use when.** Build and test jobs, set through `default:`.

**Do not use when.** Deploy jobs; set `interruptible: false` there.

**Example.** `default: { interruptible: true }` for all jobs, and
`interruptible: false` on `deploy`. From [`.gitlab-ci.yml`][gl-asset]:

```yaml
default:
  image: python:3.14-slim
  interruptible: true
  timeout: 20 minutes
```

The `deploy` job overrides it with `interruptible: false`, as the
excerpt in "GitLab: deployment with id_tokens and resource_group"
shows.

**Cost removed.** Runner time on superseded commits, without cancelling
deployments.

**Verify.**

1. Project settings show auto-cancel enabled. Not run here.

## Bitbucket: start conditions

**Definition.** `pipelines:` has several start sections:

- `default`: pushes that no branch section matches;
- `branches`, `tags`, `pull-requests`: glob keys;
- `custom`: manual or scheduled runs.

A PR pipeline merges the destination branch in before it runs
([start conditions][bb-start]).

**Use when.** Choosing the section a step goes in.

**Do not use when.** A branch name contains `/`: `*` does not match it;
use `**`, as the example does.

**Example.**

```yaml
pipelines:
  pull-requests:
    "**":
      - step: *build-and-test
  branches:
    main:
      - step: *build-and-test
```

**Cost removed.** Branches such as `feature/x` that never run CI.

**Verify.**

1. Each branch naming pattern in use maps to a named section.

## Bitbucket: step isolation, artifacts, and anchors

**Definition.** Each step runs in a fresh container. Only files listed
under `artifacts`, with paths relative to the clone directory, reach
later steps ([artifacts][bb-artifacts]). YAML anchors under
`definitions: steps:` reuse one step definition.

**Use when.** A later step needs build output, or several sections run
the same step.

**Do not use when.** Passing values through `export`; environment
variables do not survive a step boundary.

**Example.**

```yaml
definitions:
  steps:
    - step: &build-and-test
        name: Build and test
        script:
          - python -m pip wheel --no-deps -w dist .
          - python -m pip install dist/*.whl
          - python -m unittest discover -s tests
        artifacts:
          - dist/**
```

**Cost removed.** Deploy steps that rebuild instead of deploying the
tested wheel.

**Verify.**

1. The deploy step's input path (`dist/*.whl`) is listed under
   `artifacts` in the step that produced it.

## Bitbucket: manual OIDC deployment

**Definition.**

- `deployment: production` binds the step to the environment and its
  variables.
- `trigger: manual` waits for a click.
- `oidc: true` provides an OIDC token for cloud federation
  ([OIDC][bb-oidc]).

**Use when.** Releasing from `main` after the tests pass.

**Do not use when.** Never put the deploy step in `pull-requests`.

**Example.**

```yaml
- step:
    name: Deploy tested wheel
    deployment: production
    trigger: manual
    oidc: true
    script:
      - ./ci/deploy.sh dist/*.whl
```

**Cost removed.** Automatic deployments with static keys.

**Verify.**

1. The cloud trust policy restricts the workspace, repository, and
   deployment environment claims. Not run here.

## Schema validation and its limits

**Definition.** `check-jsonschema --builtin-schema vendor.gitlab-ci` or
`vendor.bitbucket-pipelines` validates a file against the published
JSON Schema. It catches wrong types and unknown values, but not
everything: the vendored Bitbucket schema accepted a step with
`scripts:` instead of `script:`.

**Use when.** Before pushing any pipeline file change, and in the
repository's own CI.

**Do not use when.** Treating a pass as proof that the pipeline runs.
GitLab's CI Lint with pipeline simulation, or a real run, checks
variables, includes, and runners.

**Example.** Executed:

```text
$ uvx check-jsonschema@0.38.2 --builtin-schema vendor.bitbucket-pipelines \
    bitbucket/broken.bitbucket-pipelines.yml
$.options['max-time']: 'thirty' is not of type 'integer'
$ uvx check-jsonschema@0.38.2 \
    --builtin-schema vendor.bitbucket-pipelines typo.yml
ok -- validation done        # step uses `scripts:`: not caught
```

**Cost removed.** Type and key errors caught at push time instead of in
a failed pipeline. The typo case marks what still needs review.

**Verify.**

1. `verify.sh network` asserts both results. If the typo starts failing,
   the schema improved, and the script says so.

[gl-yaml]: https://docs.gitlab.com/ci/yaml/
[gl-oidc]: https://docs.gitlab.com/ci/secrets/id_token_authentication/
[gl-asset]: ../assets/examples/gitlab/.gitlab-ci.yml
[bb-start]: https://support.atlassian.com/bitbucket-cloud/docs/pipeline-start-conditions/
[bb-artifacts]: https://support.atlassian.com/bitbucket-cloud/docs/use-artifacts-in-steps/
[bb-oidc]: https://support.atlassian.com/bitbucket-cloud/docs/integrate-pipelines-with-resource-servers-using-oidc/
