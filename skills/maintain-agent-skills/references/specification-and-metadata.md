# Specification and metadata

Research: 2026-09-11. Agent Skills use progressive disclosure: catalog metadata,
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
OpenAI-specific interface and invocation-policy fields are client metadata, not
Agent Skills frontmatter; parse their YAML and check the fields against the
target client documentation instead of assuming portability. Do not invent a
JSON Schema or claim a generator validates existing metadata. Keep display text
consistent with the skill and include `$skill-name` in a default invocation
prompt as required by the bundled skill creator.

The [OpenAI skills guidance](https://openai.com/academy/skills/) recommends
explicit inputs, workflow, output, and final checks, and favors composable
skills over an unfocused end-to-end package.

## Discovery is not authorization

The [Codex skill guide](https://learn.chatgpt.com/docs/build-skills) documents
`policy.allow_implicit_invocation` in `agents/openai.yaml`: omission means
`true`; `false` prevents implicit selection but allows explicit invocation. Keep
automatic selection for normal skills. Use explicit-only policy when the user
requests that mode or delegates the invocation-policy decision and the workflow
should require deliberate named invocation. Do not infer this solely from
commits, releases, or other consequential operations. Require authorization at
the mutation boundary. Preserve a deliberate existing invocation policy;
investigate its provenance when the task explicitly asks to reconsider the
catalog.

A policy change cannot repair an ambiguous description. Test natural requests
against all candidate descriptions, including near neighbors and composition.
Client discovery can shorten descriptions or omit skills when its metadata
budget is exceeded. Put the distinguishing user goal first; inspect actual
client discovery before claiming that a large catalog is fully available.

A keyword match is not a task match. Put likely neighboring non-goals in the
metadata; do not activate a specialized review or audit simply because its
subject appears in routine implementation. For an intentional explicit-only
workflow, also state the invocation requirement in its description and body.
`openai.yaml` is client-specific: it is not a universal enforcement mechanism
for other agents. Check the target host's supported invocation controls rather
than promising that every agent honors this field.
