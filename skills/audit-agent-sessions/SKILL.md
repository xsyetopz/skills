---
name: audit-agent-sessions
description: >-
  Reads Claude Code session transcripts to measure token use, tool calls,
  cost, and failure patterns. Use when reviewing why a session was slow,
  costly, or went wrong.
---

# Audit agent sessions

Claude Code only: the transcripts and their fields belong to Claude Code. Measure where sessions
spent turns and tokens, then report one fix per finding. The fix is a proposal, so make it only if
the user asks.

## Rules

- Report counts, paths, session IDs, and command names, not message text, tool output, or file
  contents. Transcripts store every tool result, so they hold any secret a command printed.
- Count an API message once. Claude Code writes one row per content block and each row repeats the
  same `usage`, so summing rows inflates totals.
- Search `~/.claude/projects` by explicit path. `rg` and `fd` skip hidden directories and
  `.gitignore`d paths, and report zero matches with no error. State the searched directory in the
  report.
- Prefix project directories with `./` or use a full path. Their names can start with `-`, which
  commands read as an option.
- Ask for the date range first. Transcripts older than `cleanupPeriodDays` (default 30) are deleted,
  so older sessions cannot be audited.
- Cache reads usually dominate agent cost, because every turn re-reads the prompt prefix. Compare
  token types from the counts before you pick a fix.
- Treat transcript fields as undocumented. Check the schema on this machine before you rely on a
  `jq` recipe, and name the `version` you read.
- A pattern over message text only flags candidates. Open each flagged task by index, confirm it,
  and report only confirmed counts.
- Give each finding one class and one fix. Missing rule: a line in project instructions
  ($write-agents-md). Hook that blocks correct work: narrow it ($create-agent-hooks). Vague brief:
  rewrite or split it. Expected cost for a wanted result: change nothing.

## Scripts

`python3 scripts/session_stats.py PATH [--json] [--top N] [--prices FILE]` reads a transcript file
or a directory of them. It counts tokens by model and by main or subagent, repeated identical Bash
commands, and re-reads of unchanged files. It prints counts and paths, never message text. On
Windows, use `py -3` for `python3`.

Cost needs a prices file: JSON mapping a model id to `input`, `output`, `cache_write`, and
`cache_read` USD per million tokens, taken from the provider's current pricing page. Without
`--prices` the script reports tokens only. Models missing from the file are listed as unpriced.

## References

- Read [transcript data](references/transcript-data.md) when you need to locate transcripts, check
  the line schema, or write a `jq` recipe.
- Read [waste measures](references/waste-measures.md) when you measure compaction points, subagent
  turn limits, unverified "done" claims, or announce-and-stop turns, which the script does not
  count.
