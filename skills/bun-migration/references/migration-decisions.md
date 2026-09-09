# Bun version and package-manager migration

Research: 2026-09-09. Default for a new migration is stable **Bun 1.4.2**, as
identified by the [release announcement](https://bun.com/blog/bun-v1.4.2).
Refresh the affected section for an older target, a newer lockfile schema, or an
API absent here.

## Choose the migration surface

Inventory `packageManager`, version-manager files, CI setup actions, container
tags, executable shebangs, workspace manifests, lockfiles, and deployment
commands. Record which executable actually runs each script. Treat package
installation and runtime selection independently. For a pin-only request, update
pins and their consumers. For runtime adoption, check the compiler, type
checker, and deployment contracts separately.

Select the target version through the version manager or Bun's versioned
installer. Record `bun --version` and `bun --revision` from the resulting
executable. The [installation guide](https://bun.com/docs/installation)
describes platform requirements and version selection. Canary builds are a
separate, opt-in channel.

## Preserve dependency resolution

At the workspace root, with the selected Bun available:

```sh
bun install --lockfile-only
bun install --frozen-lockfile
```

The first command resolves/writes metadata without installing `node_modules`,
but can populate the global cache. The frozen install must fail on
manifest/lockfile disagreement. Compare package versions, registry URLs,
workspace edges, optional platform packages and overrides with the previous
graph before removing the old lockfile.

Current automatic migration accepts Yarn v1, npm lockfileVersion 2/3/4, and pnpm
lockfiles when `bun.lock` is absent. npm v1 falls back to manifest resolution,
so a successful install can still change the graph. Preserve the original until
verified. For a pre-1.2 binary lockfile, the documented conversion is:

```sh
bun install --save-text-lockfile --frozen-lockfile --lockfile-only
```

Inspect `bun.lock`, then remove `bun.lockb` only after all consumers accept the
text format. Older Bun consumers may still require the binary file; do not
mechanically delete it in a mixed-version project.
[Lockfile contracts](https://bun.com/docs/pm/lockfile).

## Lifecycle, registries and workspaces

Check native-addon build output after installation. `trustedDependencies`
controls dependency lifecycle execution: omission uses Bun's curated npm list;
an explicit list **replaces** it; `[]` trusts none. Local/git dependencies need
explicit trust even when their names match a default entry. Review the actual
build script before granting it trust. `--ignore-scripts` disables scripts and
can leave a deliberately incomplete install. [Lifecycle semantics][ref-1].

Supply scoped-registry credentials through environment interpolation:

```toml
[install.scopes]
"@example" = { url = "https://registry.example.test", token = "$PACKAGE_TOKEN" }
```

Keep `.npmrc` scope mappings, certificates and registry ownership when
converting configuration; never copy a token into the lockfile or documentation.
An authentication error is not permission to substitute the public registry.
[Registry configuration][ref-2].

Keep the workspace root authoritative for shared installation. Run a
representative package from its own directory as well as root scripts:
accidental access to hoisted undeclared dependencies can hide a broken manifest.
Choose hoisted or isolated installation from dependency visibility requirements.
Declare dependencies that the chosen linker exposes as missing.
[Workspaces](https://bun.com/docs/pm/workspaces), [isolated installs][ref-3].

For runtime, test-runner and bundler changes, continue with
[tool contracts](runtime-and-tooling.md).

[ref-1]: https://bun.com/docs/pm/lifecycle
[ref-2]: https://bun.com/docs/pm/scopes-registries
[ref-3]: https://bun.com/docs/pm/isolated-installs
