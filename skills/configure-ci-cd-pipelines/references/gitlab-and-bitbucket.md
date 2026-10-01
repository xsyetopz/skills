# GitLab CI and Bitbucket Pipelines

Facts from the [GitLab CI YAML reference][gl-yaml] (fetched 2026-09-25) and the linked Atlassian
pages. No pipeline ran on either service. Validate with
`check-jsonschema --builtin-schema vendor.gitlab-ci FILE` or `vendor.bitbucket-pipelines FILE`.

## Contents

- [GitLab: duplicate pipelines](#gitlab-duplicate-pipelines)
- [GitLab: needs, manual jobs, deploys](#gitlab-needs-manual-jobs-deploys)
- [Bitbucket: start conditions](#bitbucket-start-conditions)
- [Bitbucket: steps, artifacts, deploys](#bitbucket-steps-artifacts-deploys)

## GitLab: duplicate pipelines

`workflow:rules` decides whether a pipeline is created; job `rules` pick jobs inside it. The first
matching `if` wins. Without workflow rules, a push to a branch with an open MR creates two
pipelines. Never copy the `when: never` rule without its `$CI_PIPELINE_SOURCE == "push"` condition,
or it also blocks scheduled and triggered pipelines.

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

## GitLab: needs, manual jobs, deploys

- `needs` starts a job when its needed jobs finish and downloads artifacts only from them when
  `artifacts: true` (a misspelled `artifact` fails the schema). A `needs` entry naming a job absent
  from the pipeline fails pipeline creation unless `optional: true`; do not set it just to silence
  that, because the consumer then gets no artifact.
- `allow_failure` defaults to `true` for manual jobs, so an unstarted manual deploy does not block
  the pipeline. Inside `rules`, `when: manual` switches the default to `false`. Set it explicitly.
- `interruptible: true` only has effect when "auto-cancel redundant pipelines" is on. Set it in
  `default:` for build and test jobs and `false` for deploys.
- `id_tokens` gives an OIDC JWT for the audience you name ([ID tokens][gl-oidc]); `resource_group`
  serializes deploys. Protected environments and approvals are project settings, not YAML. Never
  store long-lived cloud keys in variables: masking hides them from logs, not from jobs.

```yaml
deploy:
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

## Bitbucket: start conditions

`pipelines:` sections: `default` (pushes no branch section matches), `branches`, `tags`,
`pull-requests` (glob keys), and `custom` (manual or scheduled). A PR pipeline merges the
destination branch first ([start conditions][bb-start]). `*` does not match `/`, so `feature/x`
never runs under `*`; use `**`.

```yaml
pipelines:
  pull-requests:
    "**":
      - step: *build-and-test
  branches:
    main:
      - step: *build-and-test
```

## Bitbucket: steps, artifacts, deploys

- Each step runs in a fresh container. Only paths listed under `artifacts` (relative to the clone
  directory) reach later steps ([artifacts][bb-artifacts]); `export`ed variables do not.
- Put the deploy step in `branches: main`, never in `pull-requests`: `deployment: production`,
  `trigger: manual`, `oidc: true` ([OIDC][bb-oidc]), and the deploy input (`dist/*.whl`) listed in
  the producing step's `artifacts`. Restrict workspace, repository, and environment claims in the
  cloud trust policy.

```yaml
definitions:
  steps:
    - step: &build-and-test
        name: Build and test
        script:
          - python -m unittest discover -s tests
        artifacts:
          - dist/**
```

[gl-yaml]: https://docs.gitlab.com/ci/yaml/
[gl-oidc]: https://docs.gitlab.com/ci/secrets/id_token_authentication/
[bb-start]: https://support.atlassian.com/bitbucket-cloud/docs/pipeline-start-conditions/
[bb-artifacts]: https://support.atlassian.com/bitbucket-cloud/docs/use-artifacts-in-steps/
[bb-oidc]: https://support.atlassian.com/bitbucket-cloud/docs/integrate-pipelines-with-resource-servers-using-oidc/
