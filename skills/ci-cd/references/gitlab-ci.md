# GitLab pipeline creation, DAGs and deployment

Research: 2026-09-09; current GitLab CI YAML. Replace example script paths and
configure a compatible build image.

## Avoid duplicate branch and MR pipelines

```yaml
workflow:
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
    - if:
        '$CI_COMMIT_BRANCH && $CI_OPEN_MERGE_REQUESTS && $CI_PIPELINE_SOURCE ==
        "push"'
      when: never
    - if: "$CI_COMMIT_BRANCH"
    - if: "$CI_COMMIT_TAG"

build:
  stage: build
  script:
    - ./scripts/build
  artifacts:
    paths: [dist/]
    expire_in: 1 week

verify:
  stage: test
  needs:
    - job: build
      artifacts: true
  script:
    - ./scripts/verify-built-output
```

`workflow:rules` decides whether a pipeline exists; job `rules` selects jobs
within it. Rules use first-match behavior. Scope the duplicate suppression to
push so scheduled/triggered pipelines are not accidentally blocked. Define
image/runtime through the project's existing defaults. [Workflow rules][ref-1].

## Status and artifact edges

Stages impose order by default; `needs` builds a DAG and can start earlier. With
`needs`, artifact downloads come from selected needed jobs. A required need
referencing an omitted job can fail pipeline creation; use `optional:true` only
if absence is valid and the consumer handles it. Avoid mixing `dependencies` and
`needs` without a documented reason. `artifacts:reports` enables parsable
test/coverage reporting; keep report paths and actual file generation
consistent. [YAML reference](https://docs.gitlab.com/ci/yaml/), [job
artifacts][ref-2].

`when:always` can retain diagnostic artifacts after failure.
`allow_failure:true` changes pipeline success semantics and must not be used to
conceal a required check. A manual job's blocking behavior depends on how it is
declared, including rules; make the intended `allow_failure` explicit when its
effect matters.

## Includes and downstream pipelines

Includes can load local, project, remote or template configuration. Pin
external/project includes to immutable revisions. Inspect the merged
configuration with CI Lint. A child pipeline consumes its own configuration and
does not automatically inherit every artifact or variable. Select an explicit
downstream status strategy (`mirror` on supporting servers, or the compatible
project convention) when parent success must reflect downstream completion.
Check protected-variable availability against refs, project settings, and MR
context.

## Credentials and deployment

An OIDC job declares an audience-specific token:

```yaml
deploy:
  stage: deploy
  id_tokens:
    CLOUD_ID_TOKEN:
      aud: https://cloud.example.test
  environment:
    name: production
  resource_group: production
  script:
    - ./scripts/deploy-tested-artifact
  rules:
    - if: "$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH"
      when: manual
      allow_failure: false
```

Implement provider token exchange and artifact identity verification in the
deployment script. Restrict the role to the relevant project/ref/environment
claims. `resource_group` serializes a shared deployment target; protected
environments and approvals are separately configured controls. Masking a
variable does not make running untrusted code with it safe. [ID tokens][ref-3].

Use CI Lint's merged configuration/pipeline simulation for affected refs, then
repository checks. Check protected variables and environment approvals in the
selected project settings.

[ref-1]: https://docs.gitlab.com/ci/yaml/workflow/
[ref-2]: https://docs.gitlab.com/ci/jobs/job_artifacts/
[ref-3]: https://docs.gitlab.com/ci/secrets/id_token_authentication/
