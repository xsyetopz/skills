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
| [AGENTS.md open format](https://agents.md/) | General format and ecosystem context. |
| [OpenAI AGENTS.md documentation](https://learn.chatgpt.com/docs/agent-configuration/agents-md) | Codex/ChatGPT-specific discovery and precedence behavior; verify current version. |
| [OpenAI Codex — AGENTS.md](https://developers.openai.com/codex/guides/agents-md) | Use for the current Codex discovery and precedence behavior. |
| [Gemini CLI — GEMINI.md](https://geminicli.com/docs/cli/gemini-md/) | Use for Gemini CLI context files and hierarchical loading. |
| [GitHub Copilot repository custom instructions](https://docs.github.com/en/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot) | Use for GitHub Copilot-specific instruction files and supported scopes. |
| [Claude Code memory](https://docs.anthropic.com/en/docs/claude-code/memory) | Use for Claude Code project/user memory behavior; verify current path and precedence. |

## Updating this reference

Update a link only after confirming the replacement covers the same contract. If
a source disappears, preserve the rule supported by local evidence and mark the
external verification gap; do not invent a new behavior from memory.
