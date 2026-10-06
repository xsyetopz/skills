# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/). The project has no
released versions yet.

## [Unreleased]

### Added

- 33 skills for coding agents, grouped in install bundles in `bundles.toml`. Three are manual-only
  (`disable-model-invocation`) and load only when invoked by name.
- `configure-project-tooling` copies checked lint, format, compiler, and toolchain baselines:
  Biome, tsconfig, and bunfig for Bun, and rustfmt, clippy, and cargo-deny for Rust.
  It checks each new dependency against a dated catalog of npm, crates, NuGet, and Go packages,
  which `scripts/package_catalog.py` queries, refreshes, and extends from the registries.
- `refactor-code-smells` has a readability reference
  and a reference on the failure modes of agent-written code.
- `apply-architecture-patterns` has a file-layout reference with a layout for each ecosystem.
- Skills stop and ask before outward-facing, paid, or destructive steps, such as pushes, releases,
  and paid runs, and name the consequence.
- Every skill that can trigger on its own has 20 trigger queries with a fixed train and validation
  split, and output evals with fixtures and deterministic checks, under `evals/<skill>/`. Installed
  skills do not include them. `just eval-triggers` and `just eval-outputs` run them in isolated
  Claude Code sessions and write results under `.evals/`.
- `just validate` checks the Agent Skills spec, names, a 200-line body limit,
  300-character descriptions with no `when_to_use` field,
  each bundle's skill listing against 8,000 characters,
  links, skill layout, file hygiene, secrets, Markdown,
  Python tests, ruff, pyright, shellcheck, and justfiles.
  The pre-commit hook runs the fast checks, and the pre-push hook runs all of them.
- Every skill description starts with what the skill does,
  then "Use when" with the user's phrasings,
  within the 300 characters that Claude Code shows in its skill listing.
- `just index` prints a skill list for CLAUDE.md or AGENTS.md, one line per skill with when to use
  it, and `--bundle NAME` limits it to installed bundles.
- Markdown headings use title case: Chicago style for English, the language's own convention
  otherwise, and names as their owners write them.
