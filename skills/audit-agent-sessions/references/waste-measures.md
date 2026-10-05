# Waste Measures

Run the shell blocks in Claude Code's Bash tool (Git Bash on Windows); they need `jq`.

Each measure is a method. None has a universal threshold: compare sessions from the same machine and
Claude Code version, and read the largest outliers first. All recipes assume `f` is one transcript
and print counts, never message text. The fields they use are undocumented; run the [schema
check](transcript-data.md#check-the-schema-first) first.

## Contents

- [Re-reads and Repeated Commands](#re-reads-and-repeated-commands)
- [Agents That End at Their Turn Limit](#agents-that-end-at-their-turn-limit)
- [Compaction Points](#compaction-points)
- [Split a Transcript into Tasks](#split-a-transcript-into-tasks)
- [Unverified Done Claims](#unverified-done-claims)
- [Announce and Stop](#announce-and-stop)
- [Sources](#sources)

## Re-reads and Repeated Commands

`scripts/session_stats.py` counts both. Two blind spots: reads and edits through Bash (`cat`,
`sed -i`) are not `Read` or `Edit` calls, so count them separately and call the result approximate.
A re-read after a formatter, generator, or another agent changed the file, and polling a running
job, are not waste; check the calls in between.

- Typical fix: read only the needed line range, and rerun a status command only after an action that
  can change its output.

## Agents That End at Their Turn Limit

A subagent with `maxTurns` in its definition stops at that limit, and Claude Code marks its returned
output as partial. The parent then resumes it, redoes the work, or reports an incomplete result.

Per subagent transcript, count API messages, tool errors, and the last stop reason:

```sh
for s in "$session_dir"/subagents/agent-*.jsonl; do
  jq -s -c --arg f "${s##*/}" '{file: $f,
    messages: ([.[] | select(.type == "assistant") | .message.id]
      | unique | length),
    errors: ([.[] | select(.type == "user") | .message.content[]?
      | select(.type == "tool_result" and .is_error == true)] | length),
    last_stop: ([.[] | select(.type == "assistant")] | last
      | .message.stop_reason)}' "$s"
done
```

- A transcript whose last assistant row has `stop_reason` `tool_use` stopped while it was still
  calling tools. `null` also appears on final rows; do not read a meaning into it.
- Compare `messages` with the agent's `maxTurns` (from its definition file and the `agentType` in
  `agent-<agentId>.meta.json`). Many runs at or near the limit mean the limit, the brief, or the
  task size is wrong.
- A high `errors` count near the end shows turns spent on denied or failed tool calls. Open the
  error rows by index to see which tool and rule denied them (keys only, unless the user asks).
- Typical fix: a smaller brief, a rule or hook that stops the retry loop earlier, or a different
  limit.

## Compaction Points

Each compaction writes a `system` row with `subtype` `compact_boundary`:

```sh
jq -c 'select(.type == "system" and .subtype == "compact_boundary")
  | [.timestamp, .compactMetadata.trigger, .compactMetadata.preTokens,
     .compactMetadata.postTokens]' "$f"
```

- Count compactions per session and record `preTokens` (context size at the trigger) and the time
  between compactions.
- A compaction discards detail, and the cache prefix is rebuilt after it. Look at what the agent
  does next: re-reads and repeated commands right after a boundary show lost context.
- Typical fix: split long tasks, start a fresh session between unrelated tasks, or add a
  `# Compact instructions` section to `CLAUDE.md` that names what to keep.

## Split a Transcript into Tasks

A task runs from one typed prompt to the next. A typed prompt is a `user` row whose
`message.content` is a string, with `isMeta` and `isCompactSummary` not set. The program below
prints one object per task with a count of test or build commands and two booleans; it never prints
text. Save it as `tasks.jq`:

```jq
reduce (.[] | select(.type == "user" or .type == "assistant")) as $r
  ([]; if $r.type == "user" and ($r.message.content | type) == "string"
          and ($r.isMeta | not) and ($r.isCompactSummary | not)
       then . + [{tests: 0, last_text: ""}]
       elif length == 0 then .
       else .[-1] |= (
         ([$r.message.content[]? | select(.type == "tool_use"
            and .name == "Bash") | .input.command
            | select(test($tests))] | length) as $n
         | .tests += $n
         | ([$r.message.content[]? | select(.type == "text") | .text]
            | last) as $t
         | if $t then .last_text = $t else . end)
       end)
| to_entries
| map({task: .key, tests: .value.tests,
       claims_done: (.value.last_text | test($done; "i")),
       announces_next: (.value.last_text | test($next; "i"))})
```

Run it with the project's own test and build commands in `$tests`:

```sh
jq -s -c -f tasks.jq \
  --arg tests '\b(just test|bun test|pytest|cargo test|go test)\b' \
  --arg done '\b(done|complete|fixed|all tests pass)\b' \
  --arg next '(next,? i.ll|let me|now i.ll)[^.]*[.:]?\s*$' "$f"
```

Take the command pattern from the repository's `AGENTS.md`, `CLAUDE.md`, `justfile`, `Makefile`, or
`package.json`, not from this example.

## Unverified Done Claims

Tasks with `claims_done` true and `tests` 0. The agent reported completion without running a check
in that task.

- The pattern flags candidates. Open each flagged task by its `task` index, read the last message,
  and count only real completion claims. Report the confirmed count, not the candidate count.
- Not waste: a task with nothing to test (a question, a docs change with no checker), or a check the
  user ran themselves.
- Typical fix: a rule naming the check command to run before reporting done, or a `Stop` hook that
  blocks the stop until a check ran ($write-agent-stop-condition).

## Announce and Stop

Tasks with `announces_next` true: the last text says what the agent will do next ("Next, I'll run
the tests."), and the turn ends. The user must send another prompt to get the work the agent already
planned.

- Confirm each candidate by eye, as above. A question to the user is not a stop; a plan the user
  asked for is not a stop.
- Typical fix: a rule that the final message reports results, not plans, while work remains; or a
  `Stop` hook that checks the last message.

## Sources

- [Subagents][sub]: `maxTurns` stops a subagent and marks its output as partial. Fetched 2026-09-30.
- [Manage costs][costs]: `# Compact instructions` in `CLAUDE.md`. Fetched 2026-09-30.
- The transcript fields used here are observed, not documented; see [transcript
  data](transcript-data.md#fields-observed).

[sub]: https://code.claude.com/docs/en/sub-agents
[costs]: https://code.claude.com/docs/en/costs
