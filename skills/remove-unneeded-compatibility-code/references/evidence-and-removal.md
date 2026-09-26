# Evidence and removal

Deciding whether a candidate is removable, removing it completely, and
proving that nothing supported broke.

## Contents

- Support policy
- Consumer tracing
- Classification
- Complete removal
- Version impact
- Proof after removal

## Support policy

**Definition.** The declared range of versions, platforms, and data the
project supports: manifest fields, docs, and release policy.

**Use when.** Always, before judging any candidate.

**Do not use when.** Never infer support from what CI happens to test or
from the age of the code.

**Example.**

```sh
rg -n 'requires-python|python_requires' pyproject.toml setup.cfg
rg -n '"engines"|"browserslist"' package.json
dotnet msbuild -getProperty:TargetFrameworks src/App/App.csproj
rg -n 'rust-version' Cargo.toml
```

**Cost removed.** Removing support someone still relies on, or keeping
support nobody promised.

**Verify.**

1. The report quotes the policy line that makes the candidate dead.

## Consumer tracing

**Definition.** Every way a candidate can be reached: imports, re-exports,
string references (config, CLI registration, reflection, plugin
discovery), generated registries, tests, deployment files, persisted data,
and external consumers of published packages.

**Use when.** Every candidate.

**Do not use when.** Never treat an empty search as proof for a published
API; local search cannot see external consumers.

**Example.**

```sh
rg -n '\bload_config\b'
rg -n '"load_config"|load_config' --glob '*.{toml,yaml,json,cfg}'
git log -S 'load_config' --oneline | head
```

**Cost removed.** Breaking a caller the first search missed.

**Verify.**

1. List each place found and its kind. Rely on a code graph index only
   when it is fresh.

## Classification

**Definition.** Each candidate is one of: never required (added without a
requirement), retired (policy ended its support), required (still
supported), or unresolved (evidence missing).

**Use when.** Always, before editing.

**Do not use when.** Never invent a deprecation cycle for support that
never existed, or remove an unresolved external surface without a
decision.

**Example.** Worked package: import fallback and version branch are
retired (minimum is 3.11); `load_config` is retired (deprecated in 1.2,
removal planned for 2.0, no callers); the `timeout` key alias is required
(saved 1.2 files).

**Cost removed.** Mixed decisions in one change.

**Verify.**

1. The report lists every candidate with its class and evidence.

## Complete removal

**Definition.** Remove the obsolete path with its registrations,
dedicated tests, fixtures, docs, packaging entries, and dependencies.
Keep shared code that supported paths use.

**Use when.** A candidate is classified never required or retired.

**Do not use when.** Never leave a forwarding wrapper, hidden flag, or
catch-all fallback to keep a test passing.

**Example.** Removing the `tomllib` fallback also removes `tomli` from the
dependency list; removing `./legacy` also removes its `exports` key.

**Cost removed.** Half-removed paths that still ship.

**Verify.**

1. `rg` finds no remaining reference to the removed names or files;
   the build and packaging output no longer contain them.

## Version impact

**Definition.** Removing a supported public API or behavior is an
incompatible change (MAJOR under [SemVer][semver]). Removing internal or
never-public code is not.

**Use when.** Writing the changelog entry and choosing the release.

**Do not use when.** Never treat a deprecation warning as the end of the
promise; the policy's removal version ends it.

**Example.** `load_config` removal ships in 2.0.0 (the worked package bumps
its version); the internal version branch could ship in any release.

**Cost removed.** Breaking consumers in a minor release.

**Verify.**

1. The changelog entry sits under Removed in the major release.

## Proof after removal

**Definition.** Run the same tests on the minimum and latest supported
versions, with deprecation warnings as errors, and inspect the packaged
artifact.

**Use when.** After every removal.

**Do not use when.** Never rely on source-tree tests alone for packaging
changes.

**Example.**

```sh
python3 -W error::DeprecationWarning -m unittest
uv run --python 3.11 --no-project python -m unittest  # minimum version
```

**Cost removed.** Regressions found by users.

**Verify.**

1. `verify.sh` runs the tests on before and after and shows 0 remaining
   candidates in `after/`. Measured: the `after/` tests also passed under
   Python 3.11.16 via `uv run --python 3.11`.

[semver]: https://semver.org/
