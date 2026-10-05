# Skill Discoverability Research

This file records what the hosts and heavy users of Agent Skills say about getting skills to
trigger, and the rules this repo takes from it. Findings were read on 2026-10-05. Each finding names
its source; claims marked **unverified** come from a summarizing fetch or a search snippet, not the
raw page.

## Host Limits

| Host | Per-skill cap | Listing budget | On overflow |
| - | - | - | - |
| Claude Code | `description` + `when_to_use` truncated at 1,536 characters (`skillListingMaxDescChars`) | 1% of the model's context window: about 8,000 characters at 200k tokens, about 40,000 at 1M | Drops descriptions of the least-invoked skills first; names stay |
| Codex | 1,024 characters, with a `...` suffix | 2% of the context window, or 8,000 characters when unknown; at most 10,000 tokens if configured | Shortens descriptions first, then may omit skills and warn |
| agentskills.io spec | `description` at most 1,024 characters | About 100 tokens per skill at startup | Not specified |

Sources:

- Claude Code, <https://code.claude.com/docs/en/skills.md>, section "Skill descriptions are cut
  short": "The budget scales at 1% of the model's context window. When the listing overflows, Claude
  Code drops descriptions starting with the skills you invoke least, so the skills you use most keep
  their full text." `when_to_use` is "Appended to `description` in the skill listing and counts
  toward the 1,536-character cap", so it has no budget of its own.
- Claude Code levers from the same page:
  - `skillListingBudgetFraction`, for example `0.02`, raises the budget.
  - `SLASH_COMMAND_TOOL_CHAR_BUDGET` sets a fixed character count.
  - `skillOverrides` values `"on"`, `"name-only"`, `"user-invocable-only"` and `"off"` set
    visibility per skill.
  - `disable-model-invocation: true` removes the description from the listing.
  - `/doctor` estimates the listing cost. `/skill-doctor` finds unused skills. `--debug` logs an
    overflow warning. The `/context` Skills row overstated the listing before v2.1.196.
- Claude Code compaction: after a summary, the most recent invocation of each skill is re-attached,
  keeping its first 5,000 tokens, within a shared budget of 25,000 tokens.
- Codex source, `openai/codex` `codex-rs/ext/skills/src/render.rs`:
  `DEFAULT_SKILL_METADATA_CHAR_BUDGET = 8_000`, `SKILL_METADATA_CONTEXT_WINDOW_PERCENT = 2`,
  `MAX_CONFIGURED_SKILL_METADATA_TOKEN_BUDGET = 10_000`,
  `MAX_CATALOG_SKILL_DESCRIPTION_CHARS = 1_024`. Codex reads `name` and `description` only, so
  `when_to_use` does nothing there.
- Codex docs, <https://learn.chatgpt.com/docs/build-skills> (**unverified** wording): "Front-load
  the key use case and trigger words so a host can still match the skill if descriptions are
  shortened." `policy.allow_implicit_invocation: false` in `agents/openai.yaml` turns off implicit
  selection.
- Spec, <https://agentskills.io/specification.md>: "Max 1024 characters. Non-empty. Describes what
  the skill does and when to use it."

## How Descriptions Should Read

- Anthropic best practices,
  <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices.md>: third
  person, say what the skill does and when to use it, and avoid vague text such as "Helps with
  documents". Claude chooses "from potentially 100+ available Skills".
- Anthropic `skill-creator` (`anthropics/skills`): Claude tends to "undertrigger", so descriptions
  should be "a little bit 'pushy'", and name situations where the user does not say the skill's
  keyword. "Claude only consults skills for tasks it can't easily handle on its own", so trigger
  evals need substantive queries. Its trigger eval uses a 60/40 train/test split, 3 runs per query,
  and up to 5 iterations.
- obra/superpowers `skills/writing-skills/SKILL.md` (2026-09-25): start with "Use when...", keep
  under 500 characters, and "NEVER summarize the skill's process or workflow", because an agent "may
  follow the description instead of reading the full skill content".
- Blake Crosley, <https://blakecrosley.com/blog/skills-my-agent-could-not-see> (**unverified**,
  undated): with 84 skills, 5 lost their descriptions silently. Rewriting 74 descriptions down to
  trigger words cut the listing from 21,848 to 9,885 characters, and the 5 skills came back.
