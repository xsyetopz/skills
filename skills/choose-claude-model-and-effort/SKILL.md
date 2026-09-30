---
name: choose-claude-model-and-effort
description: >-
  Chooses the Claude model, effort, and cache TTL for a session, subagent,
  claude -p run, or API call. Use when picking Opus or Sonnet, setting effort
  or subagent frontmatter, or on usage limits.
---

# Choose Claude Model and Effort

Pick a model and an effort level from what a run costs and what the task
needs, then set them where they take effect. Prices, model IDs, and
defaults below come from the official docs as checked on 2026-09-30.
They change: confirm them on the linked pages before you quote a number.
Never state a benchmark gap, a limit multiplier, or a savings figure
that you did not measure or read in a primary source.

## Workflow

1. Name the unit of work: the main session, one subagent type, a batch
   of headless runs, or an API request. Each has its own control
   ([where to set it][where]).
1. Confirm current model IDs on the [models overview][overview] and
   prices on the [pricing page][pricing]; both change.
1. Classify the task shape (see below), pick a starting model, and
   estimate the cost from real token counts ([cost formula][formula]).
1. Pick a starting effort from the model's default and the task
   ([effort levels][levels]), then set model and effort in the one place
   that applies and check what overrides it ([precedence][precedence]).
1. For a batch or a new configuration, run a small sample first and
   measure tokens and plan-limit use
   ([measure a batch][batch]).

## Current models

| Model | API ID | Claude Code alias |
| --- | --- | --- |
| Claude Fable 5.1 | `claude-fable-5-1` | `fable` |
| Claude Opus 5.5 | `claude-opus-5-5` | `opus` |
| Claude Sonnet 5.5 | `claude-sonnet-5-5` | `sonnet` |
| Claude Haiku 4.5 | `claude-haiku-4-5` (`claude-haiku-4-5-20251001`) | `haiku` |

The overview lists Haiku 4.5 retirement as not sooner than October 15,
2026. Check the models overview page before you hard-code any ID.

## Prices

US dollars per million tokens, from the pricing page, checked
2026-09-30:

| Model | Input | 5m cache write | 1h cache write | Cache hit | Output |
| --- | --- | --- | --- | --- | --- |
| Fable 5.1 | 10 | 12.50 | 20 | 0.25 | 50 |
| Opus 5.5 | 4 | 5 | 8 | 0.20 | 20 |
| Sonnet 5.5 | 2 | 2.50 | 4 | 0.20 | 10 |
| Haiku 4.5 | 1 | 1.25 | 2 | 0.10 | 5 |

