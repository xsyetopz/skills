# Transcript Data

Run these commands in Claude Code's Bash tool (Git Bash on Windows); the recipes need `jq`.

## Contents

- [Where the Transcripts Are](#where-the-transcripts-are)
- [Check the Schema First](#check-the-schema-first)
- [Fields Observed](#fields-observed)
- [jq Recipes](#jq-recipes)
- [Sources](#sources)

## Where the Transcripts Are

The [`.claude` directory reference][dir] documents these paths:

| Path under `~/.claude/` | Content |
| --- | --- |
| `projects/<project>/<session>.jsonl` | Main conversation |
| `projects/<project>/<session>/subagents/` | Subagent transcripts, `agent-<agentId>.jsonl` and `.meta.json` |
| `projects/<project>/<session>/tool-results/` | Large tool outputs spilled to files |
| `projects/<project>/<session>.orphaned-<timestamp>-<suffix>.jsonl` | A set-aside earlier transcript; skip it or you count the session twice |

`<project>` is the working directory with `/` (and `\`, `:` on Windows) replaced by `-` (observed,
not documented). Inside `~/.claude/projects`, `ls -t ./*/*.jsonl` works and `ls -t */*.jsonl` passes
an option. Subagent transcripts are deleted with their parent session.

```sh
rg -l --glob '*.jsonl' 'compact_boundary' ~/.claude/projects
fd -e jsonl . ~/.claude/projects/-Users-me-repo
```

## Check the Schema First

List keys and types of a recent transcript before you run a recipe. These print structure only,
never message text:

```sh
cd ~/.claude/projects
f=$(ls -t ./*/*.jsonl | head -1)
jq -c '[.type, (.message.model // null), (.message.usage | keys? // null),
  (.entrypoint // null)]' "$f" | sort | uniq -c | sort -rn | head
jq -c 'paths | map(tostring) | join(".")' "$f" | sort -u \
  | grep -v '\.input\.' | head -80
```

If a field a recipe uses is missing, adapt the recipe and say so.

## Fields Observed

Seen in September 2026 on Claude Code 2.1.284 and 2.1.285. A starting point, not a contract.

| Field | Where | Observed values |
| --- | --- | --- |
| `type` | every row | `user`, `assistant`, `system`, `attachment`, bookkeeping types |
| `sessionId`, `uuid`, `parentUuid`, `timestamp`, `version`, `cwd`, `gitBranch` | message rows | strings |
| `isSidechain`, `agentId` | subagent rows | `true`, string |
| `message.id` | assistant rows | repeated on each row of one API message |
| `message.model` | assistant rows | a model ID, or `<synthetic>` with zero usage |
| `message.stop_reason` | assistant rows | `tool_use`, `end_turn`, `refusal`, `null` |
| `message.usage` | assistant rows | `input_tokens`, `output_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens`, `cache_creation` (`ephemeral_5m_input_tokens`, `ephemeral_1h_input_tokens`) |
| `message.content[]` | assistant rows | blocks `text`, `thinking`, `tool_use` (`id`, `name`, `input`) |
| `message.content[]` | user rows | a string for a typed prompt; `tool_result` blocks (`tool_use_id`, `content`, `is_error`) |
| `isMeta`, `isCompactSummary` | user rows | `true` on injected rows the user did not type |
| `toolUseResult` | user rows | Bash: `stdout`, `stderr`, `interrupted`; Read: `file.filePath` |
| `subtype`, `compactMetadata` | system rows | `compact_boundary`; `trigger`, `preTokens`, `postTokens`, `durationMs` |

Each subagent transcript has a sibling `agent-<agentId>.meta.json` with `agentType`, `description`,
`model`, and `spawnDepth`.

## jq Recipes

Tokens by model for one transcript, each API message counted once:

```sh
jq -s '[.[] | select(.type == "assistant" and .message.usage)]
  | unique_by(.message.id) | group_by(.message.model)
  | map({model: .[0].message.model, messages: length,
      input: (map(.message.usage.input_tokens // 0) | add),
      cache_write: (map(.message.usage.cache_creation_input_tokens // 0)
        | add),
      cache_read: (map(.message.usage.cache_read_input_tokens // 0) | add),
      output: (map(.message.usage.output_tokens // 0) | add)})' "$f"
```

All transcripts of one project, skipping set-aside copies:

```sh
find ~/.claude/projects/-Users-me-repo -name '*.jsonl' \
  ! -name '*.orphaned-*'
```

Subagent runs by agent type for one session directory:

```sh
jq -r '.agentType' "$session_dir"/subagents/agent-*.meta.json \
  | sort | uniq -c | sort -rn
```

Bash program names by frequency. Full command lines can hold secrets, so print only a first word
made of safe characters; a command that starts with `NAME=value` or quoting counts as `(other)`,
because splitting on spaces would print part of a quoted value. `session_stats.py` parses the words
after an assignment.

```sh
jq -r 'select(.type == "assistant") | .message.content[]?
  | select(.type == "tool_use" and .name == "Bash") | .input.command
  | (split(" ")[0]) as $w
  | if ($w | test("^[A-Za-z0-9_./+:@%-]+$")) then $w else "(other)" end' "$f" \
  | sort | uniq -c | sort -rn | head
```

Count a pattern without printing the matched text with `grep -c` or a `jq` `test()`.

## Sources

- [Explore the `.claude` directory][dir]: paths, subagent directory, `cleanupPeriodDays`. Fetched
  2026-09-30.
- Field table: observed with the schema commands above on 2026-09-30.

[dir]: https://code.claude.com/docs/en/claude-directory
