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

## Description-driven discovery is not authorization

Every catalog description must state both the concrete capability and an
explicit `Use when...` activation boundary with recognizable task language.
The official [description optimization guidance][descriptions] confirms that
catalog descriptions carry discovery and should state user intent with specific
keywords. Do not require a user to name a skill, and do not add client-specific
invocation-policy fields to opt a skill out of normal description matching.
Natural-language selection supplies workflow guidance only. It never grants
permission for commits, pushes, hosted mutations, security testing, emulator
execution, or any other consequential operation beyond the user's request.

A policy change cannot repair an ambiguous description. Test natural requests
against all candidate descriptions, including near neighbors and composition.
Client discovery can shorten descriptions or omit skills when its metadata
budget is exceeded. Put the distinguishing user goal first; inspect actual
client discovery before claiming that a large catalog is fully available.

A keyword match is not a task match. Put likely neighboring non-goals in the
metadata; do not activate a specialized review or audit simply because its
subject appears in routine implementation. Keep authorization and side-effect
limits in the body, where they constrain execution after discovery.

[descriptions]: https://agentskills.io/skill-creation/optimizing-descriptions
