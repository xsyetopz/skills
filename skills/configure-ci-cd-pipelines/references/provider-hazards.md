# Check CI provider permissions and untrusted execution

## GitHub Actions

Check each event's ref, token permissions, and secret availability.
`pull_request_target` runs in a privileged base-repository context; checking out
and executing an untrusted PR there can expose that privilege. Treat expressions
derived from titles, branch names, comments, and other attacker-controlled
fields as untrusted; pass data through arguments/environment safely rather than
interpolating it into shell source.

Set permissions at the narrowest appropriate scope. Pin external actions
according to the project's supply-chain policy and verify the intended immutable
revision when changing a pin. A reusable workflow, composite action, and
ordinary job have different input, secret, and permission behavior. Do not
assume one can be substituted without checking the native contract.

## GitLab CI

Inspect `workflow: rules`, job `rules`, pipeline source, and
branch/merge-request context together; avoid unintended duplicate pipelines or
missing jobs. Check protected variables/runners, artifact paths and expiry,
`needs` relationships, and token permissions. A merged-result or merge-train
pipeline can test a different commit than a branch pipeline.

## Bitbucket Pipelines

Check branch, pull-request, tag, and custom pipeline selectors against the
requested event. Verify step isolation, artifacts, caches, deployment
environments, and variable scope under current provider documentation. Do not
copy GitHub event expressions or GitLab `rules` into a superficially similar
YAML file.

## Across providers

A checksum from the same untrusted artifact producer does not establish
provenance. Do not grant deploy authority to arbitrary PR-generated artifacts.
Verify the association between the tested revision, artifact, and release
destination. Keep native provider settings accessible; unsupported requested
controls must be reported, not approximated silently.

Sources: [GitHub Actions security][ref-github-actions-security], [GitLab CI
YAML](https://docs.gitlab.com/ci/yaml/), [Bitbucket
configuration][ref-bitbucket-configuration].

[ref-github-actions-security]: https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions
[ref-bitbucket-configuration]: https://support.atlassian.com/bitbucket-cloud/docs/configure-bitbucket-pipelinesyml/
