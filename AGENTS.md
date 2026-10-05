# xsyetopz/skills

Skills guide requested work without expanding its scope or authorizing adjacent changes. Preserve
unrelated work and keep one clear implementation path.

## Existing Mechanisms

- Before adding a file or tool, inspect the root and affected subtree. Extend an existing mechanism
  with the same responsibility.
- Treat existing commands, lockfiles, and configuration as authoritative unless the task changes
  that policy.
- Preserve `.markdownlint-cli2.jsonc` and the shared rules it extends, `.markdownlint.jsonc`; use
  them for all repository Markdown.
- Use Bun for JavaScript tooling. Never introduce npm, npx, Yarn, or pnpm.
- Use `just` for new task orchestration.

## Change Boundaries

- Treat everything under `skills/` as published package content. Keep internal plans, audits, and
  execution records outside it, such as in `docs/audits/`. Published instructions must not depend on
  or link to internal maintenance records; retain reusable audit methodology, technical sources,
  examples, and benchmark evidence in packages.
- Batch coherent behavior with its tests and documentation. Remove superseded duplication in the
  same slice.
- Do not edit generated files or create commits unless requested.
- For authorized commits, group independently valid, revertible behavior and run its relevant
  checks. Do not rewrite earlier history to reshape commits.

## Validation

Keep each `SKILL.md` body within 200 lines, normally about 150 or fewer. The repository validator
excludes frontmatter and surrounding blank lines but counts headings, internal blanks, examples, and
link definitions. References have no numerical ceiling. This is catalog policy, not a model limit or
a measure of density, read coverage, or reliability. Keep the existing validator and its boundary
tests; do not add a density checker.

Keep each description within 400 characters and each optional `when_to_use` within 250. Every skill
sits in exactly one bundle in `bundles.toml`, and each bundle's listing, one
`- name: description when_to_use (file: skills/name/SKILL.md)` line per model-invoked skill, stays
within 8,000 characters. `just metadata` prints each bundle's total.
`docs/research/skill-discoverability.md` records the sources for these limits.

Run commands from the repository root through existing `just` recipes. Use narrow recipes while
iterating and `just validate` for catalog-wide changes. Do not duplicate recipe logic in new scripts
or configuration. The recipes provision JavaScript tools with Bun and validation tools under
`SKILLS_CACHE_DIR` or the default user cache.