- Conflict: Anthropic asks for what and when in the description, while superpowers asks for triggers
  only. No head-to-head test exists. This repo states when, names trigger words, and leaves out the
  workflow.

Measured description lengths, in characters:

| Repo | Skills | Min | Median | Max |
| - | - | - | - | - |
| obra/superpowers | 15 | — | 107 | 375 |
| vercel-labs/agent-skills | 9 | 184 | 295 | 664 |
| JetBrains/skills | 129 | — | 275 | 967 |
| anthropics/skills | 19 | 204 | about 320 | 1,077 |
| trailofbits/skills | 85 | 102 | 398 | 893 |

## Whether Skills Get Invoked

- Vercel, <https://vercel.com/blog/agents-md-outperforms-skills-in-our-agent-evals> (Jude Gao, 27
  Jan 2026; full text read 2026-10-05). The eval has four arms on Next.js 16 API tasks, scored on
  build, lint, and test. Pass rates were: no docs 53%; a docs skill alone 53%, with "In 56% of eval
  cases, the skill was never invoked"; the skill plus an AGENTS.md line telling the agent to invoke
  it 79%, which "improved the trigger rate to 95%+"; and an 8KB index of doc files in AGENTS.md,
  with no skill, 100%.
  - The index arm maps directories to `.mdx` doc files, not situations to skills. It shows that
    passive docs beat on-demand retrieval, not that a skill index helps.
  - The evidence for a situation-to-skill index is the explicit-instruction arm. Its wording
    mattered: "You MUST invoke the skill" anchored the agent on the docs and missed project
    context, while "explore project first, then invoke skill" did better.
  - The post does not state the model, the host, the number of tasks, the number of runs, or any
    variance. It covers one skill, not routing across many.
  - The harness is in the git history of <https://github.com/vercel/next-evals-oss> (January 2026,
    `lib/claude-code-runner.ts`). It ran Claude Code only, at its default model, with up to 4
    retries for a case that did not fully pass. It counted a skill as invoked when the transcript
    held a `Skill (/nextjs-doc)` call. The codemod PR, vercel/next.js#88961, cites 19 evals. No
    public per-run results back the 56% or 95% figures.
  - The skill's description began "PRIORITY: Use this skill FIRST for ANY task involving Next.js".
    The instruction arm's CLAUDE.md said "Before starting any Next.js task, always use the
    `nextjs-doc` skill first."
- No other source measures a situation-to-skill index in CLAUDE.md or AGENTS.md (searched
  2026-10-05). Related measurements:
  - Scott Spence, [Measuring skill activation][spence-evals] (read through a summarizing fetch, so
    lower confidence): Sonnet 4.5 in Claude Code, 22 prompts,
    2 runs. Activation was 55% and 50% with no hook, 59% and 50% with a simple instruction, and 100%
    in both runs with a UserPromptSubmit hook that makes Claude decide yes or no for each skill
    before acting.
  - Scott Spence, <https://scottspence.com/posts/how-to-make-claude-code-skills-activate-reliably>:
    Haiku 4.5, 50 tests. Simple hook 20%, LLM-eval hook 80%, forced-eval hook 84%.
  - Ivan Seleznov, "How to Make Claude Code Skills Actually Activate (650 Trials)" on Medium
    (**unverified**: the page was blocked, search summary only): directive descriptions reached 100%
    activation "without hooks, without CLAUDE.md".
