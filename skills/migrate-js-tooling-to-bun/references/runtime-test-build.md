# Runtime, tests, and bundling

Cards for moving script execution, the test runner, or the bundler to
Bun, each a responsibility separate from the package manager.
"Executed" results come from [`assets/examples/verify.sh`][verify] with
Bun 1.4.2 and Node 26.8.2 on macOS arm64.

## Contents

- [Script runtime: bun run and --bun](#script-runtime-bun-run-and---bun)
- [Direct entry point on Bun](#direct-entry-point-on-bun)
- [Node compatibility boundary](#node-compatibility-boundary)
- [Test runner switch](#test-runner-switch)
- [Test setup, coverage, and reports](#test-setup-coverage-and-reports)
- [Bundler target](#bundler-target)
- [Rollback unit](#rollback-unit)

## Script runtime: bun run and --bun

**Definition.** `bun run <script>` runs a `package.json` script without
changing the runtime of the script's own command: an explicit `node`
command, or a CLI with a `node` shebang, still runs on Node.
`bun --bun run <script>` puts a `node` symlink to Bun ahead of Node on
the script's path, so those commands run on Bun ([runtime][runtime]).

**Use when.** `bun run` moves the script runner alone. Add `--bun` only
when the runtime moves too.

**Do not use when.** Never add `--bun` to CI while only the package
manager moves; it silently switches the production runtime.

**Example.** Executed. `"start": "node packages/app/index.js"`:

```text
$ bun run start
$ node packages/app/index.js
hello-world (node 26.8.2)
$ bun --bun run start
$ node packages/app/index.js
hello-world (bun 1.4.2)
```

The script text is identical in both runs; only the runtime changes.

**Cost removed.** Believing a service runs on Bun when it runs on Node,
or the reverse. `process.versions.bun` shows which.

**Verify.**

1. The entry point logs its runtime once at startup, and the line
   matches the responsibility table.

## Direct entry point on Bun

**Definition.** `bun path/to/entry.ts` runs a file on Bun, transpiling
TypeScript and JSX without a build step. It is a runtime switch.

**Use when.** The requested change is "run the service on Bun" and the
[compatibility boundary](#node-compatibility-boundary) checks pass.

**Do not use when.** Type checking is expected. Bun strips types without
checking them, so `tsc --noEmit` (or the configured checker) remains a
separate CI step.

**Example.**

```sh
bun packages/app/index.js          # runtime switch
bunx tsc --noEmit                  # still required for .ts projects
```

**Cost removed.** The transpile step before start. Measure it as the
wall time of `build && start` against `bun entry` on the same inputs.

**Verify.**

1. Start a server on a free port with disposable storage, send one
   valid and one invalid request, then stop it with SIGTERM.
1. Compare the status codes, bodies, and exit code with the Node run.

## Node compatibility boundary

**Definition.** The Node APIs the project and its dependencies call,
checked against Bun's per-module status. The status page tracks Node.js
v26 and lists known differences per module
([Node compatibility][compat]); for example, `console` output bypasses a
replaced `process.stdout.write`. Native addons built on Node-API load in
Bun; addons that use V8 internals are a separate case
([Node-API][node-api]).

**Use when.** Before any runtime switch, for each dependency that does
I/O, uses native code, or spawns processes.

**Do not use when.** Treating "Fully implemented" on the page as a test
result for this project.

**Example.**

```sh
rg -n "from ['\"]node:" src
rg -n "(child_process|worker_threads|node:vm|node:v8|inspector)['\"]" src
fd -e node . node_modules | head
```

For each module found, run the tests that exercise it on both
runtimes. Keep Node for a tool that relies on an API marked partially
implemented or missing.

**Cost removed.** Production failures in code paths no test ran; they
appear as new errors in the comparison run.

**Verify.**

1. The report lists each boundary module with the test that ran it on
   Bun.

## Test runner switch

**Definition.** `bun test` runs files named `*.test.*`, `*_test.*`,
`*.spec.*`, and `*_spec.*`. Its Jest-like API, imported from `bun:test`
or used as globals, includes `mock`, `spyOn`, and snapshots. Bun tracks
missing Jest features in [issue 1825][jest-compat]
([test runner][test], [discovery][discovery]).

**Use when.** The requested change is the test runner, and the suite
uses Jest-style APIs or `node:test` patterns that Bun supports.

**Do not use when.** The suite depends on Jest configuration without a
Bun equivalent, such as `moduleNameMapper`, custom transforms, or
`testEnvironment: jsdom`. A DOM environment needs its own setup, such
as happy-dom through preload.

**Example.** Executed ([`slug.test.js`][slug-test]):

```js
import { describe, expect, it, mock } from "bun:test";
import { slug } from "@fixture/util";

describe("slug", () => {
  it("lowercases and joins words", () => {
    expect(slug("  Hello   World ")).toBe("hello-world");
  });

  it("supports jest-style mocks", () => {
    const fn = mock((x) => x * 2);
    fn(2);
    expect(fn).toHaveBeenCalledTimes(1);
  });
});
```

**Cost removed.** The transform pipeline, such as babel-jest or
ts-jest. Measure full-suite wall time on both runners with the same
test set, and report how many tests ran on each.

**Verify.**

1. Bun runs as many tests as the old runner. Fewer means the discovery
   patterns differ.
1. A deliberate bug fails the suite; `verify.sh` changes `slug()` and
   requires a failure.
1. Review snapshot changes one by one. Never run
   `bun test --update-snapshots` to make the suite pass.

## Test setup, coverage, and reports

**Definition.** `[test] preload` in `bunfig.toml` runs setup files
before any test. `--coverage` with `--coverage-reporter=lcov` writes
`coverage/lcov.info`. `--reporter=junit --reporter-outfile=<path>`
writes JUnit XML ([test configuration][test-config]).

**Use when.** The old runner had `setupFiles`, a coverage threshold, or
a CI test-report consumer.

**Do not use when.** Never drop a CI coverage gate because the format
changed; point it at the new file.

**Example.** Executed:

```toml
[test]
preload = ["./setup.js"]
```

```sh
bun test --coverage --coverage-reporter=lcov
bun test --reporter=junit --reporter-outfile=./bun.xml
```

`verify.sh` asserts that the preload global is set and that
`SF:packages/util/index.js` is in the lcov file.

**Cost removed.** CI gates that silently stop checking, visible as a
missing coverage or report artifact in the CI run.

**Verify.**

1. The CI coverage and report steps read the new paths and still fail
   below their threshold.

## Bundler target

**Definition.** `bun build --target=browser|node|bun` selects resolution
rules and output for the consumer; the default is `browser`.
`--target=bun` output starts with the `// @bun` pragma, and
`format: "cjs"` with `target: "bun"` does not run on Node
([bundler][bundler]).

**Use when.** The requested change is the bundler and the bundle's
consumer is known.

**Do not use when.** The build depends on esbuild, Rollup, or Vite
plugins, which do not implement Bun's plugin API. Port each plugin or
keep the old bundler.

**Example.** Executed:

```sh
bun build packages/app/index.js --target=node --outdir=dist
node dist/index.js   # hello-world (node 26.8.2)
```

**Cost removed.** A second build tool in the dependency tree. Compare
build wall time and output size (`ls -l dist`) with the old bundler.

**Verify.**

1. Run the built artifact on its actual consumer.
1. Compare the list of output files, their sizes, and the source maps
   with the old build.

## Rollback unit

**Definition.** The files that move together for one responsibility
and revert as one change. For the package manager: the lockfile,
`packageManager`, the CI setup step, the image, and any `bunfig.toml`
keys.

**Use when.** Planning the change and reporting it.

**Do not use when.** The responsibility was not part of this change.

**Example.**

```sh
git restore --source=HEAD~1 -- bun.lock package-lock.json package.json \
  .github/workflows/ci.yml Dockerfile
```

**Cost removed.** Partial rollbacks, such as a restored
`package-lock.json` beside CI that still runs `bun ci`. Running the old
CI command on the rolled-back tree catches them.

**Verify.**

1. The report names the rollback command, run once on a scratch
   branch.

[verify]: ../assets/examples/verify.sh
[slug-test]: ../assets/examples/fixture/packages/app/slug.test.js
[runtime]: https://bun.com/docs/runtime
[compat]: https://bun.com/docs/runtime/nodejs-compat
[node-api]: https://bun.com/docs/runtime/node-api
[test]: https://bun.com/docs/test
[discovery]: https://bun.com/docs/test/discovery
[jest-compat]: https://github.com/oven-sh/bun/issues/1825
[test-config]: https://bun.com/docs/test/configuration
[bundler]: https://bun.com/docs/bundler
