---
name: write-justfiles
description: >-
  Create, repair, review, or run justfiles using the current Just language and
  command-line contract. Not for implementing application build logic.
---

# Write Justfiles

Inspect the installed Just version and the repository's existing commands before
changing orchestration. Preserve one obvious task path and delegate work to the
project-native tools rather than reproducing their logic in recipes.

## Workflow

1. Read the affected recipes and their manifest, lockfile, and contributor
   commands. Check `just --version` against the syntax they need.
1. For changes to environment access, dependencies, paths, or failure handling,
   consult [the language reference](references/current-just-api.md).
1. Keep caches and generated state in established locations. Quote interpolated
   paths and make environment loading explicit.
1. Use `env("KEY")` for a required environment variable and
   `env("KEY", default)` for an optional variable. Never introduce deprecated
   `env_var` or `env_var_or_default` calls.
1. Add only recipes that name a meaningful project operation. Use dependencies
   to compose existing recipes instead of copying their bodies.
1. Inspect the result before running the narrowest harmless recipe.

## Validation

Run these from the repository root:

```sh
just --list
python3 /path/to/write-justfiles/scripts/check_justfiles.py justfile
```

When `just-lsp` is available, also run `just-lsp analyze justfile` and resolve
every diagnostic rather than disabling a rule.

Use `just --dry-run <recipe>` before a recipe with external effects. Then run
its real validation path and preserve the exit status of every delegated tool.

The bundled [example](assets/example.just) demonstrates current environment
access without implicitly loading a dotenv file.
