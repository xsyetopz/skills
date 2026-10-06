# Package catalog

The catalog lists packages by ecosystem and domain.
Each row holds facts read from a registry or a GitHub repository.
It holds no ratings and no recommendations.
Choosing between packages stays with the person configuring the project.

## Contents

- [Files](#files)
- [Row fields](#row-fields)
- [Status](#status)
- [Traits](#traits)
- [Commands](#commands)
- [Rules for adding rows](#rules-for-adding-rows)

## Files

All files live in `assets/packages/`.

| File | Facts come from |
| --- | --- |
| `npm.jsonl` | packument, last-month downloads, bulk advisories |
| `crates.jsonl` | crates.io API, `.crate` manifest, RustSec advisory-db |
| `nuget.jsonl` | registration index, search service |
| `go.jsonl` | module proxy, `go.mod`, module zip, vuln.go.dev |
| `schema.json` | JSON Schema 2020-12 for one row, including the domains |

One JSON object per line, sorted by `(domain, name)`, each file under 400 KB.
Rows are written compactly so that a refresh changes only the lines whose facts changed.

## Row fields

Unknown values are `null`.
A field is never guessed.

| Field | Meaning |
| --- | --- |
| `ecosystem` | `npm`, `crates`, `nuget`, or `go` |
| `name` | package name, crate name, package id, or module path |
| `domain` | one term from the `domain` enum in `schema.json` |
| `status` | derived, see below |
| `latest` | newest stable version, `null` for a `prerelease` row |
| `released` | date of that version, `YYYY-MM-DD` |
| `license` | SPDX expression from the registry; Go reads it from GitHub |
| `repository` | normalized `https://` URL |
| `archived` | GitHub archived flag, `null` without GitHub data |
| `pushed` | date of the last push to the repository |
| `deprecation` | deprecation message, at most 200 characters |
| `replacement` | package that the registry or the message names, else `null` |
| `advisories` | ids of advisories that affect `latest` |
| `downloads` | npm last month, crates recent, NuGet total; Go has none |
| `deps` | direct dependency count of `latest` |
| `traits` | per-ecosystem facts, below |
| `verified` | local date of the run that wrote the row |

`downloads` is not comparable across ecosystems.
Compare it only inside one file.

## Status

The first matching rule wins.

1. `missing`: the registry has no such package.
1. `deprecated`: one of these holds.
   - npm or NuGet marks the package deprecated, or NuGet has unlisted `latest`.
   - crates.io yanked `latest`, or RustSec lists an unmaintained advisory against it.
   - A Go module has a `// Deprecated:` comment, or retracts `latest`.
1. `archived`: the repository is archived on GitHub.
1. `prerelease`: the package has no stable release, so `latest` and `released` are `null`.
   A deprecation or an archived repository still wins over this status.
1. `stale`: `released` is more than 730 days before `verified`.
1. `active`: none of the above.

Only `active` rows have a stable release that is recent and not deprecated.
A `prerelease` row lists a package that ships only prerelease versions or Go pseudo-versions.
Add it only after reading what those versions promise.

A fact that is `null` never moves a row down the list.
A row can therefore be `active` because the repository could not be read.

## Traits

| Ecosystem | Keys | Source |
| --- | --- | --- |
| npm | `types`, `module`, `engines` | `types`, `exports`, `type` in the manifest |
| crates | `msrv`, `noStd`, `procMacro` | `rust_version`, `no-std` category, `[lib]` |
| nuget | `frameworks`, `aot` | target frameworks; `aot` is always `null` |
| go | `goVersion`, `cgo` | `go.mod` go line, `import "C"` in the zip |

`npm.module` is `dual` when `exports` offers both `import` and `require` conditions.

## Commands

Run from the skill directory with Python 3.10 or newer.
The script uses only the standard library.

```sh
python scripts/package_catalog.py query --ecosystem crates --domain http-client --status active
python scripts/package_catalog.py query --name serde --json
python scripts/package_catalog.py domains
python scripts/package_catalog.py add --ecosystem npm --name zod --domain validation
python scripts/package_catalog.py refresh --ecosystem go
```

- `query` filters by ecosystem, domain, status, and name substring.
  Active rows come first, then higher `downloads`, then name.
  The table shows 40 rows by default; `--limit 0` shows all, `--json` prints rows.
- `domains` lists each domain with its row count.
- `add` fetches one package, or a JSONL file of `{name, domain}` with `--from`.
  It skips names that are already present.
- `refresh` fetches every row again.
  A row whose fetch fails keeps its old facts, and the command exits with status 1.
  `--limit N` refreshes only the first N rows.

Set `GITHUB_TOKEN` in the environment before a large run.
Without it the script skips GitHub.
Then `archived` and `pushed` are `null`, and so is the Go `license`.
The script never writes the token anywhere.
crates.io is read at one request per second, so a crates refresh takes several minutes.

## Rules for adding rows

- Take names from the user or from the project, not from another catalog.
- Add packages, not framework APIs.
  A name that the registry lacks is stored as `missing`, so check the id first.
- Pick the domain from the schema enum.
  Add a domain only together with a change to `schema.json`.
- Run `add` and keep the result.
  Do not edit facts by hand, because the next `refresh` overwrites them.
