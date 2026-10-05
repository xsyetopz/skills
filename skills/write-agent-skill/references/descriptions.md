# Descriptions and Triggering

## Contents

- [Not Selected](#not-selected)
- [Selected for Wrong Requests](#selected-for-wrong-requests)
- [Listing Budgets](#listing-budgets)
- [Trigger Evaluation](#trigger-evaluation)

## Not Selected

- The description names a category ("Python testing") instead of the words users type (`pytest`,
  fixtures, flaky test). Add those words to the first sentence.
- The trigger words sit at the end. Codex shortens descriptions from the end when the listing
  overflows, and readers weigh the opening most. Put the verb, the object, and the main tool names
  in the first 100 characters.
- There is no "Use when" sentence. Add one phrased as the user would phrase the request: "Use when
  tsc is slow or runs out of memory".
- The catalog has too many overlapping skills, so a neighbor wins. Merge them, or add a "Not for"
  clause to both.
- The host dropped the description to fit its budget. See the budgets below. Claude Code drops the
  least-invoked skills' descriptions first.

Quick check: ask the agent "When would you use the X skill?" It answers from the description. If the
answer is vague, so is the description.

## Selected for Wrong Requests

- Generic words such as "code", "quality", "best practices", or "expert" match everything. Remove
  them.
- Unrelated keywords were added to raise activation. Remove them. They also push other skills out of
  the listing.
- No boundary. Add "Not for" naming the one or two nearest neighbors, not every non-goal.
- Shouted wording in the description ("ALWAYS use this skill") makes several models load it for
  everything.

## Listing Budgets

Descriptions are always in context, so their total is a fixed cost on every turn.

- Claude Code caps each `description` plus `when_to_use` at 1,536 characters and budgets the whole
  listing at 1% of the context window. On overflow it drops descriptions of the least-invoked skills
  and keeps every name. `disable-model-invocation: true` removes a skill from the listing ([Claude
  Code skills][cc-skills]).
- Codex renders each skill as `- name: description (file: path)`. It budgets 2% of the context
  window, or 8,000 characters when the window is unknown. On overflow it shortens descriptions
  round-robin, then drops them, then omits skills ([render.rs][codex-render]). The Codex app UI
  shows `short_description` from `agents/openai.yaml` instead.
- The spec limit for one description is 1,024 characters ([specification][spec]). That is a ceiling,
  not a target.

A catalog larger than one budget needs more than short descriptions:

- Group skills into install bundles whose listing fits 8,000 characters, the Claude Code budget at a
  200k-token window and the Codex fallback. Most users install a bundle, not the whole catalog.
- Make niche skills manual-only (`disable-model-invocation: true`, and
  `allow_implicit_invocation: false` for Codex), so they cost no listing space.
- Offer one line per skill in the always-loaded AGENTS.md or CLAUDE.md that says when to use it in
  terms of the task, not a copy of its description, which the host already lists. In
  [Vercel's eval][vercel], a skill that went uninvoked in 56% of cases reached a trigger rate over
  95% once an AGENTS.md line said when to invoke it.
- Claude Code users who install many skills can raise `skillListingBudgetFraction` or set
  low-priority skills to `"name-only"` in `skillOverrides` ([Claude Code skills][cc-skills]).

## Trigger Evaluation

`eval_queries.json`, kept outside the installed skill directory, holds about 20 queries:

```json
[
  {"query": "tsc takes 90s on CI and I don't know why",
   "should_trigger": true, "split": "train"},
  {"query": "our Node API got slower after the upgrade",
   "should_trigger": false, "split": "validation",
   "expected_skill": "optimize-runtime-performance"}
]
```

- Use 10 should-trigger and 10 should-not queries, split 12 train and 8 validation, with both labels
  in each split ([optimizing descriptions][optimizing]).
- Vary positives by phrasing, explicitness, and detail. Make negatives near misses that share
  vocabulary with this skill but belong to a neighbor.
- Run each query several times on the target host with the full catalog installed. Aim for 80 to 90
  percent correct on both labels.
- Change the description only from train failures, and keep the version with the best validation
  score, so the description is not fitted to the test queries.

[cc-skills]: https://code.claude.com/docs/en/skills
[codex-render]: https://github.com/openai/codex/blob/e72da2b/codex-rs/ext/skills/src/render.rs
[spec]: https://agentskills.io/specification
[optimizing]: https://agentskills.io/skill-creation/optimizing-descriptions
[vercel]: https://vercel.com/blog/agents-md-outperforms-skills-in-our-agent-evals
