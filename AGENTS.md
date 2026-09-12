# Repository instructions

## Existing mechanisms

- Before adding a file, configuration, script, or documentation entry, inspect
  the repository root and the affected subtree for an existing mechanism with
  the same responsibility. Extend that mechanism instead of creating a
  parallel path.
- Treat existing project tool choices, commands, lockfiles, and configuration
  as authoritative unless the user explicitly requests a policy or toolchain
  change. A skill's bundled configuration is only a fallback when no project
  policy governs the target.
- Preserve `.markdownlint-cli2.jsonc`. Use it for this repository's Markdown;
  do not replace it with a skill asset or a newly generated policy.
- Add a new file only when no existing mechanism can own the responsibility.

## Change and commit boundaries

- Batch edits into coherent behavioral slices. Keep each responsibility on one
  clear implementation path and remove superseded duplication in the same
  slice.
- Do not create commits unless the user authorizes them. For future authorized
  commits, slice by independently valid, revertible behavior rather than file
  count or diff size. Keep an implementation with its relevant tests and
  necessary documentation, and run the relevant checks for every commit.
- Honor an explicit request for one commit. Apply these rules only to new
  commits; do not rewrite existing history to reshape earlier work.

## Validation

- Run commands from the repository root with the pinned or configured tools.
- Run `just validate` for repository-wide validation. Use its narrower recipes
  for focused checks while iterating; do not duplicate their logic in new
  scripts or configuration.
- Use Bun for JavaScript tooling in this repository. The validation environment
  is provisioned by the existing `just` recipes under `SKILLS_CACHE_DIR` or the
  default user cache.
