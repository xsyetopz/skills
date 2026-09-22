# Standards, APIs, and authorities for Delivery Pipeline

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
| [SLSA provenance specification](https://slsa.dev/spec/v1.2/provenance) | Use when artifact provenance is a requirement; match the repository's adopted level and tooling. |
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

## Agent behavior and skill-authoring authorities

These sources govern how an agent loads and applies this skill while it works on
CI/CD workflow change. They supplement the domain authorities in the earlier
source table for Configure CI/CD Pipelines.

| Source | Rule applied in this skill |
| --- | --- |
| [OpenAI GPT-5.6 guidance](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.6) | State intent, constraints, autonomy, tools, and success evidence once; compare model and reasoning settings with task evaluations instead of assuming more reasoning is better. |
| [OpenAI GPT-6 guidance](https://developers.openai.com/api/docs/guides/latest-model) | Keep instructions lean, resolve conflicts, make follow-through and approval boundaries explicit, and test behavior on the target model. |
| [OpenAI Codex prompting](https://developers.openai.com/codex/prompting) | Name relevant files, reproduction details, constraints, and verification for repository work. |
| [OpenAI Agent Skills](https://developers.openai.com/codex/skills) | Keep the capability focused and route from `SKILL.md` to task-relevant resources. |
| [Anthropic Agent Skills overview](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview) | Treat a skill as a discoverable directory with progressive resource loading. |
| [Anthropic authoring practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) | Match instruction detail to task fragility and evaluate on intended models. |
| [Anthropic skill engineering](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) | Inspect actual trajectories and use deterministic scripts where generated mechanics create avoidable error. |
| [Agent Skills home](https://agentskills.io/home) and [specification](https://agentskills.io/specification) | Preserve portable frontmatter and progressive disclosure; keep client metadata separate. |
| [Agent Skills best practices](https://agentskills.io/skill-creation/best-practices) | Derive procedures from real tasks, state defaults, include gotchas, and close the plan-validate-execute loop. |
| [Description optimization](https://agentskills.io/skill-creation/optimizing-descriptions) | Test positive, near-miss, and competing-skill activation on the target client. |
| [Skill evaluation](https://agentskills.io/skill-creation/evaluating-skills) | Use realistic `evals/evals.json` cases, clean contexts, paired baselines, objective assertions, and artifact review. |
| [Using scripts](https://agentskills.io/skill-creation/using-scripts) | Prefer direct native commands; add a script only for repeated deterministic work and test its error paths. |
| [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119) | Reserve normative keywords for requirements whose violation causes a material safety, correctness, or interoperability failure. |
| [ASD-STE100](https://www.asd-ste100.org/) | Use controlled technical English principles to reduce ambiguity; do not claim formal conformance without a licensed conformance review. |

## Updating this reference

Update a link only after confirming the replacement covers the same contract. If
a source disappears, preserve the rule supported by local evidence and mark the
external verification gap; do not invent a new behavior from memory.
