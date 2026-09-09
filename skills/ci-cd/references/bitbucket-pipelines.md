# Bitbucket Cloud steps, artifacts and deployment

Research: 2026-09-09; Bitbucket Cloud Pipelines documentation. No server release
number applies.

## Select the correct start condition

`default` handles pushes without a more specific branch pipeline. `branches`,
`tags`, `pull-requests` and `custom` define different entrypoints; a PR pipeline
can run in addition to a branch pipeline. PR pipeline behavior includes merging
the destination into the working branch before execution, so distinguish the
contributor SHA from tested merge content. Use `custom` for explicitly
selected/scheduled workflows and declared variables. Match glob patterns
carefully: one-level `*` does not express every slash-containing branch. [Start
conditions][ref-1].

```yaml
image: your-existing-build-image
pipelines:
  default:
    - step:
        name: Build
        script:
          - ./scripts/build
        artifacts:
          - dist/**
    - step:
        name: Verify built output
        script:
          - ./scripts/verify-built-output
  custom:
    deploy-production:
      - step:
          name: Deploy approved artifact
          deployment: production
          oidc: true
          script:
            - ./scripts/deploy-approved-artifact
```

The custom deployment requires the existing script to obtain the specific
approved artifact; it does not inherit files from an unrelated default pipeline
automatically.

## Step isolation and parallel work

Each step has its own execution container and environment. Shell exports and
ordinary files do not automatically survive the step. Declare artifacts for
files needed by later steps; paths are relative to the clone directory and must
exist there. Control artifact downloads for consumers that do not need them.
Retention limits mean an old manual deployment may no longer have its build
artifact; rebuild/reapprove under the project's release procedure instead of
silently deploying another revision. [Artifacts][ref-2].

Give parallel steps a common prior artifact. Do not depend on sibling
completion. Configure `fail-fast` according to whether sibling diagnostic work
is useful after failure. Caches are accelerators and may be absent or stale; key
lockfile-dependent caches by the relevant file content. Service containers have
their own memory allocation and network assumptions. Exit-status handling in
`after-script` differs from the main script, so do not place the only required
verification in cleanup. [Step options][ref-3].

## Secrets and deployment boundaries

Repository/workspace/deployment variable scopes differ. Deployment variables
belong to the declared environment, not every step. Secured variables can be
masked in logs but remain readable to code running with them. `oidc:true` makes
the step token available for provider exchange; cloud trust must restrict
workspace/repository/deployment identity and audience. The YAML switch does not
create a cloud role or approve a release. [OIDC][ref-4].

Configure manual controls and environment ordering/permissions for the required
release sequence. Identify the source commit and tested artifact in the
deployment step. Bound execution and report its outcome. Validate both branch
and PR entrypoints when shared definitions change, and check artifact
availability at each boundary. Check deployment permissions in hosted
environment settings. [Configuration reference][ref-5].

[ref-1]:
  https://support.atlassian.com/bitbucket-cloud/docs/pipeline-start-conditions/
[ref-2]:
  https://support.atlassian.com/bitbucket-cloud/docs/use-artifacts-in-steps/
[ref-3]: https://support.atlassian.com/bitbucket-cloud/docs/step-options/
[ref-4]:
  https://support.atlassian.com/bitbucket-cloud/docs/integrate-pipelines-with-resource-servers-using-oidc/
[ref-5]:
  https://support.atlassian.com/bitbucket-cloud/docs/bitbucket-pipelines-configuration-reference/
