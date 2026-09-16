# Select JavaScript package-management changes for Bun

Target-dependent reference for the supplied Bun 1.4.2 examples. This does not
establish which version is installed or selected in the target repository.
Verify the requested target against its release and installed `--help`; do not
substitute the newest release for an explicit version.

## Choose the migration surface

Inventory `packageManager`, version-manager files, CI setup actions, container
tags, executable shebangs, workspace manifests, lockfiles, and deployment
commands. Record which executable actually runs each script. Treat package
installation and runtime selection independently. For package-manager adoption,
update pins and every installer consumer. For a Bun-only upgrade, keep the
existing runtime, test runner, dependency constraints, and build ownership;
change their behavior only when required by the requested version transition.
For runtime adoption, check the compiler, type checker, and deployment contracts
separately.

Select the target version through the version manager or Bun's versioned
installer. Record `bun --version` and `bun --revision` from the resulting
executable. A `packageManager` field records intent; verify the executable
actually used instead of treating that field as version enforcement. The
[installation guide][ref-installation-guide] describes platform requirements and
version selection. Canary builds are a separate, opt-in channel.

For a pin-only transition, first try the target executable with the existing
lockfile and a frozen install in a disposable copy. Do not run `bun update` or
resolve the dependency graph merely to change a Bun version. If the target
requires a lockfile conversion, let that Bun executable generate it and compare
resolved package identities before acceptance. A newer executable working
locally does not update a CI/container pin automatically.

### Runtime pin change that also updates dependencies

**Deciding condition:** The requested change is only the Bun runtime version;
dependency versions and application behavior must remain unchanged.

```sh
bun update
bun install
```

Why it fails:

- `bun update` authorizes new dependency resolutions unrelated to the runtime
  transition;
- a passing test cannot distinguish runtime compatibility from dependency
  changes;
- CI and container pins can still use the previous executable.

### Change the pin and verify the existing graph

```sh
bun --version
bun install --frozen-lockfile
bun test
```

Why it works:

- the selected executable and existing dependency graph remain separate
  variables;
- frozen installation exposes manifest/lockfile incompatibility;
- repository tests exercise the target runtime without an incidental upgrade.

Check:

- compare the lockfile and resolved package identities before and after, then
  verify every CI, container, and version-manager pin names the target version.

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
verified. For a pre-1.2 binary lockfile, first retain a recoverable copy outside
the conversion workspace. The documented conversion is:

```sh
bun install --save-text-lockfile --frozen-lockfile --lockfile-only
```

Bun 1.4.2 removes `bun.lockb` during this conversion; do not assume both files
remain for comparison. Inspect `bun.lock` and the saved original before
acceptance. Older consumers may still require binary format: do not convert the
shared project until their compatibility or retirement is established. [Lockfile
contracts](https://bun.com/docs/pm/lockfile).

## Lifecycle, registries and workspaces

Check native-addon build output after installation. `trustedDependencies`
controls dependency lifecycle execution: omission uses Bun's curated npm list;
an explicit list **replaces** it; `[]` trusts none. Local/git dependencies need
explicit trust even when their names match a default entry. Review the actual
build script before granting it trust. `--ignore-scripts` disables scripts and
can leave a deliberately incomplete install. [Lifecycle
semantics][ref-lifecycle-semantics].

Supply scoped-registry credentials through environment interpolation:

```toml
[install.scopes]
"@example" = { url = "https://registry.example.test", token = "$PACKAGE_TOKEN" }
```

Keep `.npmrc` scope mappings, certificates and registry ownership when
converting configuration; never copy a token into the lockfile or documentation.
An authentication error is not permission to substitute the public registry.
[Registry configuration][ref-registry-configuration].

Keep the workspace root authoritative for shared installation. Run a
representative package from its own directory as well as root scripts:
accidental access to hoisted undeclared dependencies can hide a broken manifest.
Choose hoisted or isolated installation from dependency visibility requirements.
Declare dependencies that the chosen linker exposes as missing. Isolated linking
is not a proof that undeclared imports cannot resolve: the default store
fallback and root dependencies can still expose packages. Evaluate
`install.hoist = false` only when stricter dependency visibility is required,
and test the actual package import from its consuming directory.
[Workspaces](https://bun.com/docs/pm/workspaces), [isolated
installs][ref-isolated-installs].

For runtime, test-runner and bundler changes, continue with [tool
contracts](runtime-and-tooling.md).

[ref-installation-guide]: https://bun.com/docs/installation
[ref-lifecycle-semantics]: https://bun.com/docs/pm/lifecycle
[ref-registry-configuration]: https://bun.com/docs/pm/scopes-registries
[ref-isolated-installs]: https://bun.com/docs/pm/isolated-installs
