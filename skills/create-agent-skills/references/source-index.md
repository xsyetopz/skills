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
| [Agent Skills specification](https://agentskills.io/specification) | Portable skill structure and metadata requirements. |
| [Agent Skills best practices](https://agentskills.io/skill-creation/best-practices) | Authoring and progressive-disclosure guidance. |
| [OpenAI Codex skill creator](https://github.com/openai/codex/blob/rust-v0.154.0/codex-rs/skills/src/assets/samples/skill-creator/SKILL.md) | Codex-specific authoring guidance and optional metadata behavior. |
| [Google Agent Skills engineering](https://cloud.google.com/blog/topics/developers-practitioners/behind-the-scenes-how-we-build-test-and-scale-google-agent-skills) | Large-scale evaluation and governance practices. |
| [Red Hat skill pitfalls and practices](https://next.redhat.com/2026/07/28/building-skills-for-ai-agents-pitfalls-and-best-practices/) | Production observations on domain knowledge, determinism, scope, and evals. |
| [agentskills.io: evaluating skills](https://agentskills.io/skill-creation/evaluating-skills) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [agentskills.io: optimizing descriptions](https://agentskills.io/skill-creation/optimizing-descriptions) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [agentskills.io: using scripts](https://agentskills.io/skill-creation/using-scripts) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [arxiv.org: 2602.12670v4](https://arxiv.org/pdf/2602.12670v4) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [developers.openai.com: latest model](https://developers.openai.com/api/docs/guides/latest-model) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [developers.openai.com: rethinking skills and prompts for gpt 6 astra](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [developers.openai.com: mcp](https://developers.openai.com/mcp) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [docs.astral.sh: ruff](https://docs.astral.sh/ruff/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub: DavidAnson/markdownlint-cli2](https://github.com/DavidAnson/markdownlint-cli2) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub: agentskills/agentskills/tree/main/skills-ref](https://github.com/agentskills/agentskills/tree/main/skills-ref) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub: microsoft/pyright](https://github.com/microsoft/pyright) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub source: openai/codex — metadata.rs](https://github.com/openai/codex/blob/rust-v0.154.0/codex-rs/ext/skills/src/loader/metadata.rs) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub source: openai/codex — openai_yaml.md](https://github.com/openai/codex/blob/rust-v0.154.0/codex-rs/skills/src/assets/samples/skill-creator/references/openai_yaml.md) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub source: openai/codex — interface.rs](https://github.com/openai/codex/blob/rust-v0.154.0/codex-rs/skills/src/interface.rs) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub source: openai/codex — model.rs](https://github.com/openai/codex/blob/rust-v0.154.0/codex-rs/skills/src/model.rs) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub: rhysd/actionlint](https://github.com/rhysd/actionlint) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub: sharkdp/hyperfine](https://github.com/sharkdp/hyperfine) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [learn.chatgpt.com: build skills](https://learn.chatgpt.com/docs/build-skills) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [marketplace.visualstudio.com: items?itemName=xsyetopz.versionlens redux](https://marketplace.visualstudio.com/items?itemName=xsyetopz.versionlens-redux) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [openai.com: skills](https://openai.com/academy/skills/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [platform.claude.com: best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [www.anthropic.com: equipping agents for the real world with agent skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [www.reddit.com: codex may only read the first 220 lines of a](https://www.reddit.com/r/codex/comments/1t1rbqt/codex_may_only_read_the_first_220_lines_of_a/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [www.shellcheck.net: www.shellcheck.net](https://www.shellcheck.net/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |

## Updating this reference

Update a link only after confirming the replacement covers the same contract. If
a source disappears, preserve the rule supported by local evidence and mark the
external verification gap; do not invent a new behavior from memory.
