# Extension API and toolchain authorities for Vscode Extension Host

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
| [VS Code Extension API](https://code.visualstudio.com/api) | Primary extension API and guides. |
| [VS Code extension host](https://code.visualstudio.com/api/advanced-topics/extension-host) | Host placement and capability model. |
| [Workspace Trust](https://code.visualstudio.com/docs/editor/workspace-trust) | Trust semantics for workspace-controlled execution. |
| [code.visualstudio.com: tree view](https://code.visualstudio.com/api/extension-guides/tree-view) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [code.visualstudio.com: virtual workspaces](https://code.visualstudio.com/api/extension-guides/virtual-workspaces) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [code.visualstudio.com: web extensions](https://code.visualstudio.com/api/extension-guides/web-extensions) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [code.visualstudio.com: webview](https://code.visualstudio.com/api/extension-guides/webview) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [code.visualstudio.com: workspace trust](https://code.visualstudio.com/api/extension-guides/workspace-trust) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [code.visualstudio.com: programmatic language features](https://code.visualstudio.com/api/language-extensions/programmatic-language-features) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [code.visualstudio.com: activation events](https://code.visualstudio.com/api/references/activation-events) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [code.visualstudio.com: extension manifest](https://code.visualstudio.com/api/references/extension-manifest) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [code.visualstudio.com: vscode api](https://code.visualstudio.com/api/references/vscode-api) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [code.visualstudio.com: publishing extension](https://code.visualstudio.com/api/working-with-extensions/publishing-extension) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [code.visualstudio.com: testing extension](https://code.visualstudio.com/api/working-with-extensions/testing-extension) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [code.visualstudio.com: updates](https://code.visualstudio.com/updates) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub source: microsoft/vscode-docs — publishing-extension.md](https://github.com/microsoft/vscode-docs/blob/main/api/working-with-extensions/publishing-extension.md) | Use for the exact target version or source revision; verify applicability before copying an API or command. |

## Agent behavior and skill-authoring authorities

These sources govern how an agent loads and applies this skill while it works on
VS Code extension. They supplement the domain authorities in the earlier source
table for Develop VS Code Extensions.

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
