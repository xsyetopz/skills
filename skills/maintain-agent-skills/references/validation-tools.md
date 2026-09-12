# Validation tool selection

Reviewed 2026-09-12 against the linked upstream documentation. Project-native
commands and configuration take precedence. Add one external tool only when it
checks a concrete artifact that existing tooling does not.

- `skills-ref`: validate Agent Skills structure and frontmatter with
  `skills-ref validate skills/name`. There is no equivalent custom schema; if
  it is unavailable, report that limit.
- `markdownlint-cli2`: apply the existing Markdown policy with
  `markdownlint-cli2 "skills/**/*.md"`. Prefer the repository's existing
  Markdown runner when present.
- `hyperfine`: compare repeated wall-clock samples with
  `hyperfine --warmup 2 --runs 10 CMD1 CMD2`. Prefer a runtime-native benchmark
  harness when the project already has one.
- `actionlint`: validate GitHub Actions syntax and expressions with
  `actionlint`. Hosted execution remains necessary for GitHub behavior.
- `shellcheck`: diagnose shell code with `shellcheck path.sh`. `bash -n` is a
  syntax-only fallback.
- `ruff`: lint and format Python with the repository's selected rules and target
  version. Run both `ruff check` and `ruff format --check`; neither replaces
  type checking or behavioral tests.
- `pyright`: run the same checked-in type configuration used by Pylance. Select
  the provisioned Python interpreter so installed validation dependencies are
  visible instead of hiding unresolved imports.

VersionLens Redux may surface newer dependency versions in supported manifests,
but its CodeLens is discovery evidence. Confirm a proposed update against the
authoritative registry, upstream compatibility notes, and the resolved lockfile
before editing a pin.

Use Python's standard JSON, TOML, XML, and plist parsers for those formats;
PyYAML is pinned only because Python has no standard YAML parser. Use the
provider's schema or native command when generic parsing cannot validate field
semantics. Security scanners remain project- and ecosystem-specific: use an
existing lockfile, dependency, secret, or static-analysis tool before adding a
second scanner, and never upload source or secrets without authorization.

Install through a verified official package/release channel. Do not pipe a
remote installer into a shell or infer a package name from a catalog. Check
whether the tool executes repository code, follows symlinks, reads secrets, or
contacts a service. Cache provisioned validation environments outside the
repository.

Primary sources:

- [`skills-ref`][skills-ref]
- [`markdownlint-cli2`][markdownlint-cli2]
- [`hyperfine`](https://github.com/sharkdp/hyperfine)
- [`actionlint`](https://github.com/rhysd/actionlint)
- [ShellCheck](https://www.shellcheck.net/)
- [Ruff](https://docs.astral.sh/ruff/)
- [Pyright](https://github.com/microsoft/pyright)
- [VersionLens Redux][versionlens-redux]

[markdownlint-cli2]: https://github.com/DavidAnson/markdownlint-cli2
[skills-ref]: https://github.com/agentskills/agentskills/tree/main/skills-ref
[versionlens-redux]: https://marketplace.visualstudio.com/items?itemName=xsyetopz.versionlens-redux
