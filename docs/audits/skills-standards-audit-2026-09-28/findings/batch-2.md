# Batch 2 findings

Skills audited: optimize-python-code, optimize-rust-code,
optimize-scala-code, optimize-swift-code, optimize-typescript-builds,
migrate-js-tooling-to-bun, write-justfiles.

## optimize-python-code

No findings.

## optimize-rust-code

No findings.

## optimize-scala-code

No findings.

## optimize-swift-code

No findings.

## optimize-typescript-builds

No findings.

## migrate-js-tooling-to-bun

- **consider** [SC-02] `assets/examples/verify.sh`: the script reads no
  arguments at all, so `sh assets/examples/verify.sh --help` (or any
  unrecognized flag) silently runs the full 16-check offline suite
  instead of printing usage or failing. An agent probing the script's
  interface gets a multi-second full run with no explanation instead of
  guidance. Fix: reject an unrecognized argument with a usage line and a
  non-zero exit, matching the pattern already used by the optimize-\*
  skills' `verify.sh` scripts (usage message, exit 2).

## write-justfiles

- **consider** [SC-02] `assets/examples/verify.sh`: same gap as
  `migrate-js-tooling-to-bun` — no argument parsing, so an unrecognized
  argument (including `--help`) silently runs the full 39-check example
  suite. Fix: same as above.

## Batch patterns

- Every `SKILL.md` in this batch shares one template: a numbered
  Workflow, a "Route evidence/task to a construct/card" table, Rules,
  Bundled tools, References, and Completion evidence. Reference-file
  load conditions live in that routing table and the Workflow's numbered
  steps rather than a standalone "Read X when ..." sentence (FL-03).
  Judged compliant, consistent with the batch-1 finding: the condition
  is the routing-table row or workflow step itself, and every reference
  file carries a `## Contents` table of contents and is reachable from
  `SKILL.md` (checked in all seven skills, no orphans).
- `evals/eval_queries.json` is a fixed 10/10 split (not the ~60/40 the
  checklist's source describes) with near-miss negatives that name an
  `expected_skill` in every file checked. This matches the batch-1
  finding for the earlier seven skills, so it reads as a deliberate,
  catalog-wide convention rather than a per-skill defect.
- `agents/openai.yaml` `short_description` and `default_prompt` in all
  seven skills read as grammatical, complete sentences on direct
  inspection; an earlier context-compression pass in this review had
  garbled them into fragments ("Rust hot paths evidence") that were not
  present in the actual files. Noted here only so the next reviewer
  does not repeat the false alarm.
- Five of the seven bundled `assets/examples/verify.sh` scripts
  (optimize-python-code, optimize-rust-code, optimize-scala-code,
  optimize-swift-code, optimize-typescript-builds) print a usage line
  and exit 2 on an unrecognized mode argument, which is adequate
  SC-03 behavior even without a dedicated `--help` flag. The other two
  (see per-skill findings above) instead ignore all arguments and run
  their full default suite, which is the weaker case worth fixing.
