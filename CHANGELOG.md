# Changelog

All notable changes to this project are documented in this file.

The format is based on
[Keep a Changelog](https://keepachangelog.com/en/2.0.0/). The project has
no released versions yet.

## [Unreleased]

### Added

- `plan-implementation` writes implementation plans and reviews existing
  plans for flaws with one set of cards and both bundled checkers.
- `debug-software-failures` takes a failure of unknown cause from a strict
  reproduction through optional reduction and `git bisect` to a root cause
  and a regression test, with a fast path for crashes whose backtrace
  already names the fault.
- `write-readable-code` restructures code for readers and reviews it
  against the Zen of Python (PEP 20) in any language.
- Every skill has trigger queries (`evals/eval_queries.json`, 20 per skill
  with a fixed train and validation split) and output evals
  (`evals/evals.json`) with fixtures and deterministic checks.
- `just eval-triggers` and `just eval-outputs` run those evals in isolated,
  sandboxed Claude Code sessions and write agentskills.io-style results
  under `.evals/`.
- Bundled checkers accept `--json`; scanners accept `--limit`; `mutate.py`
  accepts `--list` for a dry run.

### Changed

- Skill descriptions state what the skill does, then when to use it, then
  what it is not for, in the third person.
- `SKILL.md` bodies and reference cards use plain, direct prose, and every
  code-skill card has a fenced example.
- Renamed `build-and-debug-duckstation` to `debug-duckstation`,
  `optimize-typescript-code` to `optimize-typescript-builds`,
  `design-system-architecture` to `design-software-architecture`, and
  `test-implementation-behavior` to `write-behavior-tests`. The old names
  are not kept as aliases.
- Sublime Text examples are type-checked against the skill's bundled host
  fakes instead of root stubs.
- Shared Markdown lint rules live in `.markdownlint.jsonc`, which
  `.markdownlint-cli2.jsonc` extends.

### Removed

- `write-implementation-plans` and `find-implementation-plan-flaws`; use
  `plan-implementation`.
- `reproduce-software-bugs`, `find-regression-commits`, and
  `diagnose-software-failures`; use `debug-software-failures`.
- `apply-pep20-to-codebases`; use `write-readable-code`.

### Fixed

- Reference cards no longer claim that `return cond ? a : b;` moves in
  C++, that `quote(args)` forwards `just` variadic arguments separately, or
  that release-mode `#[inline]` matches LTO in Rust; the Java integer-cache
  card explains why `AutoBoxCacheMax` did not apply.
- Bundled scripts exit with a usage error instead of a traceback on
  missing or malformed input, and fix `unittest discover` handling in
  `audit_plan_claims.py`, short `--max` versions in `wasm_api_version.py`,
  missing paths in `scan_secrets.py`, and `r` of ±1 in `check_stats.py`.
