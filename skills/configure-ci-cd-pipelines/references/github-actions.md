# GitHub Actions events, jobs and credentials

Examples below illustrate provider contracts. Resolve repository commands,
images, action revisions, and server support before applying them.

## Event semantics

`pull_request` commonly tests a synthetic merge ref; its head SHA identifies the
contributor revision. `push` runs for pushed refs. `pull_request_target` runs in
the base repository's context and can have privileged credentials: never combine
it with executing contributor code. `workflow_dispatch` requires an eligible
workflow on the default branch; `schedule` runs from the default branch and can
be delayed. Add `merge_group` when required checks must run in a merge queue.
Branch/path filters can prevent an entire workflow, leaving a required check
pending. [Events][1-source-1].

[1-source-1]:
https://docs.github.com/en/actions/reference/events-that-trigger-workflows

## Dependencies and artifacts

The example pins checkout v6 and upload-artifact v6. Their pinned upstream
READMEs were read on 2026-09-15; the workflow was not run in GitHub Actions.
Both use Node 24 and require runner 2.327.1 or later; authenticated Git in
Docker actions with checkout v6 requires runner 2.329.0 or later.
Upload-artifact v4+ is not supported on GHES: use the target server's supported
artifact action instead. See the pinned [checkout README][checkout] and [upload
README][upload]. The build command is a project-specific integration point, not
a supplied executable. Replace it with the repository's actual validation
command.

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
      - uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803
        with:
          persist-credentials: false
      - run: ./scripts/build-and-test
      - uses: actions/upload-artifact@b7c566a772e6b6bfb58ed0dc250532a479d7789f
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

The report job observes failure/skips without changing build's outcome. It is
not a required-check aggregator: printing a failed dependency still exits zero.
If only an aggregator is required by branch policy, explicitly reject each
required dependency result other than `success`; unexpected skips are not
passes. Keep intentional optional jobs outside that required set. A normal
`needs` consumer runs only after successful dependencies unless its condition
changes that behavior. Define step IDs and job `outputs` when passing small
values through `$GITHUB_OUTPUT`; artifacts carry files across jobs. Matrix
producers need unique artifact names and explicit aggregation. Fail consumers
when required artifacts are absent. [Workflow syntax][2-source-1],
[artifacts][2-source-2].

[2-source-1]:
https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
[2-source-2]:
https://docs.github.com/en/actions/using-workflows/storing-workflow-data-as-artifacts

An explicit `shell: bash` uses GitHub's `bash --noprofile --norc -e -o pipefail`
invocation. Unspecified Linux/macOS shell behavior differs; `shell: sh` does not
provide that Bash pipefail contract. Reproduce the runner's exact shell flags
when checking `producer | tee log`, not just `bash script`. Test failure and
success, including the actual final required-check status.

## Reuse and trust

Reusable workflows use `workflow_call`; declare typed inputs, outputs and
secrets and call them at job level. Keep reusable-workflow token permissions
within the caller's grants. Prefer explicit secret mapping over inheriting
unrelated secrets. `workflow_run` can grant privileges despite an unprivileged
upstream run; validate the source run and artifact before privileged
consumption.

Keep shell source literal: put `${{ github.event.pull_request.title }}` in an
environment value, then quote its shell expansion. Set `persist-credentials:
false` for checkout jobs that do not push. Pin actions to verified full commit
SHAs. Check runner requirements when updating actions. [Secure use][3-source-1].

[3-source-1]:
https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions

## Deployment and cancellation

Use job `environment` for the intended deployment target and its existing
approvals. Grant `id-token: write` only to the job exchanging OIDC tokens; this
permission alone grants no cloud role. Restrict the cloud trust policy to the
repository, ref/environment and audience. [OIDC][4-source-1].

Set concurrency groups according to resource ownership: canceling outdated PR
checks is often useful, while canceling a production deployment mid-migration
can leave partial state. Define an explicit final status job only when
required-check policy needs aggregation, and make it fail when any required
dependency failed. Verify fork PR, branch push, tag/dispatch and cancellation
paths affected by the edit; a local command pass cannot prove those hosted
transitions.

[4-source-1]:
https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/about-security-hardening-with-openid-connect
[checkout]:
https://github.com/actions/checkout/blob/d23441a48e516b6c34aea4fa41551a30e30af803/README.md
[upload]:
https://github.com/actions/upload-artifact/blob/b7c566a772e6b6bfb58ed0dc250532a479d7789f/README.md
