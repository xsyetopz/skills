# Skill standards audit summary

Date: September 28, 2026. Scope: all 40 skills under `skills/`, checked
against [checklist.md](checklist.md). Mechanical checks covered
frontmatter, body length, eval structure, `agents/openai.yaml`, script
`--help`, prompts, and orphans across the catalog. Six batch audits
judged the rest; their findings are in `findings/batch-1.md` to
`findings/batch-6.md`.

## Outcome

- No MUST violations. Every description is third person, states what and
  when, and front-loads verb, object, and trigger words.
- Catalog name plus description totals 10,343 characters, over Codex's
  8,000-character fallback (OA-04). Hosts shorten descriptions first, so
  front-loading (FM-07) is the mitigation; no description was cut.
- `plan-implementation` failed NM-02: the name did not cover reviewing
  plans. Renamed to `write-implementation-plans`, matching
  `write-behavior-tests`, `write-agents-md`, and `write-justfiles`, which
  also review and say so in their descriptions. A split into writer and
  reviewer skills was rejected: writing step 9 runs the review steps, and
  both procedures share one card table.
- `create-agent-skills` did not teach ten checklist rules (EV-05, FM-07,
  SC-05, SC-06, SC-08, SC-10, NM-03, FL-03, BD-05, BD-08). Its references
  now do.

## Fixed

| Finding | Location |
| --- | --- |
| FL-01 unresolved `<skill>/` path | `develop-intellij-platform-plugins/SKILL.md` |
| SC-02 `--help` without exit status or examples | `create-agent-hooks/assets/handlers/*.py` |
| SC-02 verifier ignores `--help` and unknown arguments | `migrate-js-tooling-to-bun`, `write-justfiles` `assets/examples/verify.sh` |
| SC-03 error without expected input | `check_hook_config.py`, `ddmin.py`, `check_gate.py`, `sync_labels.py`, `upsert_comment.py` |
| SC-03 traceback on unwritable target | `create-agent-hooks/scripts/merge_hooks.py` |
| FL-03 reference without load condition | `sources.md` in `optimize-csharp-code`, `optimize-typescript-builds` |
| NM-02 name misses half the job | `plan-implementation` renamed |
| Authoring guide gaps | `create-agent-skills` references |

## Judged conformant

- FL-03: every other reference file is linked from a routing-table row or
  workflow step that names its triggering symptom. The bottom
  `## References` lists are indexes, as `create-agent-skills` now states.
- EV-05: every skill has 20 trigger queries, 10 positive and 10 negative,
  split 12 train and 8 validation, which is the source's 60/40 split.
- BD-05: gotchas live in each `SKILL.md` `## Rules` section.
- Naming (NM-01): the catalog uses verb-noun names throughout; Anthropic
  prefers gerunds but requires one pattern, so no catalog-wide rename.

## Follow-ups

All three were resolved in a later change:

- `write-readable-code` body trimmed from 201 lines to 200 or fewer.
- The `create-agent-skills` trigger-query eval checks the `split` field
  and all four split and label combinations.
- `just hygiene` runs the `pre-commit-hooks` checks and `just secrets`
  runs gitleaks, both in `just validate` and the pre-commit hook.
