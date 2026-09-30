# Cost

## Contents

- [Price table](#price-table)
- [Price each message by its model](#price-each-message-by-its-model)
- [Find the dominant cost](#find-the-dominant-cost)
- [Main and agent split](#main-and-agent-split)
- [What the estimate is not](#what-the-estimate-is-not)
- [Sources](#sources)

## Price table

USD per million tokens, from the [pricing page][pricing], checked
2026-09-30. Prices change; check the page before you publish a figure, and
update `PRICES` and `PRICES_AS_OF` in `scripts/session_stats.py` when they
differ.

| Model ID prefix | Input | 5m cache write | 1h cache write | Cache read | Output |
| --- | --- | --- | --- | --- | --- |
| `claude-opus-5-5` | 4 | 5 | 8 | 0.20 | 20 |
| `claude-sonnet-5-5` | 2 | 2.50 | 4 | 0.20 | 10 |
| `claude-fable-5-1` | 10 | 12.50 | 20 | 0.25 | 50 |
| `claude-haiku-4-5` | 1 | 1.25 | 2 | 0.10 | 5 |

A model ID not in the table is reported as unpriced, not guessed. Add its
row from the pricing page if you need it.

## Price each message by its model

1. Deduplicate assistant rows by `message.id`
   ([why](transcript-data.md#one-api-message-spans-several-rows)).
1. Read the model from `message.model` of each message. One session mixes
   models: the main conversation, subagents with their own `model`, and
   small helper calls.
1. Split cache writes by TTL with `usage.cache_creation`:
   `ephemeral_5m_input_tokens` and `ephemeral_1h_input_tokens`. If the
   split is missing, price `cache_creation_input_tokens` at the 5m rate and
   say so.
1. Multiply each token type by its price and sum per model and per scope.

`scripts/session_stats.py` does these steps and prints one row per model
and scope, with `cost_usd` and a total.

## Find the dominant cost

In agent runs, cache reads usually hold most of the tokens, because each
turn re-sends the whole prompt prefix and it is read from the cache. Do not
assume it: compute the cache-read share of tokens per model from the
script's `--json` output:

```sh
python3 scripts/session_stats.py ~/.claude/projects/-Users-me-repo --json \
  | jq -c '.tokens[] | select(.cost_usd) | {model, scope, cost_usd,
      tokens: (.input + .cache_write_5m + .cache_write_1h + .cache_read
        + .output),
      cache_read_share: (.cache_read / ((.input + .cache_write_5m
        + .cache_write_1h + .cache_read + .output) | if . == 0 then 1
        else . end))}'
```

Then price each token type with the table above and pick the lever that
matches the largest share:

| Dominant cost | Lever |
| --- | --- |
| Cache reads | Fewer turns (the measures in [waste measures](waste-measures.md)), a shorter prompt prefix, fewer large tool results kept in context |
| Cache writes | A stable prefix: fewer changes to injected context mid-session, fewer compactions, a TTL that matches the gap between turns |
| Output | A cheaper model or lower effort for that agent ($choose-claude-model-and-effort), shorter reports |
| Input (uncached) | Check why caching missed: first turns, expired TTL, or a prefix that changes every turn |

Per-million cache-read prices are equal for Opus 5.5 and Sonnet 5.5 in the
table above, so on those two models a model switch mainly changes the
output and cache-write cost. Check the current table before you rely on
this.

## Main and agent split

The script splits by main or subagent from the file path. For agent type,
group subagent files by the `agentType` in their `agent-<agentId>.meta.json`
and run the script on each group, or use the
[jq recipes](transcript-data.md#jq-recipes). Report the agent types that
hold the most cost, with their run counts, before judging any one run.

## What the estimate is not

- It is list-price cost at standard rates. Rows with `usage.speed` other
  than `standard` (fast mode) or `usage.inference_geo` `us` cost more; the
  script counts them in `nonstandard_rate_rows`.
- On a subscription plan it is not the bill. It is a comparable measure of
  how much work a session asked of the model. How plan limits count
  tokens is not stated here; measure it on your own plan if it matters.
- In a live session, `/usage` shows the current session's tokens and cost,
  and a `Prompt cache (main)` line for the main conversation only.

## Sources

- [Pricing][pricing]: base input, 5m and 1h cache writes, cache hits, and
  output per model; the 1.1x US-only inference multiplier; fast mode
  pricing. Fetched 2026-09-30.
- [Manage costs][costs]: `/usage` Session block and the
  `Prompt cache (main)` line. Fetched 2026-09-30.
- [Prompt caching in Claude Code][caching]: cache TTLs and the
  `usage.cache_creation` TTL fields. Fetched 2026-09-30.

[pricing]: https://platform.claude.com/docs/en/about-claude/pricing
[costs]: https://code.claude.com/docs/en/costs
[caching]: https://code.claude.com/docs/en/prompt-caching
