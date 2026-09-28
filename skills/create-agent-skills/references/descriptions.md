# Descriptions and triggering

Before choosing a skill, the model sees only its name and description
(plus `when_to_use` in Claude Code). These cards cover writing the
description and testing its selection.

## Contents

- Overlap check before creating
- Description structure
- Trigger vocabulary
- Boundary clause
- Length budget across a catalog
- Triggering evaluation

## Overlap check before creating

**Definition.** Before adding a new skill, search installed skills and the
catalog for the trigger words and scope it would claim. If an existing
skill already owns that responsibility, extend it (a new card, a routing
row, a wider description) instead of creating a second skill that competes
for the same request.

**Use when.** Every new skill, before naming it or writing its
description.

**Do not use when.** The candidate skill targets a genuinely different
task that only shares a few keywords with an existing one; then write both
descriptions with a boundary clause instead of merging unrelated work.

**Example.** A request for "review this GitHub Actions workflow" could
plausibly load `configure-ci-cd-pipelines` or a new "audit-yaml-pipelines"
skill. Search first
(`rg -il 'github actions|pipeline|workflow' skills/*/SKILL.md`); finding
`configure-ci-cd-pipelines` already covers triggers and token permissions,
add the audit content there instead of a second skill.

**Cost removed.** Two skills with overlapping descriptions, so the agent
loads the wrong one or both for the same request.

**Verify.**

1. `rg -il '<candidate trigger words>' skills/*/SKILL.md` finds no
   existing skill claiming the same scope, or the existing skill's
   description already excludes it with a boundary clause.

## Description structure

**Definition.** One third-person paragraph stating what the skill does
(concrete verbs and objects) and when to use it (the situations and terms
a user would mention) ([best practices][anthropic-bp],
[optimizing descriptions][optimizing]). Anthropic: "Always write in third
person", because the description is injected into the system prompt.

**Use when.** Writing or revising any description. Apply three checks:

- Front-load: the concrete verb, the object, and the main trigger words
  sit in roughly the first 100 characters. OpenAI: "Front-load the key
  use case and trigger words" ([build skills][codex-skills]). Over the
  listing budget, Codex first shortens every description, keeping its
  opening ([render.rs][codex-render]); the length budget card has the
  details.
- Say when: an explicit "Use when ..." sentence after the "what" part,
  naming the situations and terms users type.
- Name the neighbor: a closing "Not for ..." clause (boundary clause card).

**Do not use when.** Never write "I can help", "You can use this", or
generic claims ("expert", "comprehensive", "best practices"). They carry
no routing signal, and an inconsistent point of view causes discovery
problems ([best practices][anthropic-bp]).

**Example.**

```yaml
description: >-
  Profiles and optimizes C#/.NET CPU time, latency, and allocations with
  BenchmarkDotNet, dotnet-counters, dotnet-trace, and JIT disassembly. Use
  when a .NET benchmark or profile shows the cost. Not for framework
  upgrades alone.
```

