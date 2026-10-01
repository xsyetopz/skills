# Compatibility removal

Read before deleting any version branch, import fallback, deprecated
alias, stored-format reader, export alias, feature probe, polyfill, or flag.

## Contents

- [Decide](#decide)
- [Looks dead but is not](#looks-dead-but-is-not)
- [Trace consumers](#trace-consumers)
- [Remove](#remove)
- [Prove](#prove)

## Decide

Classify each candidate before editing, and do not mix classes in one
change:

- Never required: added without a requirement. Remove.
- Retired: the support policy ended it. Remove, and quote the policy line.
- Required: still supported, by a version, a consumer, or stored data. Keep.
- Unresolved: evidence is missing. Do not remove; report what is missing.

Read the support policy, not the age of the code or what CI happens to
test:

```sh
rg -n 'requires-python|python_requires' pyproject.toml setup.cfg
rg -n '"engines"|"browserslist"' package.json
rg -n 'rust-version' Cargo.toml
dotnet msbuild -getProperty:TargetFrameworks src/App/App.csproj
```

## Looks dead but is not

- Version branch (`sys.version_info`, `#if NET...`, `cfg`, `@available`):
  dead only below the declared minimum; if the minimum is undeclared or
  disputed, settle the policy first. A platform probe (Windows lacks
  `os.fork`) is live while those platforms are supported.
- Import fallback (`try: import X except ImportError`): live when it guards
  an optional dependency the project supports running without, such as an
  optional C accelerator.
- Deprecated alias that warns and forwards: live in a published API until
  the release named by the deprecation policy; removal is an incompatible
  change, not a cleanup.
- Persisted or serialized alias (old config keys, enum values, columns,
  queue messages): live while files, databases, or queues may still hold
  the old form, even when no code writes it any more. Example: a
  `_LEGACY_KEYS = {"timeout": "timeout_s"}` map stays while saved files
  with `timeout` exist. Check snapshots of production data, fixtures under
  `stored/` or `data/`, and migration scripts; retire the reader only
  after a migration or a policy that ends support for that data.
- Package export alias (`exports`, re-export module): deleting the wrapper
  source leaves the manifest entry and stale build output shipping it.
- Feature probe or polyfill (`hasattr`, `typeof`, a `structuredClone`
  polyfill): removable only when every supported runtime has the feature.
- Rolled-out flag: a kill switch the team still wants is live.
- Generated compatibility surface: remove the operation from the schema
  and regenerate; do not delete generated methods by hand.

## Trace consumers

An empty local search is not proof for a published API, since it cannot see
external consumers. Search:

```sh
rg -n '\bname\b'
rg -n '"name"' --glob '*.{toml,yaml,json,cfg}'
git log -S 'name' --oneline -n 10
```

Cover imports and re-exports, strings (config, CLI registration,
reflection, plugin discovery), generated registries, tests, packaging and
deployment files, docs, persisted data, and external users. List each place
found and its kind. A code graph index counts only when fresh.

## Remove

Remove the path with its registrations, dedicated tests, fixtures, docs,
manifest entries, and dependencies (dropping a `tomllib` fallback also
drops `tomli`; removing `./legacy` also drops its `exports` key). Keep
shared code that supported paths use. Leave no forwarding wrapper, hidden
flag, or catch-all to keep a test green. Removing a supported public API
ships in a major release under Removed in the changelog
([SemVer](https://semver.org/)).

## Prove

- `rg` finds no reference to the removed names or files.
- Tests pass on the minimum supported version and the latest, with
  deprecation warnings as errors:

```sh
python3 -W error::DeprecationWarning -m unittest
uv run --python 3.11 --no-project python -m unittest  # the minimum version
```

- When exports changed, inspect the packaged artifact (`npm pack --dry-run`,
  the built wheel), not just the source tree.
