# Standards, APIs, and authorities for Hosted Git Resource

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
| [GitHub REST API](https://docs.github.com/en/rest) | Provider-native resource operations and pagination. |
| [GitLab REST API](https://docs.gitlab.com/api/rest/) | Provider-native resource operations and authentication. |
| [Bitbucket Cloud API](https://developer.atlassian.com/cloud/bitbucket/rest/intro/) | Provider-native resource operations. |
| [GitHub: manual/gh_run_view](https://cli.github.com/manual/gh_run_view) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub: en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub: en/graphql/overview/resource-limitations](https://docs.github.com/en/graphql/overview/resource-limitations) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub: en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub: en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets#required-reviewers](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets#required-reviewers) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub: en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub: en/rest/branches/branch-protection](https://docs.github.com/en/rest/branches/branch-protection) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub: en/rest/issues/comments](https://docs.github.com/en/rest/issues/comments) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub: en/rest/issues/issues](https://docs.github.com/en/rest/issues/issues) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub: en/rest/pulls/pulls](https://docs.github.com/en/rest/pulls/pulls) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub: en/rest/pulls/reviews](https://docs.github.com/en/rest/pulls/reviews) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub: en/rest/releases/assets](https://docs.github.com/en/rest/releases/assets) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub: en/rest/releases/releases](https://docs.github.com/en/rest/releases/releases) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub: en/rest/repos/repos](https://docs.github.com/en/rest/repos/repos) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub: en/rest/using-the-rest-api/troubleshooting-the-rest-api](https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub: en/rest/using-the-rest-api/using-pagination-in-the-rest-api](https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [docs.gitlab.com: issues](https://docs.gitlab.com/api/issues/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [docs.gitlab.com: merge request approvals](https://docs.gitlab.com/api/merge_request_approvals/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [docs.gitlab.com: merge requests](https://docs.gitlab.com/api/merge_requests/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [docs.gitlab.com: notes](https://docs.gitlab.com/api/notes/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [docs.gitlab.com: projects](https://docs.gitlab.com/api/projects/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [docs.gitlab.com: protected branches](https://docs.gitlab.com/api/protected_branches/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [docs.gitlab.com: releases](https://docs.gitlab.com/api/releases/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [docs.gitlab.com: authentication](https://docs.gitlab.com/api/rest/authentication/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [docs.gitlab.com: codeowners](https://docs.gitlab.com/user/project/codeowners/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [docs.gitlab.com: description templates](https://docs.gitlab.com/user/project/description_templates/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [docs.gitlab.com: protected](https://docs.gitlab.com/user/project/repository/branches/protected/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [support.atlassian.com: use branch permissions](https://support.atlassian.com/bitbucket-cloud/docs/use-branch-permissions/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |

## Agent behavior and skill-authoring authorities

These sources govern how an agent loads and applies this skill while it works on
hosted Git operation. They supplement the domain authorities in the earlier
source table for Manage Git Hosting.

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
