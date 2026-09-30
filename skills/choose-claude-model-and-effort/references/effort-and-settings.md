# Effort and settings

## Contents

- [Effort levels](#effort-levels)
- [Defaults per model](#defaults-per-model)
- [Where to set effort](#where-to-set-effort)
- [Claude Code precedence](#claude-code-precedence)
- [Subagent frontmatter](#subagent-frontmatter)
- [Subagent model order](#subagent-model-order)
- [Cache effects of switching](#cache-effects-of-switching)
- [Sources](#sources)

## Effort levels

Effort controls how many tokens Claude spends on a response, thinking,
text, and tool calls alike; lower effort also means fewer and terser
tool calls. The effort docs describe the levels as:

| Level | Docs description | Typical use in the docs |
| --- | --- | --- |
| `max` | No constraints on token spending | Deepest reasoning |
| `xhigh` | Extended capability for long-horizon work | Agentic and coding tasks over 30 minutes |
| `high` | As many tokens as the task needs | Complex reasoning, hard coding, agentic tasks |
| `medium` | Moderate token savings | Balance of speed, cost, and performance |
| `low` | Significant savings, some capability loss | Simple tasks, subagents |

Not every model that supports `max` supports `xhigh`. The docs list
`xhigh` and `max` on Fable 5.1, Opus 5.5, and Sonnet 5.5. Claude Haiku
4.5 is not on the effort page's supported-models list; check the docs
before you set effort for it.

## Defaults per model

From the effort docs, checked 2026-09-30:

- Default: `high` on every model that supports effort, except Opus 5.5,
  which defaults to `medium`. Setting the default value explicitly
  behaves the same as omitting it.
- Opus 5.5: adaptive thinking is always on, so effort is the main
  control for reasoning and cost. A request that omits effort runs one
  level lower than it did on Opus 5. The docs say to run an effort sweep
  on your own evals instead of carrying settings over.
- Sonnet 5.5: levels are recalibrated against Sonnet 5. For agentic
  coding and multistep tool use, the docs suggest starting at `medium`
  for well-specified tasks and `high` for harder or longer ones; use
  `xhigh` or `max` only where evals show a gain.
- Fable 5.1: start at `high`, the default; step up for the most
  capability-sensitive work, down once evals show quality holds.
- At high levels, set a large `max_tokens`: it limits total output,
  thinking plus response text.

An effort sweep: run the same task set at two or three levels, record
`output_tokens` and pass or fail for each run, and keep the lowest level
whose results hold.

## Where to set effort

API, on the request (no beta header needed):

```json
{
  "model": "claude-opus-5-5",
  "max_tokens": 64000,
  "output_config": { "effort": "high" },
  "messages": [{ "role": "user", "content": "..." }]
}
```

Opus 5.5, Sonnet 5.5, and Fable 5.1 also accept a per-message effort
change in beta (header `mid-conversation-output-config-2026-07-01`),
which keeps the prompt cache. For request code, use the Claude API
reference.

Claude Code:

- `CLAUDE_CODE_EFFORT_LEVEL`: `low`, `medium`, `high`, `xhigh`, `max`,
  or `auto` for the model default. Available levels depend on the model.
- `--effort` flag for one session.
- `/effort [level|auto|status]` in a session; `max` is session-only.
- `effortLevel` and `modelSettings` in settings files.
- `maxEffortLevel`: a cap; the lowest cap from any scope applies
  (Claude Code v2.1.267 or later for caps from non-managed scopes).

Model in Claude Code: `--model` or `/model` for a session, the
`ANTHROPIC_MODEL` variable, or the `model` setting.

## Claude Code precedence

- Effort: `CLAUDE_CODE_EFFORT_LEVEL` wins over `--effort`, `/effort`,
  `modelSettings`, and `effortLevel`. A `maxEffortLevel` cap still
  applies on top. A variable exported in a shell profile therefore
  silently overrides every `/effort` you type; check it first when a
  level does not stick.
- Model: `--model` and `/model` override `ANTHROPIC_MODEL`, which
  overrides the `model` setting. A managed `availableModels` list
  restricts all of them.

## Subagent frontmatter

A subagent file in `.claude/agents/` sets both fields:

```markdown
---
name: bug-investigator
description: Finds the root cause of a failure with no known fix.
model: opus
effort: high
---
```

- `model`: `sonnet`, `opus`, `haiku`, `fable`, a full model ID such as
  `claude-opus-5-5`, or `inherit`.
- `effort`: `low`, `medium`, `high`, `xhigh`, or `max`; overrides the
  session level while the subagent runs; inherits it when omitted.
  Available levels depend on the model.

## Subagent model order

Claude Code resolves a subagent's model in this order:

1. The per-invocation `model` parameter Claude passes.
1. The `model` frontmatter (`inherit` selects the main model).
1. `CLAUDE_CODE_SUBAGENT_MODEL`, when set to an alias or ID.
1. The main conversation's model.

A family alias such as `opus` in frontmatter resolves to the main
conversation's exact model when the main model is in that family. An
alias in `CLAUDE_CODE_SUBAGENT_MODEL` always resolves to the version the
alias points to. `CLAUDE_CODE_SUBAGENT_MODEL` alone does not change the
built-in Explore and Plan subagents.

## Cache effects of switching

- Model: each model has its own cache. After `/model`, the next request
  reads the whole conversation with no cache hits.
- Effort: on most models each level has its own cache. On Opus 5.5,
  Sonnet 5.5, and Fable 5.1 with an API key or a Claude subscription,
  changing effort keeps the cache. This does not hold on Amazon
  Bedrock, Google Cloud's Agent Platform, a Claude apps gateway, with
  `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS`, or in a HIPAA configuration.
- A subagent starts its own cache; its first request does not read the
  parent's.

Pick the model and effort at the start of a session; change them at a
natural break.

## Sources

- Effort: <https://platform.claude.com/docs/en/build-with-claude/effort>
- Models overview:
  <https://platform.claude.com/docs/en/about-claude/models/overview>
- Environment variables: <https://code.claude.com/docs/en/env-vars>
- Settings: <https://code.claude.com/docs/en/settings>
- Commands (`/effort`, `/model`): <https://code.claude.com/docs/en/commands>
- Subagents: <https://code.claude.com/docs/en/sub-agents>
- Prompt caching: <https://code.claude.com/docs/en/prompt-caching>
