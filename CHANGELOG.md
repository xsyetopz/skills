# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/). The project has no
released versions yet.

## [Unreleased]

### Added

- 32 skills for coding agents, grouped in install bundles in `bundles.toml`. Three are manual-only
  (`disable-model-invocation`) and load only when invoked by name.
- Skills stop and ask before outward-facing, paid, or destructive steps, such as pushes, releases,
  and paid runs, and name the consequence.
- Every skill that can trigger on its own has 20 trigger queries with a fixed train and validation
  split, and output evals with fixtures and deterministic checks, under `evals/<skill>/`. Installed
  skills do not include them. `just eval-triggers` and `just eval-outputs` run them in isolated
  Claude Code sessions and write results under `.evals/`.
- `just validate` checks the Agent Skills spec, names, a 200-line body limit, 400-character
  descriptions, 250-character `when_to_use` fields, each bundle's skill listing against 8,000
  characters, links, skill layout, file hygiene, secrets, Markdown, Python tests, ruff, pyright,
  shellcheck, and justfiles. The pre-commit hook runs the fast checks, and the pre-push hook runs
  all of them.
- `just index` prints a skill list for CLAUDE.md or AGENTS.md, one line per skill with when to use
  it, and `--bundle NAME` limits it to installed bundles.
- Markdown headings use title case: Chicago style for English, the language's own convention
  otherwise, and names as their owners write them.
