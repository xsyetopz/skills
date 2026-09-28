# Batch 6 findings

Skills: create-agent-skills, write-agents-md, write-behavior-tests,
write-readable-code, manage-git-changes, manage-git-hosting.

## create-agent-skills

No findings beyond the comparison below. Its bundled tool
(`scripts/check_reference_structure.py`), evals (6 cases, 20 queries,
10/10 split), `agents/openai.yaml`, and every quoted command checked
out.

## create-agent-skills vs sources

This skill is the catalog's own authoring guide, so gaps here mean the
catalog has no documented rule to follow, not just one skill missing a
rule.

- **fix** [EV-05] references/evaluation.md, descriptions.md: neither
  file names `evals/eval_queries.json`, its `{query, should_trigger,
  split}` shape, or the ~20-query, 8-10/8-10 positive/negative,
  near-miss-heavy split that all 40 catalog skills actually use. The
  "Triggering evaluation" card only describes ad hoc `{"prompt":
  ..., "should_trigger": ...}` pairs run on a host, with no file name
  or split ratio. An author following only this skill would not
  create the file every other skill in the catalog has. Fix: add a
  card (or extend "Triggering evaluation") naming
  `evals/eval_queries.json`, its fields, and the 8-10/8-10 split with
  near-miss negatives.
- **fix** [FM-07] references/descriptions.md: "Description structure"
  and "Trigger vocabulary" never state the front-load rule (key use
  case and trigger words in the first ~100 characters). The only
  mentions are one clause in `SKILL.md`'s workflow step 6 ("key use
  case first") and an aside in "Length budget"'s Example ("Each puts
  the key use case first, so a shortened or dropped description loses
  the least") — neither is phrased as an actionable rule with the
  character budget. Given this catalog's own name+description total
  is 10,343 characters (over Codex's 8,000-character fallback, per
  "Length budget across a catalog"), front-loading is exactly the
  mitigation FM-07 exists for, and the reference that owns description
  writing never teaches it as a check. Fix: add a bullet to
  "Description structure" or "Length budget across a catalog": put the
  concrete verb, object, and main trigger nouns in the first ~100
  characters, since a Codex-truncated description keeps only that
  prefix.
- **consider** [SC-05, SC-06, SC-10] references/executable-resources.md,
  package-format.md: the script guidance covers exit codes, error
  messages, unexplained constants, `--help`, disposable-copy
  verifiers, and plan-validate-execute, but never states that output
  should be bounded by default (SC-05), that dependencies should be
  declared inline (PEP 723) or documented with local-only installs
  (SC-06), or that network calls must match the skill's stated purpose
  (SC-10). These are checked mechanically against the catalog's own
  scripts, but an author writing a new skill from this guide alone has
  no card telling them to do it. Fix: add short "Use when" bullets for
  these three to "Deterministic helper script" or a new card.
- **consider** [SC-08] references/package-format.md:284-286: "Host
  discovery and invocation"'s own example command, `bunx skills add
  https://github.com/xsyetopz/skills`, is unpinned, and no card
  anywhere states the "pin one-off command versions" rule
  (`bunx pkg@1.2.3`) that the checklist expects. The one worked
  example an author is likely to copy models the opposite of the rule.
  Fix: pin the example (`bunx skills@<version> add ...`) if a version
  exists, and add the pinning rule to "Scripts: execute or read" or
  "Deterministic helper script".
- **consider** [NM-03] references/package-format.md "Name",
  audit-and-rewrite.md: naming guidance covers style (action-oriented,
  gerund) and avoiding vague names, and "Overlap check" covers
  duplicate scope, but no card asks whether a skill's own scope is
  coherent and neither too narrow nor too broad (for example, a skill
  that bundles two unrelated ecosystems, or one construct dressed up
  as a whole skill). Fix: add a "Do not use when" line to "Name" or a
  short card cross-referencing "Choosing constructs" for scope size.
- **consider** [FL-03] references/package-format.md "References one
  level deep": teaches linking every reference directly from
  `SKILL.md` but never asks for a load condition per reference (`Read
  X when …`). `create-agent-skills`' own `## References` section lists
  only topic nouns per file, e.g. "Package format
  (references/package-format.md): layout, frontmatter, names,
  disclosure budget, ...", with no "read when" clause; its routing
  table compensates by mapping symptoms to card anchors, but the
  bottom-of-file list, taken alone, does not say when to open each
  file. `write-readable-code` in this same batch shows the alternative
  ("Function shape ...: read when restructuring a function; ..."),
  so the pattern is achievable and inconsistently taught. Fix: either
  add "read when ..." to each `## References` bullet in this skill's
  own `SKILL.md`, or state in "References one level deep" that a
  routing table alone satisfies the load-condition requirement.

## write-agents-md

