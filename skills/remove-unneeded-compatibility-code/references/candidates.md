# Compatibility candidates

Kinds of compatibility code, how to find them, and when each is
removable. The worked package is [`assets/examples/before/`][before] and
its cleaned form `after/`; `verify.sh` runs every check below on them.

## Contents

- Version-gated branch
- Import fallback
- Deprecated alias
- Persisted or serialized alias
- Package export alias
- Feature probe and polyfill
- Fully rolled-out feature flag
- Generated compatibility surface

## Version-gated branch

**Definition.** Code that runs only on some language, runtime, or platform
versions: `if sys.version_info < (3, 11)`, `#if NET6_0_OR_GREATER`,
`#[cfg(...)]`, `@available(macOS 14, *)`. A branch is dead when the
project's declared minimum version makes its condition constant.

**Use when.** The minimum supported version has risen above the branch's
bound (read it from `requires-python`, `<TargetFrameworks>`,
`rust-version`, `engines`, deployment targets).

**Do not use when.** The minimum is undeclared or disputed; settle the
support policy first.

**Example.**

```python
if sys.version_info < (3, 11):
    def _read(path: str) -> dict: ...
else:
    def _read(path: str) -> dict: ...
```

With `requires-python = ">=3.11"`, the first branch never runs.

**Cost removed.** Code paths that no supported version executes.

**Verify.**

1. `python3 scripts/find_compat_python.py src --min-python 3.11` marks it
   `dead`; `ruff check --select UP036 --target-version py311` reports
   UP036 ([ruff UP036][up036]).
1. For .NET: `dotnet msbuild -getProperty:TargetFrameworks` and
   `rg -n '#if NET' src/`; for Rust: `rg -n 'rust-version' Cargo.toml` and
   `rg -n 'cfg\(' src/`.

## Import fallback

**Definition.** `try: import new_module` / `except ImportError: import
backport` for a module that older runtimes lack.

**Use when.** The primary module is guaranteed by the minimum version
(`tomllib` since Python 3.11 ([tomllib][tomllib])).

**Do not use when.** The fallback handles an optional dependency the
project supports running without, such as an optional C accelerator.

**Example.**

```python
try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11 only
    import tomli as tomllib
```

becomes `import tomllib`, and the backport leaves the dependency list.

**Cost removed.** An extra dependency and an untested code path.

**Verify.**

1. The scanner reports `import-fallback`. After removal, drop the backport
   from the manifest and run the tests on the minimum version.

## Deprecated alias

**Definition.** An old name that forwards to the new API and warns
(`warnings.warn(..., DeprecationWarning)`, `@deprecated`, `[Obsolete]`,
`#[deprecated]`, JSDoc `@deprecated`).

**Use when.** No consumer uses the alias, and either the policy's
deprecation period has ended or the alias was never public.

**Do not use when.** The alias is part of a published API and the release
is not a major version; removal is an incompatible change under
[SemVer][semver].

**Example.** `load_config` in the worked package: deprecated in 1.2,
removal planned for 2.0, and no references outside its own definition.

**Cost removed.** Two names for one operation.

**Verify.**

1. `rg -n '\bload_config\b'` finds only the definition.
1. `python3 -W error::DeprecationWarning -m unittest` passes, so no test
   still calls a deprecated name.

## Persisted or serialized alias

**Definition.** Code that reads old names or formats from stored data:
renamed config keys, enum values, database columns, message fields.

**Use when.** A migration has rewritten every stored instance, or the
support policy has ended for data written by old versions.

**Do not use when.** Supported saved data may still contain the old form.
No code writes it any more, but files, databases, and queues still hold
it.

**Example.** `_LEGACY_KEYS = {"timeout": "timeout_s"}` stays: saved 1.2
files contain `timeout`.

**Cost removed.** The alias table, and only after migration. Until then,
the alias prevents data loss.

**Verify.**

1. `verify.sh` removes the alias in a copy and shows that the saved-1.2
   test fails. Keep the alias until a migration task retires it.

## Package export alias

**Definition.** A public entry point kept for old import paths: a
`package.json` `"exports"` key, a re-exporting module, a Python
compatibility module.

**Use when.** The support policy authorizes retiring that entry point (a
major release).

**Do not use when.** You would delete only the wrapper source. The
manifest still advertises the path, and stale build output may still ship
it.

**Example.**

```json
{
  "exports": {
    ".": "./dist/index.js",
    "./legacy": "./dist/legacy.js"
  }
}
```

Remove the `"./legacy"` key, `src/legacy.ts`, and its build inclusion
together; wildcard exports such as `"./*"` can still expose old files
([Node package entry points][node-exports]).

**Cost removed.** A second public import path.

**Verify.**

1. Pack the package (`bun pm pack --dry-run` or `npm pack --dry-run`)
   and confirm `dist/legacy.js` is absent; install the archive in a clean
   project and import the supported path.

## Feature probe and polyfill

**Definition.** Runtime capability checks (`hasattr(os, "fork")`,
`typeof structuredClone === "undefined"`) and polyfills for missing APIs.

**Use when.** Every supported runtime has the capability (check the
project's browserslist, `engines`, or platform list).

**Do not use when.** The probe distinguishes platforms that are all still
supported (Windows lacks `os.fork`).

**Example.** A `structuredClone` polyfill in a project whose `engines`
requires Node 18+ (where `structuredClone` exists globally) is removable;
`hasattr(os, "fork")` in a cross-platform tool is not.

**Cost removed.** Bundle size and duplicate implementations.

**Verify.**

1. The scanner lists `feature-probe` candidates; check each against the
   platform list.

## Fully rolled-out feature flag

**Definition.** A flag that is on for everyone, so its off branch is dead
code.

**Use when.** The flag is 100% on in every environment and the rollout
plan's removal step is due.

**Do not use when.** The flag is a kill switch the team still wants.

**Example.** `if flags.enabled("new_export"):` with the flag on
everywhere for two releases.

**Cost removed.** Two code paths and their tests.

**Verify.**

1. The flag service shows 100% in all environments, and the on-path tests
   pass with the flag code removed.

## Generated compatibility surface

**Definition.** Compatibility code emitted by a generator (clients, schema
bindings, registries).

**Use when.** The generator input (schema, registry) no longer declares
the old surface.

**Do not use when.** Supported server versions still expose the old
surface, so the generated method is live.

**Example.** Remove the old operation from the OpenAPI schema and
regenerate; do not delete the generated method by hand.

**Cost removed.** Edits the next generation run would revert.

**Verify.**

1. Regenerate and diff: the method disappears only because its input did.

[up036]: https://docs.astral.sh/ruff/rules/outdated-version-block/
[tomllib]: https://docs.python.org/3/library/tomllib.html
[semver]: https://semver.org/
[node-exports]: https://nodejs.org/api/packages.html#package-entry-points
[before]: ../assets/examples/before/configlib/__init__.py
