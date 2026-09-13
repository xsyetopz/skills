# Specification and metadata

Research: 2026-09-13. Agent Skills use progressive disclosure: catalog metadata,
the activated `SKILL.md`, then task-relevant bundled resources. The normative
[specification](https://agentskills.io/specification) requires `SKILL.md` with
YAML frontmatter and Markdown instructions.

Required frontmatter:

- `name`: 1–64 lowercase letters, digits, and hyphens; no leading, trailing, or
  consecutive hyphen; exactly matches the parent directory.
- `description`: 1–1024 characters describing both capability and activation.

Optional specification fields are `license`, `compatibility`, `metadata`, and
the experimental `allowed-tools`. `metadata` values are strings. Do not treat an
experimental field as portable without confirming client support. The
specification recommends keeping `SKILL.md` below 500 lines and 5,000 tokens;
these are progressive-disclosure guidance, not frontmatter validity rules.
Reference bundled files with paths relative to the skill root.

OpenAI's [skills guide](https://developers.openai.com/plugins/build/skills)
requires a focused user goal and calls for representative activation,
non-activation, incomplete-input, and edge-case tests. It documents
`agents/openai.yaml` MCP dependencies separately from the portable format.
OpenAI-specific interface fields are client metadata, not Agent Skills
frontmatter; parse their YAML and check the fields against the target client
documentation instead of assuming portability. Do not invent a JSON Schema or
claim a generator validates existing metadata. Keep display text consistent
with the skill and include `$skill-name` in a default invocation prompt as
required by the bundled skill creator.

The [OpenAI skills guidance](https://openai.com/academy/skills/) recommends
explicit inputs, workflow, output, and final checks, and favors composable
skills over an unfocused end-to-end package.

## Description-driven discovery

Describe one recognizable user goal in natural language and, when useful, its
nearest non-trigger. The official [description optimization
guidance][descriptions] confirms that catalog descriptions carry discovery and
should state user intent with specific terms. Do not require one literal grammar
such as `Use when...`; supported clients may expose a boolean invocation policy.

A policy change cannot repair an ambiguous description. Test natural requests
against all candidate descriptions, including near neighbors and composition.
Client discovery can shorten descriptions or omit skills when its metadata
budget is exceeded. Put the distinguishing user goal first; inspect actual
client discovery before claiming that a large catalog is fully available.

A keyword match is not a task match. Prefer the nearest meaningful non-goal over
lists of distant exclusions. Keep concrete consequential-operation boundaries
in the body when the skill can write hosted state, rewrite Git history, execute
hooks or emulators, or perform security testing.

[descriptions]: https://agentskills.io/skill-creation/optimizing-descriptions
