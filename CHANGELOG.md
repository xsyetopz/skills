# Changelog

All notable changes to this project are documented in this file.

The format is based on
[Keep a Changelog](https://keepachangelog.com/en/2.0.0/). The project has
no released versions yet.

## [Unreleased]

### Added

- `write-architecture-md` writes, updates, and audits ARCHITECTURE.md files
  from the architecture.md template, with matklad's durability rules. The
  file is always `ARCHITECTURE.md` at the repository root; one kept in
  `docs/` is moved there. `scripts/check_architecture.py` checks the
  document against the repository: its name and location, missing or
  empty sections, leftover placeholders, unfenced
  diagrams, paths that do not exist, and undescribed top-level directories.
- `design-command-line-interfaces` designs, changes, renames, and reviews
  an application's CLI commands from the Command Line Interface Guidelines
  (clig.dev): streams, exit codes, help, errors, flags, prompts, config, and
  deprecated aliases for renamed commands under a compatibility promise, or
  direct renames with a changelog entry when the project allows breaking
  changes. `scripts/check_cli.py` probes a
  built CLI for help, unknown-flag, color, stack-trace, and hang defects.
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
  against the Zen of Python (PEP 20) in any language. It limits source
  files to 300 code lines and test files to 500, split by responsibility;
  `scripts/file_length.py` counts code lines without comments or blank
  lines in any common language and flags files over their limit.
- `analyze-binaries-with-ghidra` queries Ghidra projects from a coding
  agent through the pyghidra-mcp MCP server, or the ghidra-bridge CLI over
  exported data: setup, the one-time export, the query order, output
  limits, crash-address lookup, and project-lock errors.
- `reverse-engineer-functions` reverses one function with any disassembler
  or decompiler: evidence-cited claims, calling conventions per platform,
  compiler idioms, struct recovery, vtables and RTTI, name confidence, and
  a report with open questions by address.
- `build-matching-decompilations` builds source that compiles to the same
  bytes as a reference binary, with a pinned reference hash and toolchain,
  fail-closed full-function compares, negative controls, and an attempt
  log. `scripts/check_match_evidence.py` recomputes the recorded hashes and
  coverage and fails on any gap in the acceptance evidence.
- `run-reagent-pipelines` runs Reagent (`re-agent`) as a budgeted batch
  job: `doctor`, `estimate`, `plan`, then a small `reverse` run, with a
  measured usage check and review of parity results as candidates.
- `choose-claude-model-and-effort` picks the Claude model and effort level
  for a main session, subagent, headless run, or API call from current
  prices, cache economics, and task shape, and sets `model`, `effort`, and
  the prompt cache TTL where they take effect.
- `audit-agent-sessions` audits Claude Code transcripts for wasted turns,
  tokens, and attention, and turns each finding into one rule, hook, or
  prompt fix. `scripts/session_stats.py` reports token use by model and
  agent, repeated reads and commands, and compaction points without
  printing message text.
- `write-goal-conditions` writes and repairs `/goal` conditions that a
  transcript-only evaluator can judge: an end state the output shows, the
  check command, and a turn bound.
- `find-code-smells` reports code smells with evidence and routes each to
  the refactoring that removes it: the 24 smells of *Refactoring* (2nd
  ed.), folder-layout smells from published style guides (folders by kind,
  name prefixes standing in for a directory, numbered copies, dumping-ground
  and category files, stutter), change coupling from Git history, and the
  default size and complexity limits of common linters.
  `scripts/layout_smells.py` scans a tree for layout smells, and
  `scripts/change_coupling.py` computes code-maat's logical coupling from
  `git log`.
- `write-github-markdown` writes and fixes GitHub Flavored Markdown that
  also reads well as raw text: heading anchors, linked Contents lists,
  relative and reference-style links, fences, tables, lists, alerts,
  footnotes, collapsed sections, Mermaid, math, and a markdownlint rule
  map. `scripts/markdown_toc.py` writes or checks the linked list under a
  `## Contents` heading.
- Every skill has trigger queries (`evals/eval_queries.json`, 20 per skill
  with a fixed train and validation split) and output evals
  (`evals/evals.json`) with fixtures and deterministic checks.
- `just eval-triggers` and `just eval-outputs` run those evals in isolated,
  sandboxed Claude Code sessions and write agentskills.io-style results
  under `.evals/`.
- `just skill-lint` (`scripts/skill_lint.py`) checks each skill for body
  token budgets, bare file references including `${CLAUDE_SKILL_DIR}/`
  paths, orphan files, nested references, prompting scripts, `--help`,
  layout, and auxiliary or junk files. `just validate` and the pre-commit
  hook run it with `--strict`.
- `just hygiene` runs the pre-commit-hooks checks (large files, private
  keys, case conflicts, symlinks, shebangs against the executable bit), and
  `just secrets` runs gitleaks on staged, unstaged, and committed content.
  The pre-commit hook and `just validate` run both.
- Bundled checkers accept `--json`; scanners accept `--limit`; `mutate.py`
  accepts `--list` for a dry run.

### Changed

- Skill descriptions state what the skill does, then when to use it, then
  what it is not for, in the third person.
- Every skill description is at most 200 characters and puts the task and
  its trigger words first.
- Skill descriptions use plain words without colons, slashes, parentheses,
  or other symbols, and `create-agent-skills` requires this for new skills.
- Every `## Contents` section in skill references is a list of links to
  heading anchors, written by `markdown_toc.py`, and
  `check_reference_structure.py` fails a Contents entry that is not a link
  or a `##` heading the list does not link.
- `document-codebases` routes Markdown syntax (fences, tables, alerts,
  collapsed sections, diagrams, Contents lists) to `write-github-markdown`
  instead of repeating it.
- `write-readable-code` treats repository-wide category files (`types`,
  `constants`, `models`) as dumping grounds and lists SwiftLint, RuboCop,
  and detekt size defaults next to its file-length limits.
- `design-software-architecture` adds package cohesion (REP, CCP, CRP) and
  stable-dependency (ADP, SDP, SAP) cards with Martin's instability and
  abstractness metrics.
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
- Every script with a shebang is executable.
- `update-changelogs` hands version choice to `apply-semantic-versioning`
  and keeps checking release-heading syntax in `audit_changelog.py`.
- Sublime Text examples are type-checked against the skill's bundled host
  fakes instead of root stubs.
- Shared Markdown lint rules live in `.markdownlint.jsonc`, which
  `.markdownlint-cli2.jsonc` extends.
- `create-agent-hooks` covers choosing deny, ask, or warn, deny reasons
  that name the next action, an ask budget, a verdict log without secrets,
  shell-faithful path checks for writes through Bash, loop and waste
  detectors, and refusal detection.
- `manage-git-changes` checks repository rules and harness settings for
  agent commit attribution (Claude Code, Aider, Copilot CLI, Cursor), and
  warns before staging binaries under analysis or tool exports.
- `debug-software-failures` reads effective settings and profiles before
  blaming a tool, and starts a new session with a handoff when an agent
  keeps refusing.
- `coordinate-phase-gated-subagents` reads the concurrent subagent limit
  before planning a wave and gives each brief one behavior.
- `write-behavior-tests` treats snapshot update commands as loosened
  assertions.
- `write-agents-md` covers Claude Code's `# Compact instructions` section
  and links human docs from the project map.
- `write-implementation-plans` tags each task's evidence as verified,
  reported, or inferred, and starts report-only tasks with a spike.
- `create-agent-skills` routes agent `model` and `effort` choices to
  `choose-claude-model-and-effort`.
- `find-vulnerabilities` routes compiled targets to
  `analyze-binaries-with-ghidra` and `reverse-engineer-functions`.

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
