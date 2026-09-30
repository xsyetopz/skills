# Limits and caching

## Contents

- [Measure a headless batch](#measure-a-headless-batch)
- [Prompt cache TTL](#prompt-cache-ttl)
- [TTL controls and precedence](#ttl-controls-and-precedence)
- [Write cost versus idle misses](#write-cost-versus-idle-misses)
- [Verify the TTL](#verify-the-ttl)
- [Sources](#sources)

## Measure a headless batch

The Claude Code docs do not say how `claude -p` or Agent SDK runs count
against subscription plan limits compared with interactive use. Do not
plan a large batch on a multiplier from a forum or from memory. Measure
it:

1. Pick a sample of 5 to 10 jobs that match the batch: same prompt
   shape, repository size, model, and effort.
1. Stop other Claude use on the account for the measurement, so that
   only the sample moves the numbers. Session and weekly limits are
   shared across all models.
1. Start well inside a usage window, not near a reset, and open `/usage`
   in an interactive session. Write down the session and weekly
   percentages.
1. Run the sample and keep each result:

   ```sh
   claude -p "$(cat job-01.txt)" --output-format json > run-01.json
   ```

1. Sum the `usage` fields across the results and price them with the
   [cost formula](prices-and-cost.md#cost-formula). This is the
   API-equivalent cost of the sample.
1. Open `/usage` again. The change in each percentage divided by the
   number of jobs is the limit use per job. Make the sample large
   enough to move the bars by several points; a one-point move is
   within rounding.
1. Multiply by the batch size and compare it with the percentage left
   in the window, with a margin. Split the batch across windows if it
   does not fit.
1. To compare with interactive work, repeat steps 3 to 6 for an
   interactive session of similar size and compare limit use per
   API-equivalent dollar. Record the date and Claude Code version; the
   result can change with either.

With an API key, runs are billed at API rates, so the cost formula
gives the bill; workspace spend and rate limits still apply.

## Prompt cache TTL

Claude Code sorts each request into one of two buckets:

- Main conversation: interactive turns, `-p` runs, and Agent SDK turns.
- Everything else: subagents, workflows, in-process teammates, forks,
  compaction, and session titles.

Default TTL per bucket:

| Bucket | Subscription within plan usage | Usage credits, API key, or cloud provider |
| --- | --- | --- |
| Main conversation | One hour | Five minutes |
| Everything else | Five minutes (a few server-controlled helpers get one hour) | Five minutes |

Once a subscription draws on usage credits, the main conversation drops
to five minutes unless you set the TTL yourself.

## TTL controls and precedence

Each control takes `5m` or `1h`; Claude Code ignores other values. The
variables and settings need Claude Code v2.1.242 or later.

- Main conversation: `CLAUDE_CODE_PROMPT_CACHE_TTL` or the
  `promptCacheTtl` setting.
- Everything else: `CLAUDE_CODE_SUBAGENT_PROMPT_CACHE_TTL` or the
  `subagentPromptCacheTtl` setting.

First match wins:

1. `FORCE_PROMPT_CACHING_5M=1`: five minutes for both buckets. Use it
   to debug cache behavior, compare TTLs, or override a managed TTL.
1. The bucket's environment variable.
1. The bucket's setting.
1. For a subagent, `cacheTtl` in its `experimental` frontmatter field
   (v2.1.248 or later; a `1h` is ignored while a subscription uses
   usage credits).
1. `ENABLE_PROMPT_CACHING_1H=1`: one hour for both buckets.
1. The bucket default.

## Write cost versus idle misses

A one-hour write costs 2x the input price; a five-minute write costs
1.25x. The one-hour TTL pays only when the work idles longer than five
minutes and less than an hour, so that a five-minute cache would expire
and the next request would write the prefix again. Short bursts that
never idle past five minutes pay the higher write rate for nothing.

Per million tokens, with `W` the tokens a session writes to cache, `S`
the prefix size at an idle gap, and `g` the number of such gaps:

```text
extra cost of 1h   = W × (P_write_1h − P_write_5m)
saving from 1h     = g × S × (P_write_5m − P_hit)
1h pays when       g > W × (P_write_1h − P_write_5m)
                       / (S × (P_write_5m − P_hit))
```

Example with illustrative numbers on Sonnet 5.5: `W = 0.4`, `S = 0.15`.
The extra cost is 0.4 × (4 − 2.50) = $0.60; each avoided miss saves
0.15 × (2.50 − 0.20) = $0.345. Two or more idle gaps of 5 to 60 minutes
in the session make the one-hour TTL cheaper. Subagents that run to
completion without pauses rarely have such gaps; a subagent that waits
on a long tool run or on a teammate may.

Measure before you keep a non-default TTL: run the same work with each
setting and compare cache writes and cost.

## Verify the TTL

For the main conversation:

```sh
claude -p "hello" --output-format json
```

Read `usage.cache_creation` in the result: one-hour writes appear under
`ephemeral_1h_input_tokens`, five-minute writes under
`ephemeral_5m_input_tokens`. The docs give this check for the main
conversation. For subagents, compare cost and cache writes over the
same work under each setting, and check the `/usage` plan breakdown,
which flags cache misses when they account for 10% or more of recent
usage.

In an interactive session, `/usage` shows a `Prompt cache (main)` line
with the hit ratio and miss count (v2.1.251 or later). A high
read-to-creation ratio means the cache works; creation that stays high
turn after turn means something in the prefix keeps changing.

## Sources

- Claude Code prompt caching:
  <https://code.claude.com/docs/en/prompt-caching>
- Claude Code costs and `/usage`: <https://code.claude.com/docs/en/costs>
- Commands: <https://code.claude.com/docs/en/commands>
- Pricing (cache multipliers):
  <https://platform.claude.com/docs/en/about-claude/pricing>
