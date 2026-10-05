# Rust Diagnostics

Read when rustc, clippy, or a Cargo lint reports a diagnostic. It gives the suppression forms to
refuse, the config keys that loosen checks, how to make the tool report unused suppressions, and
where Rust documents replacements.

Versions checked on 2026-10-06: Rust 1.99.0 (2026-09-28 build; release notes dated 2026-10-01).
Clippy ships with the toolchain. Check `rustc --version` and `cargo --version` in the repository
before you apply a rule below.

## Contents

- [Suppression Forms to Refuse](#suppression-forms-to-refuse)
- [Config Keys That Loosen Checks](#config-keys-that-loosen-checks)
- [Stale Suppressions](#stale-suppressions)
- [Deprecations and Replacements](#deprecations-and-replacements)
- [Strict CI Form](#strict-ci-form)

## Suppression Forms to Refuse

| Form | Notes |
| --- | --- |
| `#[allow(lint)]`, `#![allow(lint)]` | Silences the lint for the item or the crate. `#![allow(...)]` at the crate root is the widest form. |
| `#[expect(lint)]` | Silences the lint and warns when it stops firing (stable since 1.81.0). Still a suppression; ask first. |
| `#[warn(lint)]`, `#[deny(lint)]`, `#[forbid(lint)]` | Level attributes; `warn` on a `deny` lint is a loosening. |
| `reason = "..."` | Every lint attribute accepts it: `#[allow(unused_mut, reason = "only modified on some platforms")]`. Give a reason when the user approves a suppression. |

Source: `https://doc.rust-lang.org/reference/attributes/diagnostics.html`.

Clippy has lints that police the attributes: `clippy::allow_attributes` (restriction group,
allow by default) suggests `#[expect]` in place of an outer `#[allow]`, and
`clippy::allow_attributes_without_reason` flags an allow with no reason. Clippy's own docs say it
is meant to be used with "a generous sprinkling of `#[allow(..)]`s", which is not permission here
(see the rules in `SKILL.md`). The `clippy::restriction` group should not be enabled as a whole.

## Config Keys That Loosen Checks

| Where | Form |
| --- | --- |
| Cargo manifest | `[lints.rust]` or `[lints.clippy]` set to `allow`; `{ level = "...", priority = N }` changes. Workspaces use `[workspace.lints.*]` with a member `[lints] workspace = true`. |
| Environment | `RUSTFLAGS` (`-A warnings`, `--cap-lints allow`); `CARGO_ENCODED_RUSTFLAGS`. |
| `.cargo/config.toml` | `build.rustflags`, `target.<triple>.rustflags`, and `build.warnings = "allow"`. |
| `clippy.toml`, `.clippy.toml` | Options such as `msrv` and `disallowed-names` change what lints fire. |
| Command line | `--cap-lints` caps every level. `--cap-lints allow` hides everything and also downgrades `forbid`. |

Levels are `allow`, `warn`, `force-warn`, `deny`, and `forbid`
(`https://doc.rust-lang.org/rustc/lints/levels.html`). An inner `allow` cannot override `forbid`,
so a `forbid` in `[lints]` is a guard to keep. `[lints]` is stable since 1.74.0 and workspace
inheritance is respected as of 1.74. The `missing_lints_inheritance` Cargo lint (warn) reports a
member that does not inherit; Cargo's own `[lints.cargo]` system is unstable and nightly-only.

## Stale Suppressions

Use `#[expect(lint, reason = "...")]` in place of `#[allow]` when the user approves a suppression.
If the expectation is not fulfilled (the lint would not fire under `#[warn]`), rustc emits the
`unfulfilled_lint_expectations` lint, which is warn-by-default
(`https://doc.rust-lang.org/rustc/lints/listing/warn-by-default.html`). `#[allow]` has no staleness
report in the sources read; `clippy::allow_attributes` is how to find them.

## Deprecations and Replacements

An item is marked `#[deprecated]`, `#[deprecated = "message"]`, or
`#[deprecated(since = "5.2.0", note = "foo was rarely used. Users should instead use bar")]`.
rustc warns on use through the `deprecated` lint ("detects use of deprecated items"). It does not
interpret `since`; Clippy may check it. The `note` is "typically used to provide an explanation
about the deprecation and preferred alternatives", so the replacement is in the `note` and in the
rustdoc deprecation banner. Read both before you edit. `#[allow(deprecated)]` is the suppression
to refuse.

## Strict CI Form

- Cargo 1.97 and later: `build.warnings = "deny"` in the Cargo config, or
  `CARGO_BUILD_WARNINGS=deny`. Allowed levels are `warn` (default), `allow`, and `deny`. It was
  stabilized in 1.97.0 in place of `-Dwarnings`. The Clippy usage docs call it the recommended way
  since Cargo 1.97.
- Older Cargo: `cargo clippy -- -Dwarnings`, which invalidates the build cache.
- Do not add `-A warnings`, `--cap-lints allow`, or `build.warnings = "allow"` to a CI config.

Docs: `https://doc.rust-lang.org/clippy/usage.html`,
`https://doc.rust-lang.org/cargo/reference/config.html`, and the Clippy lint index at
`https://rust-lang.github.io/rust-clippy/master/index.html`.
