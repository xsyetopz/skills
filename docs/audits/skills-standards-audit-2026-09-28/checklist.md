# Skill standards checklist

Date: September 28, 2026. Distilled from the pages below, each read in full
on this date. Levels: MUST is a stated requirement, SHOULD a
recommendation, INFO context. Where the repository policy is stricter
(`SKILL.md` body at most 220 lines), the repository policy applies.

Sources:

- agentskills.io: [specification][spec], [best practices][bp],
  [optimizing descriptions][desc], [evaluating skills][eval],
  [using scripts][scr].
- Anthropic: [overview][ov], [best practices][antbp],
  [engineering post][eng], [cookbook][cb], [Academy tutorial][ac].
- OpenAI: [build skills][oai].

## Frontmatter

| ID | Level | Rule | Source quote |
| --- | --- | --- | --- |
| FM-01 | MUST | `name` 1-64 chars, `^[a-z0-9]+(-[a-z0-9]+)*$`, equals directory name | spec: "Must match the parent directory name" |
| FM-02 | MUST | `name` has no `anthropic` or `claude`, no XML tags | overview: "Cannot contain reserved words" |
| FM-03 | MUST | `description` 1-1024 chars, no XML tags | spec, overview |
| FM-04 | MUST | `description` says what the skill does and when to use it | overview: "must include both what the Skill does and when Claude should use it" |
| FM-05 | MUST | `description` in third person; no "I", "you" | Anthropic BP: "Always write in third person" |
| FM-06 | SHOULD | `description` has a "Use when" clause (satisfies agentskills imperative guidance and Anthropic third person together) | desc: "Use imperative phrasing" |
| FM-07 | SHOULD | Key use case and trigger words in the first ~100 chars | OpenAI: "Front-load the key use case and trigger words" |
| FM-08 | SHOULD | Describes user intent, lists implicit contexts, a few sentences | desc: "Describe what the user is trying to achieve" |
| FM-09 | SHOULD | Boundary ("Not for …") where a neighbouring skill overlaps | desc: "clarify the boundary between this skill and adjacent capabilities" |
| FM-10 | MUST | `compatibility` 1-500 chars if present; only for real environment needs | spec |
| FM-11 | MUST | `metadata` values are strings; `allowed-tools` a space-separated string | spec |
| FM-12 | INFO | Only `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools` are defined; other keys go in `metadata` | spec |

## Naming and scope

| ID | Level | Rule | Source quote |
| --- | --- | --- | --- |
| NM-01 | SHOULD | One naming pattern across the collection (gerund preferred; noun phrase or action-oriented acceptable) | Anthropic BP: avoid "Inconsistent patterns within your skill collection" |
| NM-02 | SHOULD | Name covers the skill's whole job; not vague or generic | Anthropic BP: avoid "Vague names", "Overly generic" |
| NM-03 | SHOULD | One coherent job per skill, neither too narrow nor too broad | bp: "Skills scoped too broadly become hard to activate precisely"; OpenAI: "Keep each skill focused on one job" |

## Body

| ID | Level | Rule | Source quote |
| --- | --- | --- | --- |
| BD-01 | MUST (repo) | Body at most 220 lines (sources: under 500 lines, under 5,000 tokens) | spec, bp |
| BD-02 | SHOULD | Only what the agent lacks; no general explanations | Anthropic BP: "Claude is already very smart" |
| BD-03 | SHOULD | Default plus escape hatch, not a menu of equal options | bp: "pick a default and mention alternatives briefly" |
| BD-04 | SHOULD | Procedures for a class of tasks, imperative steps with explicit inputs and outputs | bp; OpenAI: "Write imperative steps with explicit inputs and outputs" |
| BD-05 | SHOULD | Gotchas kept in `SKILL.md`, not only in references | bp: "Keep gotchas in SKILL.md" |
| BD-06 | SHOULD | Validation loop: run a check, fix, repeat | bp, Anthropic BP |
| BD-07 | SHOULD | Plan-validate-execute for batch or destructive work | bp, Anthropic BP |
| BD-08 | SHOULD | Reasons instead of bare ALWAYS/NEVER/MUST | eval: "Reasoning-based instructions … work better than rigid directives" |
| BD-09 | SHOULD | No time-sensitive statements outside an "Old patterns" section | Anthropic BP: "Don't include information that will become outdated" |
| BD-10 | SHOULD | One term per concept | Anthropic BP: "Choose one term and use it throughout" |
| BD-11 | SHOULD | Concrete example (input and output) for output-producing work | bp, Anthropic BP, Academy |
| BD-12 | MUST | Forward slashes in paths; MCP tools fully qualified `Server:tool` | Anthropic BP |

