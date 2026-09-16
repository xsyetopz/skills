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
| [Gemini CLI hooks](https://geminicli.com/docs/hooks/) | Current Gemini hook concepts and event behavior. |
| [Claude Code hooks](https://code.claude.com/docs/en/hooks) | Current Claude Code hook configuration and semantics. |
| [OpenAI Codex hooks](https://developers.openai.com/codex/hooks) | Current Codex hook configuration and semantics. |
| [code.visualstudio.com: hooks](https://code.visualstudio.com/docs/agent-customization/hooks) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [cursor.com: hooks](https://cursor.com/docs/hooks) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub: en/copilot/reference/hooks-reference](https://docs.github.com/en/copilot/reference/hooks-reference) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [geminicli.com: reference](https://geminicli.com/docs/hooks/reference/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [geminicli.com: configuration](https://geminicli.com/docs/reference/configuration/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [opencode.ai: plugins](https://opencode.ai/docs/plugins/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [opencode.ai: plugins](https://opencode.ai/v2/docs/build/plugins) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [opencode.ai: get started](https://opencode.ai/v2/docs/get-started) | Use for the exact target version or source revision; verify applicability before copying an API or command. |

## Updating this reference

Update a link only after confirming the replacement covers the same contract. If
a source disappears, preserve the rule supported by local evidence and mark the
external verification gap; do not invent a new behavior from memory.
