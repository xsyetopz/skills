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

## Apply current OpenAI model guidance

The specification governs portable format. Body headings, numbered workflows,
resource directories, and recommended size limits are not a universal authoring
schema. Keep client metadata and behavior separate from that portable contract.

For GPT-5.6, state the task intent, relevant context, hard constraints, approval
boundary, available tools, and success evidence once. Remove duplicated
directions and examples one group at a time, then run the held-out evaluations.
Compare the selected reasoning level with the next lower level on the same
tasks. Do not assume that a higher reasoning setting improves quality enough to
justify its token, latency, or monetary cost. Use prompt caching or preserved
reasoning only through the target API's documented mechanism.

For GPT-6, inspect the effective user, repository, skill, and tool instructions
for conflict because the model is more sensitive to loaded context. State how
far the agent can proceed without a question, which actions require approval,
what tests are proportional to the change, and what evidence completes the task.
The user's current instruction outranks a skill guideline when they conflict. A
skill cannot use model initiative to expand task authority.

Use parallel agents or predicted tool calls only when the target client supports
them and evaluation shows a benefit for independent or predictable work. Do not
make either mechanism a portable skill requirement. Record the target model,
reasoning setting, tool set, client, skill revision, tokens, latency, and result
quality when comparing configurations.

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

[gpt-56]:
  https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.6
[gpt-6]: https://developers.openai.com/api/docs/guides/latest-model
[claude-authoring]:
  https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
[claude-evaluation]:
  https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
[skill-practices]: https://agentskills.io/skill-creation/best-practices

Sources: [GPT-5.6 guidance][gpt-56], [GPT-6 guidance][gpt-6].

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