- **consider** [FL-03] SKILL.md:92-99: the `## References` bullets
  list only topics ("commands, project map, conventions, boundaries,
  ...") with no "read when" clause, unlike `write-readable-code`'s
  references in this batch. The routing table above it does the same
  job by symptom, so this is a style gap, not a missing load
  condition.

No other findings: `scripts/check_instructions.py --help` has exit
codes and examples; a missing file gives "error: /no/such/AGENTS.md is
not a file; pass instruction files such as AGENTS.md"; evals (5 cases,
20 queries, 10/10 split) match the catalog shape.

## write-behavior-tests

- **consider** [FL-03] SKILL.md:113-120: `## References` is a bare
  link list with no per-file summary or load condition at all (not
  even a topic list), relying entirely on the "Route the task to a
  card" table and the per-card footnote links above it. Readable, but
  a reader who only opens `## References` gets no hint which file
  covers what.

No other findings: `scripts/mutate.py --help` and its bad-input path
are solid; `assets/examples/verify.sh verify` passes 11 checks
including the expected ASan abort; evals (5 cases, 20 queries, 10/10
split) match the catalog shape.

## write-readable-code

No findings. `## References` gives a "read when ..." clause per file,
matching the checklist's FL-03 intent better than the other five
skills in this batch. `scripts/python_function_metrics.py`,
`term_report.py`, and `zen_scan.py` all have solid `--help` and error
text; `assets/examples/readable/verify.sh all` and
`assets/examples/zen-of-python/verify.sh` both pass; evals (5 cases,
20 queries, 10/10 split) match the catalog shape.

## manage-git-changes

- **consider** [FL-03] SKILL.md:82-91: `## References` lists only
  topics per file, no "read when" clause, same pattern as
  write-agents-md.

No other findings: `assets/examples/verify.sh` passes 16 checks
against disposable repositories with isolated Git config; evals (6
cases, 20 queries, 10/10 split) match the catalog shape.

## manage-git-hosting

- **consider** [SC-03] scripts/sync_labels.py, upsert_comment.py: a
  missing input file gives the bare `error: [Errno 2] No such file or
  directory: '/no/such.json'` (and the equivalent for
  `upsert_comment.py`'s `BODY_FILE`), with no "expected" or "try"
  guidance, unlike `write-agents-md/scripts/check_instructions.py`'s
  "pass instruction files such as AGENTS.md" or
  `write-readable-code/scripts/python_function_metrics.py`'s "pass
  Python files or directories" in this same batch. Fix: catch the
  `OSError`/`FileNotFoundError` and append what the argument should be
  (a labels JSON file; a Markdown comment body file).
- **consider** [FL-03] SKILL.md:84-89: `## References` is a bare link
  list with no topic or load condition, same pattern as
  write-behavior-tests.

No other findings: `scripts/sync_labels.py --help` and
`upsert_comment.py --help` both have exit codes and examples;
`assets/verify.sh` passes 1 check (9 unittest cases against a fake
`gh`); evals (5 cases, 20 queries, 10/10 split) match the catalog
shape.

## Batch patterns

1. All six skills are close to conformant: consistent third-person
   descriptions with a front-loaded key use case and a "Not for ..."
   boundary, working `--help` texts with exit codes and examples on
   every audited script (except the two `error:` messages noted
   above), and verifiers that actually pass when run.
1. `## References` sections split into three styles within this one
   batch: a per-file "read when ..." clause
   (write-readable-code), a bare topic list (write-agents-md,
   manage-git-changes, create-agent-skills), and a bare link list with
   neither (write-behavior-tests, manage-git-hosting). The checklist's
   FL-03 wants the first style; the routing tables above each
   `## References` section carry the same information by symptom
   instead, so these are style inconsistencies rather than missing
   information, but create-agent-skills — the skill that should teach
   this — never states which style satisfies the rule.
1. The bare-errno error style (`[Errno 2] No such file or
   directory: ...`) recurs in exactly the two scripts
   (`manage-git-hosting`) that pass a file path straight to `open()`
   without a wrapping `try`/`except`, while every other script in this
   batch that takes a file argument (write-agents-md,
   write-readable-code, write-behavior-tests) wraps the read and
   states what the argument should have been.
1. create-agent-skills' own reference material is strong on what it
   covers (frontmatter, disclosure budget, naming, exit-code
   contracts, plan-validate-execute, evals.json, paired evaluation),
   but is missing or thin on several rules the catalog's other 39
   skills already follow in practice: the `eval_queries.json`
   trigger-query convention, front-loading as a stated rule, and
   several script-quality checklist items (bounded output,
   dependency policy, network-call justification, version pinning in
   one-off commands). An author who followed only this skill's
   references would produce a skill that is spec-valid but misses
   catalog conventions the mechanical checks and this audit otherwise
   rely on.