## Files and progressive disclosure

| ID | Level | Rule | Source quote |
| --- | --- | --- | --- |
| FL-01 | SHOULD | Paths relative to the skill root | spec |
| FL-02 | SHOULD | References one level deep from `SKILL.md` | spec, Anthropic BP |
| FL-03 | SHOULD | Each reference mention has a load condition ("Read X when …") | bp: "more useful than a generic 'see references/ for details'" |
| FL-04 | SHOULD | Reference files over 100 lines start with a table of contents | Anthropic BP |
| FL-05 | SHOULD | No orphan files; every bundled file reachable from `SKILL.md` | overview: "Claude accesses these files only when referenced" |
| FL-06 | SHOULD | Each script mention says whether to run it or read it | Anthropic BP, engineering post |
| FL-07 | SHOULD | Descriptive file names | Anthropic BP |

## Scripts

| ID | Level | Rule | Source quote |
| --- | --- | --- | --- |
| SC-01 | MUST | No interactive prompts | scr: "This is a hard requirement" |
| SC-02 | SHOULD | `--help` with description, flags, examples, and exit codes | scr |
| SC-03 | SHOULD | Errors say what went wrong, what was expected, what to try | scr |
| SC-04 | SHOULD | Structured output available; data to stdout, diagnostics to stderr | scr |
| SC-05 | SHOULD | Bounded output by default (limit, summary, `--output`) | scr |
| SC-06 | SHOULD | Dependencies inline (PEP 723 and similar) or documented; packages installed locally only | scr, spec, overview |
| SC-07 | SHOULD | `--dry-run` or confirmation for destructive or stateful scripts; idempotent | scr |
| SC-08 | SHOULD | Pinned versions in one-off commands (`bunx pkg@1.2.3`) | scr: "Pin versions" |
| SC-09 | SHOULD | Named constants justified | Anthropic BP: "avoid voodoo constants" |
| SC-10 | SHOULD | Network calls match the stated purpose | overview security section |

## Evals

| ID | Level | Rule | Source quote |
| --- | --- | --- | --- |
| EV-01 | SHOULD | `evals/evals.json` with `skill_name` equal to `name` and `evals[]` | eval |
| EV-02 | SHOULD | Each case: int `id`, `prompt`, `expected_output`, optional `files` that exist, `assertions` | eval |
| EV-03 | SHOULD | At least three cases, one of them an edge case | Anthropic BP: "At least three evaluations"; eval |
| EV-04 | SHOULD | Assertions objectively checkable, not brittle | eval |
| EV-05 | SHOULD | About 20 trigger queries, 8-10 positive and 8-10 negative, near-miss negatives, fixed ~60/40 split | desc |
| EV-06 | SHOULD | Eval workspaces live outside the skill directory | eval |

## OpenAI metadata

| ID | Level | Rule | Source quote |
| --- | --- | --- | --- |
| OA-01 | INFO | `agents/openai.yaml` `interface` keys: `display_name`, `short_description`, `icon_small`, `icon_large`, `brand_color`, `default_prompt`; flag unknown keys | OpenAI |
| OA-02 | INFO | `policy.allow_implicit_invocation` boolean, default true | OpenAI |
| OA-03 | INFO | Icon paths exist relative to the skill root | OpenAI |
| OA-04 | INFO | Name plus description across the catalog fits ~8,000 chars, or descriptions get shortened | OpenAI: "Codex shortens skill descriptions first" |

## Conflicts between sources

- Description voice: agentskills.io asks for imperative phrasing, Anthropic
  requires third person. A third-person capability sentence followed by
  "Use when …" meets both.
- Naming: only Anthropic gives a style (gerund preferred, consistency
  required). The catalog uses the action-oriented form throughout.
- Trigger query files have no specified location; this catalog keeps them
  in `evals/eval_queries.json`.

[spec]: https://agentskills.io/specification
[bp]: https://agentskills.io/skill-creation/best-practices
[desc]: https://agentskills.io/skill-creation/optimizing-descriptions
[eval]: https://agentskills.io/skill-creation/evaluating-skills
[scr]: https://agentskills.io/skill-creation/using-scripts
[ov]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
[antbp]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
[eng]: https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
[cb]: https://platform.claude.com/cookbook/skills-notebooks-01-skills-introduction
[ac]: https://academy.claude.com/tutorials/teach-claude-your-way-of-working-using-skills
[oai]: https://learn.chatgpt.com/docs/build-skills
