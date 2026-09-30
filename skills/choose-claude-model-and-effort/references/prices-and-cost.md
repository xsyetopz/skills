# Prices and cost

## Contents

- [Price table](#price-table)
- [Cache multipliers](#cache-multipliers)
- [Price modifiers](#price-modifiers)
- [Token counts to use](#token-counts-to-use)
- [Cost formula](#cost-formula)
- [Worked example](#worked-example)
- [Break-even check](#break-even-check)
- [Sources](#sources)

## Price table

US dollars per million tokens (MTok), from
<https://platform.claude.com/docs/en/about-claude/pricing>, checked
2026-09-30. Re-check the page before you quote a number.

| Model | Input | 5m cache write | 1h cache write | Cache hit | Output |
| --- | --- | --- | --- | --- | --- |
| Claude Fable 5.1 | 10 | 12.50 | 20 | 0.25 | 50 |
| Claude Opus 5.5 | 4 | 5 | 8 | 0.20 | 20 |
| Claude Sonnet 5.5 | 2 | 2.50 | 4 | 0.20 | 10 |
| Claude Haiku 4.5 | 1 | 1.25 | 2 | 0.10 | 5 |

## Cache multipliers

The pricing page defines cache prices relative to the base input price:

- 5-minute cache write: 1.25x input.
- 1-hour cache write: 2x input.
- Cache hit (and refresh): 0.1x input on most models, 0.05x on Opus 5.5,
  0.025x on Fable 5.1.

So Opus 5.5 and Sonnet 5.5 both read cache at $0.20 per MTok, although
Opus input costs twice as much. The pricing page states that at the
standard 0.1x hit rate caching pays off after one cache read for the
five-minute duration and after two reads for the one-hour duration.

## Price modifiers

These stack with the cache multipliers:

- Batch API: 50% off input and output (Opus 5.5 batch: $2 input,
  $10 output per MTok). Fast mode is not available with batches.
- Data residency: `inference_geo: "us"` multiplies every token category
  by 1.1 on Claude 4.6 and later models.
- Fast mode (research preview, Claude API only): Opus 5.5 at $8 input
  and $40 output per MTok.

Claude Code sessions billed by an API key use these rates. On a
subscription, the same tokens count against plan limits instead; see
[limits and caching](limits-and-caching.md#measure-a-headless-batch).

## Token counts to use

Take token counts from a real run, not from a guess:

- API responses: the `usage` object with `input_tokens`,
  `cache_creation_input_tokens`, `cache_read_input_tokens`, and
  `output_tokens`. `usage.cache_creation` splits writes into
  `ephemeral_5m_input_tokens` and `ephemeral_1h_input_tokens`.
- Claude Code headless: `claude -p "..." --output-format json` returns
  the same `usage` object in its result.
- Claude Code interactive: a status line script reads `current_usage`;
  `/usage` shows the session's cost and cache hit ratio.

Output tokens include thinking. The effort docs call `max_tokens` a
hard limit on total output, thinking plus response text, so a higher
effort level raises the output count you must price.

## Cost formula

With every token count in millions:

```text
cost = input      × P_input
     + write_5m   × P_write_5m
     + write_1h   × P_write_1h
     + cache_read × P_hit
     + output     × P_output
```

`input` here is uncached input only; the API reports cached reads and
writes separately from `input_tokens`.

## Worked example

The token counts below are illustrative, not a measurement. Replace
them with the `usage` totals of your own run.

| Tokens | Count (MTok) | Opus 5.5 | Sonnet 5.5 |
| --- | --- | --- | --- |
| Uncached input | 0.05 | 0.05 × 4 = 0.20 | 0.05 × 2 = 0.10 |
| 5m cache write | 0.40 | 0.40 × 5 = 2.00 | 0.40 × 2.50 = 1.00 |
| Cache read | 20.00 | 20 × 0.20 = 4.00 | 20 × 0.20 = 4.00 |
| Output | 0.15 | 0.15 × 20 = 3.00 | 0.15 × 10 = 1.50 |
| Total | | $9.20 | $6.60 |

The cache reads cost the same $4.00 on both models. The $2.60 gap comes
from output, writes, and uncached input, which is why output tokens and
the number of attempts decide the choice.

If Sonnet 5.5 used twice the output tokens on the same task (0.30 MTok,
$3.00), its total would be $8.10. Measure output tokens for both models
on the same task before you assume either one.

## Break-even check

A cheaper run is only cheaper if it does not need to be redone. With
`C_a` and `C_b` the cost of one run on each model and `r` the share of
runs on the cheaper model that need a full rerun:

```text
cheaper model wins while  C_b × (1 + r) < C_a
break-even rerun share    r = C_a / C_b − 1
```

For the example, `r = 9.20 / 6.60 − 1 ≈ 0.39`: Sonnet 5.5 stays cheaper
while fewer than about 39% of its runs need a rerun. The formula leaves
out review time and the cost of a wrong result that nobody catches;
add them when they apply. Estimate `r` from your own trials on the
same kind of task, at the same effort.

## Sources

- Pricing: <https://platform.claude.com/docs/en/about-claude/pricing>
- Effort (output limit includes thinking):
  <https://platform.claude.com/docs/en/build-with-claude/effort>
- Claude Code prompt caching (usage fields, `-p` JSON output):
  <https://code.claude.com/docs/en/prompt-caching>
- Claude Code costs (`/usage`): <https://code.claude.com/docs/en/costs>