- Both hosts already put a skill listing in every session. Claude Code loads "a listing of skill
  names and descriptions into context" within 1% of the context window
  ([skills docs](https://code.claude.com/docs/en/skills)). The Codex catalog prompt says to use a
  skill when "the task clearly matches a skill's description shown above"
  ([`catalog_prompt.rs`][codex-catalog]).
  An index that repeats names and descriptions duplicates that listing. Only a line that says when
  to invoke a skill adds something, and only the Vercel instruction arm measures it.
- SkillsBench, arXiv 2602.12670: compact skill bodies helped, and "comprehensive" ones scored about
  +0.7, close to nothing.
- Selection gets worse when near-identical skills sit side by side, so skills are split by distinct
  job, not by language or tool.

## Rules This Repo Takes

- `description` is 400 characters or fewer, with trigger words first, then "Use when …" with
  phrasings that never name the skill, then "Not for <nearest neighbor>". It never summarizes the
  workflow.
- `when_to_use` is optional, 250 characters or fewer, and holds extra user phrasings for Claude
  Code. Anything Codex needs goes in `description`.
- The reference validator (skills-ref) allows only `name`, `description`, `license`,
  `allowed-tools`, `metadata`, and `compatibility`, and has no option to relax that.
  `scripts/validate_spec.py` strips `when_to_use` and `disable-model-invocation` before the spec
  check, and `scripts/validate_repository.py` checks their limits.
- Each install bundle's listing (`description` plus `when_to_use`) stays within 8,000 characters,
  the Claude Code budget at 200k tokens and the Codex fallback. Users install bundles, not the whole
  catalog.
- Skills set no `paths`. In the 2026-10-05 A/B on `write-ci-workflow` (validation split, 1 run,
  Opus 5.5), the skill without `paths` fired on all 4 should-trigger queries in an empty project.
  With `paths: [".github/workflows/**", ".gitlab-ci.yml", "bitbucket-pipelines.yml"]` it did not
  load at all, and the harness preflight stopped with "expected skills did not load", so "add a
  CI workflow" in a repo without one would never reach it.
- Niche skills are manual-only, so they cost no listing space.
- `just index` prints one always-loaded line per skill for CLAUDE.md or AGENTS.md that says when to
  use it in terms of the task, not a copy of its description. A listing alone leaves skills
  uninvoked, and only such a line has a measured gain (Vercel's instruction arm).
- The README tells users who install many bundles about `skillListingBudgetFraction` and
  `skillOverrides` `"name-only"`.
- Trigger evals live in `evals/`, outside the installed package, with should-trigger queries that
  never name the skill and near-miss queries from the nearest neighbor.

## Ecosystem Survey

Stars and dates come from the GitHub API on 2026-10-05.

- **Security:** trailofbits/skills (7.4k stars) and semgrep/skills are strong, but neither covers
  secret scanning or GitHub Actions hardening.
- **Decompilation:** only Melee-specific skills exist (lukechampine/melee-harness,
  itsgrimetime/melee-decomp); none cover splat, objdiff, asm-differ, m2c, or decomp-permuter.
- **Recompilation:** hkmodd/ps2-recomp-Agent-SKILL (30 stars) covers PS2Recomp only; N64Recomp,
  XenonRecomp, and rexglue ship no skills.
- **Reverse engineering:** the MCP servers are strong (ida-pro-mcp, bethington/ghidra-mcp,
  pyghidra-mcp); the skills lean mobile (P4nda0s/reverse-skills).
- **Emulators:** no agent-facing patch or debug skills exist. Several projects restrict agents:
  DuckStation's CLAUDE.md refuses agent work, Dolphin bans LLM-derived console-behavior changes,
  PCSX2 forbids LLM code from new contributors and agent PRs, and xemu requires an agent
  declaration.
- **Interview:** Pocock's `grilling` walks a design tree with a recommended answer per question, but
  has no question budget or spec output. OpenSpec writes `openspec/changes/<name>/` with
  `proposal.md`, `specs/` deltas, `design.md`, and `tasks.md`, checked by
  `openspec validate --strict`.

## Open Leads

- [Too many Claude Code skills? How the listing budget decides which descriptions Claude
  sees][rulestack]
- <https://claudefa.st/blog/guide/mechanics/skill-listing-budget>
- Claude Code issues #13343 ("Skills truncated at 30"), #12782, and #64606.
- `codex-rs` `dynamic_skill_selector.rs`, not yet read.

[rulestack]:
  https://dev.to/rulestack/too-many-claude-code-skills-how-the-listing-budget-decides-which-descriptions-claude-sees-4a6m
[spence-evals]:
  https://scottspence.com/posts/measuring-claude-code-skill-activation-with-sandboxed-evals
[codex-catalog]:
  https://github.com/openai/codex/blob/main/codex-rs/ext/skills/src/catalog_prompt.rs
