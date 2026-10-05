---
name: write-agent-skill
description: >-
  Writes, trims, and evaluates Agent Skills, SKILL.md files, skill
  descriptions, references, scripts, and trigger evals for Claude Code and
  Codex. Use when creating or auditing a skill, when a skill never triggers
  or triggers on the wrong requests, or when a SKILL.md grew too long. Not
  for AGENTS.md or CLAUDE.md, or for hooks.
when_to_use: >-
  Make this a skill. Why does Claude never use my skill. Turn these notes
  into a skill. Cut this SKILL.md down. Write trigger evals for this skill.
---

# Write Agent Skill

A skill changes agent behavior only where the model would otherwise get something wrong. Everything
else in it costs context and dilutes the parts that matter. Curated compact skills help.
Comprehensive textbook-style skills measured worse than no skill ([SkillsBench][bench]).

## Rules

- Include only what a capable model gets wrong without the skill. Write each item as the mistake,
  the correct action, and a short reason, in one to three lines. Delete anything the model already
  does reliably. Test this by asking what an agent would do without the line.
- Put the critical rules at the top of the body as specific checks, not advice. "Run
  `tsc --extendedDiagnostics` before changing tsconfig" is followable. "Measure first" is not.
  Claude Code re-attaches only the first 5,000 tokens of an invoked skill after compaction.
- A skill that changes code ends with the command that proves the change, and tells the agent to
  name each check it skipped. Without it, agents report done on unverified work.
- Keep gotchas in the body. A reference may never be opened, so it holds only material for one
  sub-case, such as one language or one tool.
- Give each reference a load condition in the body, such as "Read the Rust reference when the code
  is Rust", with a link to the file. A bare index of files does not get read.
- Keep references one level deep and linked directly from `SKILL.md`. Agents may preview a file
  reached through another file with only its first lines. A reference over 100 lines starts with a
  `## Contents` list of heading links.
- Leave out routing tables that repeat headings, "when to use" sections in the body, persona text,
  completion-report boilerplate, emoji, and horizontal rules. The description already routes, and
  the rest carries no instruction.
- Write in a calm imperative with the reason attached. Reserve capitals and "must" for real hard
  stops. Several model vendors report that shouted rules cause overtriggering and rigid behavior.
- Do not state model names, prices, versions, or benchmark numbers without a source and date. They
  go stale and the agent repeats them as fact.
- Move deterministic, fragile, or repetitive work into a script. A model recalling a number or
  rebuilding a parser each run is a bug. Do not wrap a tool that already does the job, such as
  gitleaks or benchstat.
- Label host- and OS-specific parts, such as "Claude Code only" or "POSIX sh; Git Bash on Windows".
- A risky step (deploy, publish, push, delete, registry or issue writes) names the action and its
  consequence and says to ask the user first. A step that sends data out names the data and the
  service, and the local alternative when one exists. Invoke Python scripts through `python3`, not
  the shebang, and say once that Windows uses `py -3`.
- Name the skill as an explicit verb and object that says the job, such as `write-justfile` or
  `bump-semver`. Vague nouns such as `helper`, `utils`, or `quality` match everything and say
  nothing.
- Split skills by job, not by language or tool. Near-identical skills side by side hurt selection,
  so variants of one job become references in one skill. Before adding a skill, search the catalog
  for its trigger words and extend the skill that owns the job. When two must coexist, give each a
  "Not for" clause naming the other.
- Keep evals outside the installed skill directory, such as `evals/<skill>/` at the repository root.
  Installers copy the whole skill directory, so evals inside it ship to every user.

## Description

The description is the only text a host reads before choosing a skill.

- Form: trigger words first (the tools, file names, and nouns users type), then "Use when" with
  phrasings that never name the skill, then "Not for" the nearest neighbor. Third person.
- State when to use the skill, never its workflow. An agent that reads a summarized process follows
  the summary and skips the body.
- Aim for 200 to 400 characters. Hosts shorten descriptions from the end when the listing overflows,
  so the trigger words lead.
- `when_to_use` is Claude Code only. Use it for two to four extra user phrasings, 250 characters or
  fewer. Codex ignores it, so anything Codex needs goes in `description`. Both share one
  1,536-character cap.
- Plain words only. No colon, semicolon, double quote, backtick, slash, parenthesis, bracket, `$`,
  or `|`. Product names such as C++, C#, and .NET stay as written. An unquoted colon breaks YAML,
  and the rest reads as markup.

Read [descriptions](references/descriptions.md) when a skill does not trigger, triggers on the wrong
requests, or the catalog overflows its listing budget.

## Workflow

1. Collect evidence: real prompts, the failures agents make without the skill, and primary
   documentation for the domain. Write `eval_queries.json` and `evals.json` in the eval directory
   first.
1. Draft the body in this order: one or two sentences of purpose, `## Rules`, `## Workflow` only
   when the order of steps matters, `## Scripts` with each script's usage, and the reference load
   conditions. Start from [`assets/SKILL.template.md`](assets/SKILL.template.md). Aim for about 120
   lines.
1. Write each script with `--help`, exit 0 clean, 1 findings, 2 usage error, one finding per line,
   and a test next to it. Use `.py` with the standard library or `.mjs` run by `bun`; use `.sh` only
   for a POSIX-only task, labeled.
1. Write the description last, from the evals.
1. For Codex, write `agents/openai.yaml` with `display_name`, `short_description` of 25 to 64
   characters, and a `default_prompt` containing `$<skill-name>`. Read [host
   metadata](references/host-metadata.md) for invocation policy, Claude Code frontmatter extensions,
   and install paths.
1. Validate: `skills-ref validate <dir>` if installed (else report it skipped), then
   `python3 scripts/check_reference_structure.py <dir>`, then the repository's own checks.
1. Paired evals are paid runs that send prompts and fixtures to the model API; ask before running
   them, else say that no trials ran. Static checks do not show that a skill changes behavior. Read
   [evaluation](references/evaluation.md) before writing evals or when a revision did not help.

To audit an existing skill, cut first: delete every line the model would follow anyway, then merge
overlapping skills, then fix the description. Read the [audit
checklist](references/evaluation.md#auditing-an-existing-skill).

## Scripts

- `python3 scripts/check_reference_structure.py SKILL_DIR...` checks that every reference is linked
  from `SKILL.md`, long references have a linked `## Contents`, relative links and anchors resolve,
  and the name and description are valid. Exit 0 clean, 1 problems, 2 bad input.

[bench]: https://arxiv.org/abs/2602.12670
