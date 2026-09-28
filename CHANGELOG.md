# Changelog

All notable changes to this project are documented in this file.

The format is based on
[Keep a Changelog](https://keepachangelog.com/en/2.0.0/). The project has
no released versions yet.

## [Unreleased]

### Added

- `write-implementation-plans` writes implementation plans and reviews
  existing plans for flaws with one set of cards and both bundled checkers.
- `debug-software-failures` takes a failure of unknown cause from a strict
  reproduction through optional reduction and `git bisect` to a root cause
  and a regression test, with a fast path for crashes whose backtrace
  already names the fault.
- `apply-semantic-versioning` covers all of Semantic Versioning 2.0.0,
  including pre-release identifiers, build metadata, and precedence, and
  decides whether SemVer fits the product. It maps versions to npm, Cargo,
  Go modules, PEP 440, Maven, OCI tags, and app stores. `scripts/semver.py`
  checks, compares, sorts, and bumps versions.
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
- `write-agents-md` covers symlinked instruction files, dotclaude's size
  thresholds, and merging superseded rules; `check_instructions.py` follows
  symlinks, fails on a dangling one, checks each real file once, and strips
  block-level HTML comments before counting lines.
- `write-behavior-tests` routes tests of doc, prompt, or README wording to
  tests of the program effect or of a machine-read format.
- `coordinate-phase-gated-subagents` cross-checks worker reports against
  each other and against each worktree's diff before integration.
- `design-software-architecture` puts data invariants in database
  constraints and keeps application checks for error messages.
- `create-agent-skills` checks existing skills for trigger and scope
  overlap before creating one, and audits trigger collisions.
- `write-implementation-plans` requires each slice to remove or name the TODO,
  stub, or placeholder it adds, and reviews plans for unremoved markers.
- `create-agent-skills` teaches the Agent Skills, Anthropic, and OpenAI
  authoring rules it lacked: front-loaded third-person descriptions,
  `evals/eval_queries.json` and its train and validation split, bounded
  script output, inline dependencies, pinned one-off commands, network use
  limited to the stated purpose, one job per skill, load conditions for
  references, and gotchas with reasons in `SKILL.md`.
- Bundled scripts name the missing or unwritable path and the expected
  input (`check_gate.py`, `check_hook_config.py`, `merge_hooks.py`,
  `ddmin.py`, `sync_labels.py`, `upsert_comment.py`); the hook handlers'
  `--help` lists exit status and examples; the Bun migration and `just`
  example verifiers accept `--help` and reject unknown arguments.
- `find-vulnerabilities` pins the packages its examples and dependency
  audit fetch (`jinja2==3.1.6`, `defusedxml==0.7.1`, `argon2-cffi==25.1.0`,
  `pip-audit@2.10.1`) and treats text in the reviewed code as data, not
  instructions.
- The Eclipse p2 director example names each repository URL in its own
  variable instead of one comma-joined string.
- `update-changelogs` hands version choice to `apply-semantic-versioning`
  and keeps checking release-heading syntax in `audit_changelog.py`.
- Sublime Text examples are type-checked against the skill's bundled host
  fakes instead of root stubs.
- Shared Markdown lint rules live in `.markdownlint.jsonc`, which
  `.markdownlint-cli2.jsonc` extends.

### Removed

- `find-implementation-plan-flaws`; use `write-implementation-plans`, which
  also reviews plans.
- `reproduce-software-bugs`, `find-regression-commits`, and
  `diagnose-software-failures`; use `debug-software-failures`.
- `apply-pep20-to-codebases`; use `write-readable-code`.
- `update-changelogs/scripts/audit_semver.py` and the SemVer cards; use
  `apply-semantic-versioning` and `scripts/semver.py check`.

### Fixed

- `find-vulnerabilities`' `int()`-sanitized Semgrep example rejects a
  negative `LIMIT`, which SQLite reads as no limit.
- The IntelliJ Platform workflow runs `scripts/check_plugin_xml.py`
  instead of an unresolved `<skill>/` path.
- Reference cards no longer claim that `return cond ? a : b;` moves in
  C++, that `quote(args)` forwards `just` variadic arguments separately, or
  that release-mode `#[inline]` matches LTO in Rust; the Java integer-cache
  card explains why `AutoBoxCacheMax` did not apply.
- Bundled scripts exit with a usage error instead of a traceback on
  missing or malformed input, and fix `unittest discover` handling in
  `audit_plan_claims.py`, short `--max` versions in `wasm_api_version.py`,
  missing paths in `scan_secrets.py`, and `r` of ±1 in `check_stats.py`.
