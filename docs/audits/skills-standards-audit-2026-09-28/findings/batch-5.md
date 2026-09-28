# Batch 5 findings

Skills: plan-implementation, define-requirements,
design-software-architecture, coordinate-phase-gated-subagents,
document-codebases, update-changelogs.

## plan-implementation

- **consider** [NM-03] SKILL.md:22-68: the body carries two full,
  separately numbered procedures ("Write a plan for an agreed change",
  9 steps, and "Review a plan", 7 steps) that share almost no steps,
  read different reference pairs (`plan-structure.md`/`delivery.md` to
  write, `flaw-types.md`/`review-method.md` to review), and lead with
  different bundled scripts (`check_plan.py` to write,
  `audit_plan_claims.py` to review). Every sibling skill in this batch
  that also names two verbs in its description (`design-software-
  architecture`: "Designs and reviews", `document-codebases`: "Writes
  and fixes", `update-changelogs`: "Adds and corrects") folds both
  into one numbered Workflow where the second verb is a step inside
  the first job, not a second procedure. This is a judgment call, not
  a clear violation, and it does not block the rename below either
  way. See the dedicated rename section for the naming half of this
  finding.

No other findings; `check_plan.py` and `audit_plan_claims.py` both
have accurate `--help` text (paths, flags, exit codes, examples all
checked), both fail cleanly on a missing file with an "expected"
clause, and every `assets/examples/` path named in `SKILL.md` exists.

## define-requirements

No findings. `check_requirements.py --help` and its missing-file error
both name the format expected; the five evals include a
requirement-choice edge case (Postgres vs. DynamoDB) that stays out of
scope by the "Not for architecture choices" boundary.

## design-software-architecture

No findings. `Designs and reviews` in the description names two verbs
but the body has one Workflow where "enforce it" (step 5) folds the
review half in as a step, not a second procedure — see the coherence
note under the rename section. `check_layers.py --help` and its
missing-file error are accurate; all three references are over 100
lines with a Contents list.

## coordinate-phase-gated-subagents

- **consider** [SC-03] scripts/check_gate.py: a missing `GATE.json`
  gives `error: cannot check /no/such.json: [Errno 2] No such file or
  directory: '/no/such.json'`, with no "expected" clause, while a
  malformed-but-present JSON file gets a fuller message from the same
  script (`error: missing key 'conditions'; expected {'conditions':
  [{'id': ...}]} and requirements with an 'id' (see --help)`) and its
  sibling `check_work_items.py` adds "; expected a work plan JSON
  object" to its own file-not-found error. Fix: append "; expected a
  gate evidence JSON object (see --help)" to the file-read error in
  `check_gate.py`.

Otherwise no findings: both scripts' `--help` texts are accurate, the
five evals include the non-phase-gated edge case (a same-file rename
that should be done directly, not through the ceremony), and both
reference files are single-workflow with Contents lists.

## document-codebases

No findings. `check_doc_commands.py`, `check_links.py`, and
`same_words.py` all have accurate `--help` text and clean, expected-
naming errors on bad input; the six evals include two near-miss
boundary cases (a CHANGELOG entry and a code-of-conduct request) that
correctly fall outside this skill's scope.

## update-changelogs

No findings. `draft_entries.py`, `audit_changelog.py`, and
`audit_semver.py` all have accurate `--help` text and clean errors on
bad input; `changelog_markdown.py` is an internal library imported by
the other two scripts, not an agent-facing tool, so its absence from
"Bundled tools" is not an FL-05 orphan. The five evals include a
near-miss (a README install section) that correctly falls outside this
skill's scope.

## Rename: plan-implementation

The user's premise holds: the skill both writes plans (9-step
procedure, `check_plan.py`, `plan-structure.md`/`delivery.md`) and
reviews them (7-step procedure, `audit_plan_claims.py`,
`flaw-types.md`/`review-method.md`), and `plan-implementation` as a
name only describes the first half. Someone scanning names for "which
skill critiques a plan" has no reason to land here.

