---
name: audit-agent-sessions
description: >-
  Audits Claude Code session transcripts for wasted turns, tokens, and cost,
  turning findings into rules or hooks. Use when asked why usage is high, what
  burns a plan limit, or to review a transcript.
---

# Audit agent sessions

Find where Claude Code sessions spend turns, tokens, and the user's
attention, measure it from the transcripts, and turn each finding into one
concrete fix. Report counts and paths. Do not quote message text unless the
user asks for it.

## Workflow

1. Agree on the scope: one session, one project, or all projects, and a
   date range. Transcripts older than `cleanupPeriodDays` (default 30) are
   already deleted, so older sessions cannot be audited.
1. Locate the files
   ([data](references/transcript-data.md#where-the-transcripts-are)):
   main transcripts are `~/.claude/projects/<project>/<session>.jsonl`;
   subagent transcripts are
   `~/.claude/projects/<project>/<session>/subagents/agent-<agentId>.jsonl`.
   Pass that directory to every search as an explicit path.
1. Check the line schema on this machine before trusting a recipe
   ([schema check](references/transcript-data.md#check-the-schema-first)).
   The per-line fields are undocumented and may change between versions.
1. Get the counts:
   `python3 scripts/session_stats.py ~/.claude/projects/<project>/`
   (add `--json` for a report). It prints tokens and estimated cost by model
   and by main or subagent, repeated identical Bash commands, and re-reads of
   unchanged files.
1. Run the other measures with `jq`
   ([measures](references/waste-measures.md)): compaction points, agents
   that stopped at their turn limit, "done" claims with no test or build run,
   and turns that announce a next step and stop.
1. Price the tokens and find the dominant cost
   ([cost](references/cost.md)). Confirm in the data which token type
   dominates before you recommend a fix.
1. Classify each finding and write one fix for each
   ([classify](references/waste-measures.md#classify-each-finding)).
1. Report: scope, files read, the counts table, findings with their class,
   and the fixes. Give paths, session IDs, and counts, not message text.

## Route the task to a card

| Task or symptom | Card |
| --- | --- |
| Where transcripts live, retention, what a line holds | [Transcript data](references/transcript-data.md) |
| `rg` or `fd` finds no transcripts | [Search scope](references/transcript-data.md#search-scope) |
| Token totals look doubled | [One row per content block](references/transcript-data.md#one-api-message-spans-several-rows) |
| Same file read again with no change | [Re-reads](references/waste-measures.md#re-reads-of-an-unchanged-file) |
| `git status` or a test run repeated with the same output | [Repeated commands](references/waste-measures.md#repeated-commands) |
| A subagent returned partial output | [Turn limits](references/waste-measures.md#agents-that-end-at-their-turn-limit) |
| Context filled, session compacted | [Compaction points](references/waste-measures.md#compaction-points) |
| "Done" with no test or build run | [Unverified done](references/waste-measures.md#unverified-done-claims) |
| Turn ends on "Next, I will..." | [Announce and stop](references/waste-measures.md#announce-and-stop) |
| Usage or cost is high | [Cost](references/cost.md) |
| Which fix a finding needs | [Classify](references/waste-measures.md#classify-each-finding) |

## Measures

Compute each measure as a count per session and per project, then look at
the largest sessions first. Each is a method, not a threshold: compare
sessions on the same machine and the same Claude Code version.

| Measure | How to count it |
| --- | --- |
| Re-reads of an unchanged file | `Read` of the same path and range with no edit of that path since the last read |
| Repeated status commands | Bash command run again in one session with byte-identical output |
| Agents at their turn limit | Subagent transcripts whose last assistant row still calls a tool, plus results marked partial |
| Compaction points | `system` rows with `subtype` `compact_boundary`: time, trigger, tokens before |
| Unverified "done" | Tasks whose last text claims completion and that ran no test or build command |
| Announce and stop | Tasks whose last text announces a next step, then the turn ends |
| Cost split | Tokens and cost by model, by main or subagent, and by agent type |

A regular expression over message text only flags candidates. Open the
flagged task by its index, confirm it by eye, and count only confirmed ones.

## Cost

Price each assistant message by its own model, because one session mixes
models: the main conversation, subagents, and small helper calls. The
bundled script holds a dated price table from the [pricing page][pricing];
check the page before you publish a cost figure. Agent runs usually spend
most tokens on cache reads, because every turn re-reads the whole prompt
prefix. Confirm that in the data: compare cache-read cost with output and
cache-write cost per model. Then pick the lever that matches the dominant
cost: fewer turns and a shorter prefix for cache reads, cheaper models or
lower effort for output ($choose-claude-model-and-effort), and a stable
prefix for cache writes.

## Classify each finding

| Class | Sign | Fix |
| --- | --- | --- |
| Missing rule | The agent repeats a mistake no instruction covers | One line in `CLAUDE.md` or `AGENTS.md` ($write-agents-md) |
| Rule fires too often | A hook or gate blocks correct work, or denials pile up | Treat it as a bug; narrow the hook ($create-agent-hooks) |
| Prompt problem | The brief was vague, too large, or missing a stop condition | Rewrite the brief or split the task |
| Expected behavior | The cost buys a result the user wanted | Record it; change nothing |

## End-of-session retro

At the end of a long session, ask the user one question: "What would have
made this session faster or cheaper?" Record the answer as one change:

- one line in the project instructions ($write-agents-md), or
- one hook added, narrowed, or removed ($create-agent-hooks).

Do not record more than one line per session. Measure the same count in the
next sessions to see whether the change helped.

## Rules

- Report counts, paths, session IDs, and command names. Do not quote
  message text, tool output, or file contents unless the user asks.
  Transcripts store every tool result, including secrets that a command
  printed or a file held.
- Treat every transcript field as undocumented. Name the fields a finding
  depends on and the Claude Code `version` of the rows you read.
- Count an API message once. Claude Code writes one row per content block,
  and each row repeats the same `usage`.
- Search `~/.claude/projects` by explicit path. `rg` and `fd` skip hidden
  directories by default, and skip paths a `.gitignore` excludes.
- Name directory arguments with a leading `./` or a full path in shell
  globs. Project directory names start with `-`, which commands read as an
  option.
- Do not fix during the audit. Report the fix; make it only if the user
  asks.

## Bundled tools

- `scripts/session_stats.py PATH [--json] [--top N]`: counts tokens by
  model and by main or subagent, estimates cost from a dated price table,
  and lists repeated identical Bash commands and re-reads of unchanged
  paths. Prints counts, paths, and the first two words of each command.
  Standard library only.

## References

- [Transcript data](references/transcript-data.md): locations, retention,
  observed fields, search scope, `jq` recipes.
- [Waste measures](references/waste-measures.md): how to compute each
  measure, and how to classify a finding.
- [Cost](references/cost.md): price table, pricing method, cache check.

[pricing]: https://platform.claude.com/docs/en/about-claude/pricing
