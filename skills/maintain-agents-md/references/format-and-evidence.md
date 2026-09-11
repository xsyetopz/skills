# Discovery, precedence and evidence-backed instructions

Reviewed 2026-09-12. AGENTS.md is a Markdown convention, not a versioned schema.
Check the target client's discovery behavior before changing scope.

## Format and consumer behavior

AGENTS.md has no required YAML schema or headings. It supplies repository
context such as commands, boundaries and consequential conventions. Nested
guidance can specialize a subtree, but actual discovery is implemented by the
consuming agent. GitHub `.github/agents/*.agent.md` files describe custom
personas and are not a substitute. [AGENTS.md format](https://agents.md/).

Codex builds its initial chain once per run/session. At global scope it uses the
first nonempty `AGENTS.override.md` or `AGENTS.md` in Codex home. From project
root to working directory it chooses at most one file per directory: override,
standard name, then configured fallbacks. Deeper guidance appears later. Without
a project root it checks the current directory. Empty files are skipped; the
default combined limit is 32 KiB (`project_doc_max_bytes`). Fallback names are
configured by `project_doc_fallback_filenames`. Do not assume a sibling
subtree's instructions enter the initial chain.
[Codex discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md).

Record the intended launch directory and map its chain before deciding where
guidance belongs. For `repo/services/payments`, root guidance and intermediate
instructions can apply, while `services/search/AGENTS.md` is outside that chain.
An override in payments replaces the standard file at that directory, not the
whole ancestor chain. Repository guidance remains subordinate to applicable
higher-priority instructions and explicit user requirements.

## Derive rules from evidence

For each candidate instruction, identify:

- **Build/test command** Evidence to inspect: Manifest script, working
  directory, CI invocation, required environment Common mistake: Publishing a
  remembered command that is not defined here

- **Ownership boundary** Evidence to inspect: Exports, callers, generated
  inputs, representative code Common mistake: Promoting one package's pattern
  into a root rule

- **Required gate** Evidence to inspect: CI/job policy and existing instruction
  Common mistake: Turning an optional local tool into a mandatory install

- **Prohibited side effect** Evidence to inspect: Existing policy or explicit
  user constraint Common mistake: Inventing approval rules from hypothetical
  risk

- **Compatibility** Evidence to inspect: Toolchain pins, support matrix, public
  consumers Common mistake: Requiring an upgrade because a current example uses
  it

Resolve README/CI disagreements by inspecting the invoked script and its
consumers. Record command prerequisites and actual execution results.

## Concrete root and nested formats

Root example. Replace commands and paths with verified repository values:

```markdown
# Repository instructions

## Commands

- From the repository root, run `bun install --frozen-lockfile` using the pinned
  Bun version.
- Run `bun run test` for shared-library changes. It invokes the `test` script
  defined in package.json.

## Boundaries

- Edit API schemas in `schema/`; regenerate `src/generated/` with
  `bun run generate`.
- Keep generated output and its schema change in the same change.
```

Add only the local difference in a nested file: “From `services/payments`, run
`make test-unit`; database integration tests additionally require the documented
disposable database.” Do not repeat the root's entire content or silently
disable a root gate. Explain whether a command is replacement or additional when
ambiguity affects execution.

Use a concrete trigger and action: “When editing schema inputs, run the existing
generator so checked-in clients match the schema.” Remove generic advice such as
“follow best practices.” Link the canonical document for optional detail instead
of copying it into every scope.

## Audit and maintenance

Read all applicable instruction files before editing. Check file existence,
relative links, command working directories, stale tool names, contradictions
and the consumer's size budget. Retain supported constraints. Correct obsolete
exceptions and contradictions. Put the essential boundary before long
conditional details so truncation is less consequential.

When existing agent-specific files must remain supported, choose a canonical
source and an explicit sync/link mechanism compatible with those consumers. A
symlink is not portable evidence that every host will load the target; keep a
duplicate only with identified maintenance ownership. Do not change personal
configuration to make repository documentation appear effective.

Report findings with path, instruction, consequence, and supporting evidence.
For rewrites, resolve factual defects and identify only unresolved policy
choices.

Do not equate a package-manager builtin with a manifest script. For example,
`bun test` runs Bun's test runner; `bun run test` selects the package script. A
passing builtin can bypass checks configured in that script. Verify the exact
command used by the repository rather than translating it from memory.