**(a) One job or two.** By the letter of NM-03 ("one coherent job...
neither too narrow nor too broad") this is closer to two procedures
sharing a home than one integrated workflow. Every other dual-verb
skill in the catalog (`design-software-architecture`,
`document-codebases`, `update-changelogs`) makes the second verb a
step inside one Workflow; `plan-implementation` instead has two
Workflows with almost no shared steps and disjoint reference pairs. By
the agentskills.io best-practice reading ("skills scoped too broadly
become hard to activate precisely") and OpenAI's "one job per skill",
a case exists for splitting into a writer and a reviewer skill.

Against splitting: the two procedures share the same domain vocabulary
(task, dependency, done condition, rollback) and the same card table
(`## Route the situation to a card` serves both), and review is how a
plan-writer checks its own draft (step 9 of "Write a plan" calls back
into "Review a plan" steps 2-5). A reviewer needs to know how a
well-formed plan looks to judge one, so the two procedures read as a
single "plan quality" competency exercised from either end, similar to
how `document-codebases` folds writing and checking docs into one
flow. This audit does not resolve which reading is correct; it lays
out both so the maintainer can choose, and recommends the rename
either way because "plan-implementation" fails NM-02 (name covers the
whole job) under the current scope regardless of which reading wins.

**(b) Candidate names**, checked against the catalog's action-verb
pattern (every name in `skills/` is `<verb>-<noun...>`, no gerunds)
and Anthropic's naming guidance (gerund preferred, action-oriented
acceptable, consistency required across the collection):

1. `plan-and-review-implementation` — states both halves explicitly
   and stays in the catalog's verb-noun form, but at 30 characters it
   is one of the longest names in the catalog and the "and" reads
   awkwardly next to terser siblings like `design-software-
   architecture` (also compound, but a single noun phrase, not two
   verbs joined by "and").
1. `review-implementation-plans` — mirrors `design-software-
   architecture`'s pattern of using the "higher" verb (review implies
   having produced or received a plan) to cover both jobs, and matches
   length and shape with `define-requirements` and `document-
   codebases`. Risk: on its own, "review" undersells that the skill
   also produces plans from scratch, the same way "designs and
   reviews" undersells that `design-software-architecture` also
   originates designs — but the catalog already accepts that trade-off
   for that skill, so it is consistent, not novel.
1. `write-implementation-plans` — keeps the create half explicit and
   the terser length, but repeats the exact problem the user is
   raising: it would drop the review half from the name.

**Recommendation:** `review-implementation-plans` if the coherence
call is "one job" (write-then-review, same as `design-software-
architecture`'s "design-then-review" and `document-codebases`'s
"write-then-check"), because "review" is the verb that most naturally
implies both producing and judging a plan in this catalog's existing
usage, and it keeps the name inside the catalog's length and shape
norms. If the maintainer instead decides this is genuinely two jobs,
split into `write-implementation-plans` and `review-implementation-
plans` as two skills, moving `flaw-types.md`, `review-method.md`,
`audit_plan_claims.py`, and the `config-edits/` example into the new
review skill, and keep `check_plan.py`'s "unremoved marker" and
"vague verbs" checks with the writer (they gate a draft before review,
not after).

**(c) Every place a rename to `review-implementation-plans` (or a
split) would touch**, found by searching `skills/`, `evals/`,
`agents/openai.yaml`, `README.md`, `CHANGELOG.md`, and `scripts/` for
`plan-implementation`:

- `skills/plan-implementation/` — the directory itself (FM-01 requires
  `name` to equal the parent directory name).
- `skills/plan-implementation/SKILL.md:2` — the `name:` frontmatter
  field.
- `skills/plan-implementation/agents/openai.yaml` — `default_prompt`
  contains the literal token `$plan-implementation`; `display_name`
  ("Plan Implementation") should also change to match.
- `skills/plan-implementation/evals/evals.json:2` — `skill_name`, plus
  every `$R/skills/plan-implementation/scripts/...` path built inside
  the `check` shell snippets for each assertion (lines 21, 25, 80, 84
  and others; every assertion that locates the skill's scripts by
  walking up from `$EVAL_OUTPUTS_DIR`).
- `skills/coordinate-phase-gated-subagents/evals/eval_queries.json:66`
  — `expected_skill: "plan-implementation"` on a negative trigger
  case.
- `skills/define-requirements/evals/eval_queries.json:62,91` — two
  `expected_skill: "plan-implementation"` negative cases.
- `skills/design-software-architecture/evals/eval_queries.json:62` —
  one `expected_skill: "plan-implementation"` negative case.
- `CHANGELOG.md:13,58,68` — three prose mentions of
  `` `plan-implementation` `` describing what the skill does.
- `README.md` and `scripts/` (top-level repository scripts and
  `justfile`) — searched, no hits; neither hardcodes the skill name.
- No other skill's "Not for" boundary line names
  `plan-implementation` or "implementation plan" by name, so no
  cross-skill boundary text needs updating.

## Batch patterns

1. Every skill in this batch that names two verbs in its description
   (`plan-implementation`, `design-software-architecture`,
   `document-codebases`, `update-changelogs`) folds both into one
   Workflow except `plan-implementation`, which is the only one with
   two disjoint, separately numbered procedures and two disjoint
   reference pairs — this is what makes its name specifically the
   weak one, not the two-verb description pattern itself.
1. Bundled Python tools across all six skills are close to uniformly
   strong: every `--help` states usage, flags, exit codes, output
   shape, and runnable examples, and every missing-file case exits
   non-zero with the bad path named. The one inconsistency found
   (`check_gate.py`'s file-not-found error dropping the "expected"
   clause its own malformed-JSON error and its sibling script both
   have) is narrow and only surfaced by testing both failure modes of
   every script, not just one.
1. Every skill's evals include at least one deliberate near-miss or
   boundary case that exercises the "Not for" line in its own
   description (an architecture choice for `define-requirements`, a
   README section for `update-changelogs`, a CHANGELOG entry and a
   CLA request for `document-codebases`, a non-phase-gated rename for
   `coordinate-phase-gated-subagents`, an "implement it now" request
   for `plan-implementation`), so EV-03's edge-case requirement is
   consistently met by design, not by accident.
