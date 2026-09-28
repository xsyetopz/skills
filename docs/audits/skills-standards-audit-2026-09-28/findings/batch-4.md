# Batch 4 findings

Skills: build-and-debug-pcsx2, debug-duckstation,
debug-software-failures, find-vulnerabilities,
analyze-scientific-papers, configure-ci-cd-pipelines,
remove-unneeded-compatibility-code.

## build-and-debug-pcsx2

No findings.

## debug-duckstation

No findings.

## debug-software-failures

- **consider** [SC-03] scripts/ddmin.py:132-136: on an unreadable
  `input` file the error is `error: {error}` (for example
  `error: [Errno 2] No such file or directory: '/no/such.txt'`), with
  no "expected" or "try" clause, unlike the same script's own
  `--oracle` and oracle-launch errors a few lines later ("check the
  command and its path") and unlike sibling skills' checkers (for
  example `find-vulnerabilities/scripts/check_findings.py`: "expected
  a Markdown review with '### F<n>: title' findings"). Fix: append
  what is expected, e.g. "; pass a readable UTF-8 input file".

## find-vulnerabilities

No findings.

## analyze-scientific-papers

- **consider** [FL-03] SKILL.md:86-89: the References section is two
  bare links (`- [Search and identity](references/search-and-identity.md)`)
  with no content summary or load condition, unlike every other
  skill's References section in this batch (for example
  `find-vulnerabilities/SKILL.md`'s "[Review method]: scope, boundary
  map, tracing, ...") and unlike this same skill's own reference
  files, which open with a one-line purpose statement. Fix: add a
  short summary of each file's cards, matching the sibling skills.

## configure-ci-cd-pipelines

- **consider** [FL-03] SKILL.md:102-106: the References section lists
  three bare titles (`- [GitHub Actions](references/github-actions.md)`)
  with no content summary or load condition, unlike the rest of this
  batch's References sections and unlike this skill's own
  `references/*.md` files, each of which opens with a purpose line.
  Fix: add a short summary of each file's cards, matching the sibling
  skills.

## Batch patterns

1. This batch is close to conformant: six of seven skills have no
   findings, every quoted command in every `SKILL.md` resolved to a
   real path and flag, and running the offline `verify.sh` (or
   equivalent) for build-and-debug-pcsx2, debug-software-failures, and
   find-vulnerabilities passed cleanly.
1. Both real findings are narrow misses against a pattern the rest of
   the batch (and, in one case, the skill's own reference files)
   already follows: a bare References section in two skills, and one
   error message missing the "what to try" clause its neighbors in the
   same file already use.
1. `scripts/*.py --help` texts are uniformly strong across all seven
   skills: usage, exit-code tables with meanings, stdout/stderr
   contract, and copy-pasteable examples, and bad-input runs almost
   always produced a specific, actionable error (the one exception is
   the debug-software-failures finding above).
</content>
