# Use standard AI Agent Skill files and native metadata

Research: 2026-09-14. Agent Skills use progressive disclosure: catalog metadata,
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

OpenAI's [skills guide][ref-skills-guide] requires a focused user goal and calls
for representative activation, non-activation, incomplete-input, and edge-case
tests. It documents `agents/openai.yaml` MCP dependencies separately from the
portable format. OpenAI-specific interface fields are client metadata, not Agent
Skills frontmatter; parse their YAML and check the fields against the target
client documentation instead of assuming portability. Do not invent a JSON
Schema or claim a generator validates existing metadata. Keep display text
consistent with the skill and include `$skill-name` in a default invocation
prompt as required by the bundled skill creator.

The [OpenAI skills guidance][ref-openai-skills-guidance] recommends explicit
inputs, workflow, output, and final checks, and favors composable skills over an
unfocused end-to-end package.

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
lists of distant exclusions. Keep concrete consequential-operation boundaries in
the body when the skill can write hosted state, rewrite Git history, execute
hooks or emulators, or perform security testing.

[descriptions]: https://agentskills.io/skill-creation/optimizing-descriptions

## Source decisions for reliability audits

The specification governs portable format. Body headings, numbered workflows,
resource directories and recommended size limits are not a universal authoring
schema. Keep client metadata and behavior separate from that portable contract.

OpenAI's [Astra guidance][astra] recommends focused descriptions, conditional
resource loading, less elaborate procedural scaffolding and explicit completion
boundaries. Apply those observations to Astra; do not infer that every model
will follow implicit constraints or that shorter always means more reliable.

OpenAI's [model prompting guidance][prompting] favors plain language, precise
verbs, the main point early, and completing the user's intended task without
unnecessary approval pauses. Apply that writing guidance here: state the result,
actions, and stopping evidence directly. Keep explicit rules that prevent known
mistakes. Its model settings and delegation advice are provider-specific, not
permission to change the model or delegate a skill's work.

Anthropic's [authoring guidance][claude-authoring] calibrates specificity to
fragility and variability and recommends evaluation on intended models. Its
[engineering article][claude-evaluation] motivates inspecting actual resource
use and trajectories. Claude-specific tooling examples are not requirements for
Codex. Retain portable safety invariants when they protect a real boundary.

The [Agent Skills best-practices guide][skill-practices] is authoring advice,
not additional normative frontmatter. Adopt task-derived instructions and
execution feedback; treat claims about ideal detail or structure as hypotheses
to test locally. Preserve repository lint policy; heading and list preferences
need no invented model-performance claim.

The community [incomplete-read report][read-report], titled “Codex may only read
the first ~220 lines of a skill file, so put critical instructions at the top.”
It reports partial reads in observed sessions, not a model or format limit. Put
critical instructions first and inspect read coverage when diagnosing an
omission. Do not infer its suggested cap or commenters' module-size rules as
model limits.

[SkillsBench v4][skillsbench] uses paired skill/no-skill comparisons and reports
configuration-dependent results. It supports holding model and agent host fixed,
not an optimal skill length, universal module limit or Astra-specific gain. An
instruction repair and passing package tests do not establish agent uplift.

[astra]: https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra
[prompting]: https://developers.openai.com/api/docs/guides/latest-model
[read-report]: https://www.reddit.com/r/codex/comments/1t1rbqt/codex_may_only_read_the_first_220_lines_of_a/
[claude-authoring]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
[claude-evaluation]: https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
[skill-practices]: https://agentskills.io/skill-creation/best-practices
[skillsbench]: https://arxiv.org/pdf/2602.12670v4

## Resource roles and native descriptors

For Codex 0.154.0, use [the tagged metadata contract](codex-metadata.md). Do not
discard a supported `agents/openai.yaml` as private scaffolding or replace it
with invented frontmatter fields. Preserve unrelated metadata when editing it.

A second skill introduction, installation guide, or per-directory README is not
needed when `SKILL.md` already routes to the working material. Consolidate real
run instructions, prerequisites, expected results, and limitations into the
appropriate conditional reference; do not delete that knowledge. Keep README
output templates when producing a repository README is the skill's actual job.
An output template is not redundant skill documentation.

Do not add a `LICENSE`/`README` sidecar, a frontmatter `license` value, or
license comments merely to make a skill look complete. This catalog
intentionally contains none of those skill-local additions. When third-party
material is actually redistributed, first establish that redistribution is
authorized and preserve any legally required notice in the location required by
that material; do not hide a full notice in `agents/openai.yaml`. If the task
does not authorize redistribution, link to or recreate the needed knowledge from
authoritative sources instead of copying the material. Never infer ownership or
grant a new license.

[ref-skills-guide]: https://learn.chatgpt.com/docs/build-skills
[ref-openai-skills-guidance]: https://openai.com/academy/skills/
