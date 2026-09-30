# Transcript data

## Contents

- [Where the transcripts are](#where-the-transcripts-are)
- [Search scope](#search-scope)
- [Check the schema first](#check-the-schema-first)
- [Fields observed](#fields-observed)
- [One API message spans several rows](#one-api-message-spans-several-rows)
- [jq recipes](#jq-recipes)
- [Privacy](#privacy)
- [Sources](#sources)

## Where the transcripts are

The [`.claude` directory reference][dir] documents these paths:

| Path under `~/.claude/` | Content |
| --- | --- |
| `projects/<project>/<session>.jsonl` | Main conversation: every message, tool call, and tool result |
| `projects/<project>/<session>/subagents/` | Subagent transcripts, `agent-<agentId>.jsonl` |
| `projects/<project>/<session>/tool-results/` | Large tool outputs spilled to separate files |
| `projects/<project>/<session>.orphaned-<timestamp>-<suffix>.jsonl` | A set-aside earlier transcript; skip it or you count the session twice |

`<project>` is the working directory with `/` replaced by `-` (observed,
not documented), so the name starts with `-`. Quote it and prefix `./` in
globs: `ls -t ./*/*.jsonl` inside `~/.claude/projects` works;
`ls -t */*.jsonl` passes an option.

Claude Code deletes these files once they are older than
`cleanupPeriodDays`. The default is 30 days; the minimum is 1. Subagent
transcripts go with their parent session. To audit a longer period, copy
the files out before they age out, or raise the setting ahead of time.

## Search scope

`rg` and `fd` skip hidden directories such as `~/.claude` by default, and
skip any path a `.gitignore` excludes (for example a dotfiles repository
that ignores `.claude/`). A search from `~` then finds no transcripts and
reports no error. Name the directory as the search path:

```sh
rg -l --glob '*.jsonl' 'compact_boundary' ~/.claude/projects
fd -e jsonl . ~/.claude/projects/-Users-me-repo
```

State the searched directory in the report, so a zero is read as "none in
this scope" and not "none anywhere".

## Check the schema first

The per-line fields are not documented and may change between Claude Code
versions. Before running a recipe, list the keys and types of a recent
transcript. These commands print structure only, never message text:

```sh
cd ~/.claude/projects
f=$(ls -t ./*/*.jsonl | head -1)
jq -c '[.type, (.message.model // null), (.message.usage | keys? // null),
  (.entrypoint // null)]' "$f" | sort | uniq -c | sort -rn | head
jq -r 'keys[]' "$f" | sort | uniq -c | sort -rn | head -40
jq -c 'paths | map(tostring) | join(".")' "$f" | sort -u \
  | grep -v '\.input\.' | head -80
```

If a field a recipe uses is missing, adapt the recipe to the fields you
see and say so in the report.

## Fields observed

Seen on one machine in September 2026, Claude Code `version` 2.1.284 and
2.1.285. Treat them as a starting point, not a contract.

| Field | Where | Observed values |
| --- | --- | --- |
| `type` | every row | `user`, `assistant`, `system`, `attachment`, and bookkeeping types |
| `sessionId`, `uuid`, `parentUuid`, `timestamp`, `version`, `cwd`, `gitBranch` | message rows | strings |
| `entrypoint` | message rows | `cli`, `sdk-cli` |
| `isSidechain` | message rows | `true` in subagent transcripts |
| `agentId` | subagent rows | string |
| `message.model` | assistant rows | a model ID, or `<synthetic>` with zero usage |
| `message.id` | assistant rows | repeated on each row of one API message |
| `message.stop_reason` | assistant rows | `tool_use`, `end_turn`, `refusal`, `null` |
| `message.usage` | assistant rows | `input_tokens`, `output_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens`, `cache_creation`, `speed`, `inference_geo`, `service_tier`, and others |
| `message.usage.cache_creation` | assistant rows | `ephemeral_5m_input_tokens`, `ephemeral_1h_input_tokens` |
| `message.content[]` | assistant rows | blocks of `type` `text`, `thinking`, `tool_use` (`id`, `name`, `input`) |
| `message.content[]` | user rows | a string for a typed prompt; blocks of `type` `tool_result` (`tool_use_id`, `content`, `is_error`) for tool results |
| `isMeta`, `isCompactSummary` | user rows | `true` on injected rows that the user did not type |
| `toolUseResult` | user rows | tool-specific: Bash has `stdout`, `stderr`, `interrupted`; Read has `file.filePath` |
| `subtype` | system rows | `compact_boundary`, `local_command` |
| `compactMetadata` | compact rows | `trigger` (`auto` seen), `preTokens`, `postTokens`, `durationMs` |

Each subagent transcript has a sibling `agent-<agentId>.meta.json` with
`agentType`, `description`, `model`, and `spawnDepth`.

## One API message spans several rows

Claude Code writes one assistant row per content block (thinking, text,
each tool call). Every row of one API message carries the same
`message.id` and the same `usage`. Summing `usage` over rows counts a
message several times. Deduplicate by `message.id` first, as the recipes
below and `scripts/session_stats.py` do.

## jq recipes

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

For a whole session, list the main file and its subagents, skipping
set-aside copies, and pass them together with `jq -s ... $(...)` or `cat`:

```sh
find ~/.claude/projects/-Users-me-repo -name '*.jsonl' \
  ! -name '*.orphaned-*'
```

Subagent runs by agent type for one session directory:

```sh
jq -r '.agentType' "$session_dir"/subagents/agent-*.meta.json \
  | sort | uniq -c | sort -rn
```

Bash commands by frequency (tool input can hold secrets; review before you
share it):

```sh
jq -r 'select(.type == "assistant") | .message.content[]?
  | select(.type == "tool_use" and .name == "Bash") | .input.command' "$f" \
  | sort | uniq -c | sort -rn | head
```

Paths read more than once:

```sh
jq -r 'select(.type == "assistant") | .message.content[]?
  | select(.type == "tool_use" and .name == "Read") | .input.file_path' "$f" \
  | sort | uniq -c | sort -rn | awk '$1 > 1' | head
```

## Privacy

Transcripts are not encrypted at rest; file permissions are the only
protection. If a tool read a `.env` file or a command printed a credential,
the value is in the transcript. Therefore:

- Print keys, types, counts, paths, and command names. Do not print
  `message.content[].text`, `thinking`, tool results, or `toolUseResult`
  unless the user asks for a specific row.
- Do not paste transcript rows into issues, chats, or other tools.
- Filter with `grep -c` or `jq` `test()` to count a pattern without
  printing the matched text.

## Sources

- [Explore the `.claude` directory][dir]: transcript paths, subagent
  directory, `cleanupPeriodDays`, and the note that transcripts are not
  encrypted. Fetched 2026-09-30.
- Field table: observed with the schema commands above on 2026-09-30. The
  fields are not documented.

[dir]: https://code.claude.com/docs/en/claude-directory
