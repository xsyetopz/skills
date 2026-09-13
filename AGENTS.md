# Repository instructions

Skills guide requested work without expanding its scope or authorizing adjacent
changes. Preserve unrelated work and keep one clear implementation path.

## Existing mechanisms

- Before adding a file or tool, inspect the root and affected subtree. Extend an
  existing mechanism with the same responsibility.
- Treat existing commands, lockfiles, and configuration as authoritative unless
  the task changes that policy.
- Preserve `.markdownlint-cli2.jsonc`; use it for all repository Markdown.
- Use Bun for JavaScript tooling. Never introduce npm, npx, Yarn, or pnpm.
- Use `just` for new task orchestration.

## Change boundaries

- Batch coherent behavior with its tests and documentation. Remove superseded
  duplication in the same slice.
- Do not edit generated files or create commits unless requested.
- For authorized commits, group independently valid, revertible behavior and run
  its relevant checks. Do not rewrite earlier history to reshape commits.

## Validation

Run commands from the repository root through existing `just` recipes. Use
narrow recipes while iterating and `just validate` for catalog-wide changes.
Do not duplicate recipe logic in new scripts or configuration. The recipes
provision JavaScript tools with Bun and validation tools under
`SKILLS_CACHE_DIR` or the default user cache.