Opus 5.5 reads cache at 0.05x its input price, so its cache hit costs
the same as Sonnet 5.5's. Batch API, data residency, and fast mode
change these rates ([modifiers](references/prices-and-cost.md#price-modifiers)).

## Economics

An agent session re-sends its whole conversation on every request, so
the cached prefix is read again each turn. In a long run, cache-read
tokens usually outnumber input, write, and output tokens; confirm it in
your own `usage` fields. Because Opus 5.5 and Sonnet 5.5 read cache at
the same price, that large share costs the same on both. The difference
comes from output tokens (Opus costs twice as much per output token),
cache writes and uncached input, and correctness: a wrong answer that
needs a second run or a human fix costs more than the price gap.

```text
cost = input × P_in + write_5m × P_w5 + write_1h × P_w1
     + cache_read × P_hit + output × P_out        (tokens in millions)
```

A worked example and a break-even check are in
[prices and cost](references/prices-and-cost.md#worked-example).

## Task shape

Reason from the task; do not quote benchmark numbers you have not
checked.

- Well-scoped slice (named files, a clear interface, a test that says
  done): try Sonnet 5.5 first. The spec carries most of the judgment,
  and a check catches a miss cheaply.
- Open-ended debugging, design, or review with no clear stopping test:
  start with Opus 5.5. A wrong direction here costs more than the
  output-price difference.
- Fable 5.1 costs 2.5 times Opus 5.5 per input and output token. Keep it
  for work where an Opus attempt failed or the stakes justify it.
- Haiku 4.5: short, mechanical, high-volume steps with a cheap check.
- On a hard task a cheaper model can spend more output tokens (retries,
  long reasoning) and lose its price advantage. Compare the output
  tokens of both runs, not only the rate.
- Compare any benchmark or local trial only at equal effort. A result at
  `max` against another model at `xhigh` measures effort as well as the
  model.

## Effort

Levels: `low`, `medium`, `high`, `xhigh`, `max`. Per the effort docs,
most models default to `high`; Opus 5.5 defaults to `medium`. Fable 5.1,
Opus 5.5, and Sonnet 5.5 support all five. The effort page does not list
Haiku 4.5 among supported models: check the docs before you set effort
for it. Not every model that supports `max` supports `xhigh`.

Where to set it:

- API: `output_config.effort` on the request.
- Claude Code: `CLAUDE_CODE_EFFORT_LEVEL` (also `auto`), which overrides
  `--effort`, `/effort`, and the `effortLevel` and `modelSettings`
  settings; a `maxEffortLevel` cap still applies.
- Subagent: the `effort` frontmatter field, which overrides the session
  level for that subagent; it inherits the session level when omitted.

Raise effort one level at a time and compare output tokens and results
on the same task. On Opus 5.5, Sonnet 5.5, and Fable 5.1 with an API key
or a subscription, changing effort mid-session keeps the prompt cache;
on most other models it does not
([cache effects](references/effort-and-settings.md#cache-effects-of-switching)).

## Main session plans, subagents do slices

Run the stronger model in the main session to plan, split work, and
review results. Give well-scoped slices to subagents on a cheaper model:

```markdown
---
name: slice-implementer
description: Implements one planned slice with its named tests.
model: sonnet
effort: medium
---
```

`model` takes `sonnet`, `opus`, `haiku`, `fable`, a full ID, or
`inherit`. A per-invocation `model` parameter overrides the frontmatter
([model order](references/effort-and-settings.md#subagent-model-order)).
Review each slice in the main session before merging it.

## Headless runs and plan limits

No official statement says how `claude -p` or Agent SDK runs count
against subscription limits compared with interactive use. Before a
large batch, run a small representative batch and compare `/usage`
before and after
([method](references/limits-and-caching.md#measure-a-headless-batch)).

## Prompt cache TTL

Claude Code gives the main conversation a one-hour TTL on a subscription
within plan usage and five minutes otherwise; subagents and other
background requests get five minutes. Controls (v2.1.242 or later):
`CLAUDE_CODE_PROMPT_CACHE_TTL` for the main conversation (including
`-p` and the SDK), `CLAUDE_CODE_SUBAGENT_PROMPT_CACHE_TTL` for
subagents, and `FORCE_PROMPT_CACHING_5M=1` to force five minutes for
both. A one-hour write costs 2x input against 1.25x for five minutes; it
pays only when idle gaps between five and sixty minutes would otherwise
re-write the prefix. Verify which TTL applied with
`usage.cache_creation`
([TTL trade-off](references/limits-and-caching.md#prompt-cache-ttl)).

## Rules

- Quote prices, defaults, and IDs with the date and URL you checked;
  they change between model releases.
- Do not carry an effort setting from an older model: the effort docs
  say levels are recalibrated on newer models such as Sonnet 5.5, so
  the same name can mean a different amount of thinking.
- Compare models on the same task, the same effort, and the same
  prompt, and report output tokens with the result; a single run is an
  anecdote, not a benchmark.
- Treat a limit or cost claim from a forum, a thread, or memory as a
  hypothesis; measure it on a small batch before you plan around it.
- Switching model mid-session re-reads the whole conversation uncached;
  choose the model at the start of a session or at a natural break.

## Related skills

- `$create-agent-skills` for writing the skill or agent files that
  carry these settings.
- `$coordinate-phase-gated-subagents` for running multi-phase subagent
  deliveries that use the main-session and subagent split.
- For API integration code and SDK details, use the Claude API
  reference; this skill does not write prompts or client code.

## References

- [Prices and cost](references/prices-and-cost.md): price table,
  cache multipliers, modifiers, cost formula, worked example,
  break-even check.
- [Effort and settings](references/effort-and-settings.md): levels,
  defaults, API and Claude Code controls, precedence, subagent
  frontmatter and model order, cache effects of switching.
- [Limits and caching](references/limits-and-caching.md): measuring a
  headless batch against plan limits, TTL buckets and controls, the
  write-versus-idle-miss trade-off, verification.

## Completion evidence

The answer names the model and effort for each unit of work with its
reason, the file or variable that sets it, the prices and date quoted,
a cost estimate from the formula with its token counts (measured or
labeled as assumed), and any measurement step still to run.

[where]: references/effort-and-settings.md#where-to-set-effort
[overview]: https://platform.claude.com/docs/en/about-claude/models/overview
[pricing]: https://platform.claude.com/docs/en/about-claude/pricing
[formula]: references/prices-and-cost.md#cost-formula
[levels]: references/effort-and-settings.md#effort-levels
[precedence]: references/effort-and-settings.md#claude-code-precedence
[batch]: references/limits-and-caching.md#measure-a-headless-batch
