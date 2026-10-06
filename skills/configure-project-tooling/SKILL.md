---
name: configure-project-tooling
description: >-
  Sets up lint, format, type-check, and toolchain config from checked baselines:
  Biome, tsconfig, and bunfig for Bun, and rustfmt, clippy, and cargo-deny for Rust.
  Checks new dependencies against a dated package catalog.
  Use when starting a project, adding a linter or tsconfig, or picking a library.
---

# Configure Project Tooling

Copy a checked baseline instead of writing lint, format, compiler, and package-manager config.
Query the package catalog before you add a dependency.
The baselines were checked on 2026-10-07
with Biome 2.5.15, TypeScript 7.0.2, Bun 1.4.2, Rust 1.99.0, and cargo-deny 0.20.2.

## Rules

- Never hand-write `biome.json`, `tsconfig*.json`, `bunfig.toml`, `clippy.toml`, `rustfmt.toml`,
  or `deny.toml` from memory.
  Copy the file from `assets/`, then change only the project-specific parts that are named below.
- When the project already has one of these files, the existing file is the project's policy.
  Show the user a diff against the baseline, and replace the file only when the user says yes.
- Do not weaken a rule to make a check pass.
  Fix the code.
  A rule that conflicts with another rule is a baseline defect: report it with the two diagnostics.
- Run every check in the **Verify** section after the copy.
  A config that was copied but not run is not done.
- Other ecosystems (.NET, Go, Python, Swift, C and C++) have no baseline.
  Follow the config that the project already has, and do not invent one.

## Bun and TypeScript

Copy these files from `assets/bun/` to the project root:

| File | Change for the project |
| --- | --- |
| `biome.json` | Nothing. Keep the version in the schema URL equal to the installed Biome version. |
| `tsconfig.base.json` | Nothing. |
| `tsconfig.json` | Set `include` to the project's source and test folders. |
| `bunfig.toml` | Nothing. `linker = "isolated"` stops imports of undeclared packages. |

Install the tools as exact dev dependencies:
`bun add -d -E @biomejs/biome typescript @types/bun @types/node`.

Facts behind the baseline:

- `module: "preserve"` with `moduleResolution: "bundler"` matches how Bun loads modules.
  TypeScript 7 rejects `node10` resolution, `es5`, `amd`, `baseUrl`, and `outFile`.
- `types` defaults to `[]` in TypeScript 7, so the base lists `bun` and `node`.
  Add an entry for each other global type package.
- `useLiteralKeys` is `"off"`,
  because its fix (`obj.key`) breaks `noPropertyAccessFromIndexSignature` with TS4111.
- The Biome `includes` glob lists `css` and `html`.
  Without them the `css` and `html` linter settings check nothing.
- Biome reads `.gitignore` (`vcs.useIgnoreFile`), and it stops with a configuration error
  when the project root has no `.gitignore`.
- There is no `composite`, because it fails with TS6307 when `include` misses an imported file.

## Rust

Copy these files from `assets/rust/`:

| File | Destination |
| --- | --- |
| `rust-toolchain.toml` | Project root. Change `channel` only to a newer stable release. |
| `rustfmt.toml`, `clippy.toml`, `deny.toml` | Project root. |
| `Cargo.workspace.toml` | Merge its tables into the root `Cargo.toml`. Do not copy the file. |

- Each member crate sets `[lints] workspace = true`,
  `edition.workspace = true`, and `rust-version.workspace = true`.
- Keep the `llvm-tools` component.
  rust-lld loads `libLLVM.dylib` from it, and wasm and embedded links fail without it.
- Remove the three `*_instead_of_*` lints only for a crate that will never build without `std`.
- Every lint is `forbid`, so source attributes cannot lower it.
  Test exceptions are in `clippy.toml` only.
- Keep `lib.rs`, `main.rs`, and `mod.rs` to attributes, module declarations, re-exports,
  and entry-point composition, and put the code in ordinary modules.
- Never write an inline `#[cfg(test)] mod tests { ... }`.
  Declare `#[cfg(test)] mod tests;` and put unit tests in the adjacent `<module>/tests.rs`.
  Put integration tests in the package's `tests/` folder.
- `missing_panics_doc` has no test exception.
  Give each `#[test]` function a `/// # Panics` section that says what failure it reports.
- `unknown_lints = "forbid"` fails the build when a lint name was renamed or removed.
  Rename it to the name that rustc suggests.

Check that the pinned toolchain is the one that runs.
A Homebrew `cargo-clippy` or `rustc` earlier in `PATH` overrides rustup,
and then cargo reports `rustc 1.98.1 is not supported`.
Run `cargo clippy -V` and compare it with the pin.
If it differs, put `$(dirname "$(rustup which rustc)")` first in `PATH`.

## Dependencies

The catalog in `assets/packages/` has one JSONL file for each ecosystem: `npm`, `crates`,
`nuget`, and `go`.
Each row holds registry and repository facts, such as the latest version, release date, license,
archived flag, deprecation, and advisories.
Each row also has a `status` that a fixed rule derives from those facts.
[references/package-catalog.md](references/package-catalog.md) defines the fields and the rule.

Before you add a dependency, query the catalog:

```sh
python3 scripts/package_catalog.py query --ecosystem npm --name zod
python3 scripts/package_catalog.py domains --ecosystem crates
python3 scripts/package_catalog.py query --ecosystem go --domain auth --status active
```

- Do not add a package whose status is `missing`, `deprecated`, or `archived`.
  Use its `replacement` when it has one, and otherwise pick an `active` package in the same domain.
- A `prerelease` package has no stable version.
  Tell the user, and add it only when they accept a prerelease.
- For a `stale` package, tell the user its last release date before you add it.
  A small, finished library can be stale and still correct.
- The catalog is a snapshot, and each row has a `verified` date.
  For a row older than 90 days, run `refresh` for that ecosystem first.
- For a package that is not in the catalog, run `add --ecosystem <eco> --name <name> --domain <d>`.
  The script fetches the facts, so do not type them in.
- Prefer the standard library or the runtime (`Bun.*`, `node:*`, `std`) over a package.
  The catalog does not list them.

## Verify

Bun:

```sh
bun install
bunx --bun biome check .
bunx --bun tsc -p .
bun test
```

`--bun` runs the tool with Bun, even when its script starts with a `node` shebang.

Rust:

```sh
cargo fmt --check
cargo clippy --all-targets
cargo test
cargo deny check
```

Report each command and its result.
A command that could not run goes in a **Not verified** list with the reason.
