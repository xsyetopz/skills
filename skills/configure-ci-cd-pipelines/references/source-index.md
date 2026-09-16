# Source index and freshness rules

This index is for source discovery and version checking. It is not a substitute
for the operational rules in `SKILL.md` and the other references. Open the
underlying source; do not treat a search snippet, generated summary, or copied
example as authority.

## Source order

1. Inspect the target repository, installed tool versions, lockfiles, generated
   relationships, and existing validation commands.
1. Use the exact product or language version's official documentation and
   source.
1. Use standards and protocol specifications for normative behavior.
1. Use issue trackers and community reports to discover failure patterns, then
   reproduce the relevant behavior locally before changing production code.

For changing products, record the page or source revision and access date in the
work product when the decision depends on it. Do not silently transfer an API or
limit from another version, fork, operating system, runtime, or hosting tier.

## Primary sources

| Source | Applicability |
| --- | --- |
| [SLSA provenance specification](https://slsa.dev/spec/v1.2/provenance) | Use when artifact provenance is a requirement; match the repository’s adopted level and tooling. |
| [GitHub Actions security hardening](https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions) | Provider-specific trust and permission guidance. |
| [GitLab CI/CD YAML](https://docs.gitlab.com/ci/yaml/) | Provider-specific syntax and semantics. |
| [Bitbucket Pipelines configuration](https://support.atlassian.com/bitbucket-cloud/docs/bitbucket-pipelines-configuration-reference/) | Provider-specific syntax and semantics. |
| [GitHub: en/actions/concepts/security/artifact-attestations](https://docs.github.com/en/actions/concepts/security/artifact-attestations) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub: en/actions/reference/events-that-trigger-workflows](https://docs.github.com/en/actions/reference/events-that-trigger-workflows) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub: en/actions/reference/workflows-and-actions/workflow-syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub: en/actions/security-for-github-actions/security-hardening-your-deployments/about-security-hardening-with-openid-connect](https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/about-security-hardening-with-openid-connect) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub: en/actions/using-workflows/storing-workflow-data-as-artifacts](https://docs.github.com/en/actions/using-workflows/storing-workflow-data-as-artifacts) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [docs.gitlab.com: job artifacts](https://docs.gitlab.com/ci/jobs/job_artifacts/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [docs.gitlab.com: id token authentication](https://docs.gitlab.com/ci/secrets/id_token_authentication/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [docs.gitlab.com: workflow](https://docs.gitlab.com/ci/yaml/workflow/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub source: actions/checkout — README.md](https://github.com/actions/checkout/blob/d23441a48e516b6c34aea4fa41551a30e30af803/README.md) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub source: actions/upload-artifact — README.md](https://github.com/actions/upload-artifact/blob/b7c566a772e6b6bfb58ed0dc250532a479d7789f/README.md) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [support.atlassian.com: configure bitbucket pipelinesyml](https://support.atlassian.com/bitbucket-cloud/docs/configure-bitbucket-pipelinesyml/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [support.atlassian.com: integrate pipelines with resource servers using oidc](https://support.atlassian.com/bitbucket-cloud/docs/integrate-pipelines-with-resource-servers-using-oidc/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [support.atlassian.com: pipeline start conditions](https://support.atlassian.com/bitbucket-cloud/docs/pipeline-start-conditions/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [support.atlassian.com: step options](https://support.atlassian.com/bitbucket-cloud/docs/step-options/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [support.atlassian.com: use artifacts in steps](https://support.atlassian.com/bitbucket-cloud/docs/use-artifacts-in-steps/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |

## Updating this reference

Update a link only after confirming the replacement covers the same contract. If
a source disappears, preserve the rule supported by local evidence and mark the
external verification gap; do not invent a new behavior from memory.