The first 100 characters ("Profiles and optimizes C#/.NET CPU time,
latency, and allocations with BenchmarkDotNet") carry the verb, the
object, and the tool name users type.

**Cost removed.** Missed activations (false negatives) and wrong
activations (false positives).

**Verify.**

1. From the description alone, list three user requests it should match
   and one it must not. If you cannot, it is too vague.
1. Cut the description at 100 characters; the verb, object, and main
   trigger words are still there.
1. Run the triggering evaluation below.

## Trigger vocabulary

**Definition.** The nouns, tool names, file types, and error words users
actually type for this task (`BenchmarkDotNet`, `.csproj`, `allocations`,
`GC pauses`).

**Use when.** The skill targets a specific ecosystem or artifact.

**Do not use when.** Never add unrelated keywords to raise activation;
they add false positives and push other skills out of the listing
budget.

**Example.** For a justfile skill: `justfile`, `just recipes`, `recipe
parameters`, `dependencies`, `set shell`, `dotenv`. Not: `Makefile`,
`build system`, `CI` (neighboring tasks).

**Cost removed.** Requests phrased with tool names that fail to match a
description written in abstract terms.

**Verify.**

1. Every trigger word appears in at least one eval prompt, and no eval
   prompt for a neighboring skill matches only on these words.

## Boundary clause

**Definition.** A final "Not for ..." clause naming the neighboring task
most likely to be confused with this one.

**Use when.** Another skill in the catalog, or a common adjacent request,
shares vocabulary (optimize-csharp-code versus a framework upgrade;
write-readable-code versus performance work).

**Do not use when.** Listing every non-goal; name only the one or two
nearest neighbors.

**Example.** `Not for replacing a working build system or inventing a task
format.`

**Cost removed.** Two skills loading for one request, or the wrong
one.

**Verify.**

1. The near-miss eval (a request for the neighboring task) does not select
   the skill.

## Length budget across a catalog

**Definition.** Descriptions share a listing budget. Claude Code caps each
combined `description` + `when_to_use` at 1,536 characters and budgets the
listing at 1% of the context window; on overflow it drops whole
descriptions, least-invoked skills first, and keeps every name
([Claude Code skills][cc-skills]). Codex budgets 2% of the context window
in tokens, or 8,000 characters when the window is unknown; a configured
`max_context_tokens` (at most 10,000) takes precedence. Over budget, Codex
shortens descriptions round-robin, then removes them, then omits skills,
and says so in the list
([render.rs][codex-render]).

**Use when.** A catalog has more than a handful of skills.

**Do not use when.** Shortening would remove trigger words; cut
adjectives and duplicated scope first.

**Example.** This catalog's 44 descriptions total about 10,400
characters, above Codex's 8,000-character fallback. Each puts the key use
case first, so a shortened or dropped description loses the least.

**Cost removed.** Truncated descriptions that lose their trigger words.

**Verify.**

1. Sum the description lengths (folded YAML, so the count includes
   indentation and is an upper bound):

   ```sh
   for f in skills/*/SKILL.md; do
     awk '/^---$/{n++} n==1&&/^description:/{f=1;next}
          n==1&&f&&/^[a-z-]+:/{f=0} n==1&&f' "$f"
   done | wc -c
   ```

1. In Claude Code, `/context` reports the listing's size after the budget
   is applied; `/doctor` estimates its cost and names the largest
   contributors.

## Triggering evaluation

**Definition.** Realistic prompts, each labeled "should trigger" or
"should not trigger", run on the target host with the full catalog
installed, recording which skills actually load
([optimizing descriptions][optimizing]).

**Use when.** After writing or changing a description, and before
publishing a catalog change.

**Do not use when.** Never substitute a keyword match or your own reading
for a host run; selection is model behavior and must be observed.

**Example.** Store the queries in `evals/eval_queries.json`, a JSON list
of objects with `query` (string), `should_trigger` (boolean), `split`
(`"train"` or `"validation"`), and, on negatives, an optional
`expected_skill` naming the neighbor that should fire instead. The source
recommends about 20 queries, 8-10 that should trigger and 8-10 that
should not, with near-misses (shared keywords, different task) as the
negatives, and a fixed split of about 60% train and 40% validation with
both labels in each ([optimizing descriptions][optimizing]). Every skill
in this catalog uses 20 queries: 10 positive and 10 negative, 12 train
(6 and 6) and 8 validation (4 and 4). Vary positives by phrasing,
explicitness, detail, and complexity; revise the description only from
train failures, and pick the version with the best validation pass rate.

```json
[
  {"query": "our API allocates too much in LogParser.Parse, fix it",
   "should_trigger": true, "split": "train"},
  {"query": "upgrade the solution from net8.0 to net10.0",
   "should_trigger": false, "split": "validation"},
  {"query": "our Rust parser allocates a Vec per line, speed it up",
   "should_trigger": false, "split": "train",
   "expected_skill": "optimize-rust-code"}
]
```

**Cost removed.** Descriptions tuned to one phrasing.

**Verify.**

1. Counts per label and split match the plan:
   `jq -r '.[] | "\(.should_trigger) \(.split)"' evals/eval_queries.json
   | sort | uniq -c`.
1. Each run records host, version, model, and installed catalog, and
   reports false positives and false negatives separately.

[anthropic-bp]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
[optimizing]: https://agentskills.io/skill-creation/optimizing-descriptions
[cc-skills]: https://code.claude.com/docs/en/skills
[codex-skills]: https://learn.chatgpt.com/docs/build-skills
[codex-render]: https://github.com/openai/codex/blob/e72da2b/codex-rs/ext/skills/src/render.rs
