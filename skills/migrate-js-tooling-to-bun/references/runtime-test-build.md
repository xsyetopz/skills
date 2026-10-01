# Runtime, tests, and bundling

Sources: [runtime](https://bun.com/docs/runtime),
[Node compatibility](https://bun.com/docs/runtime/nodejs-compat),
[Node-API](https://bun.com/docs/runtime/node-api),
[test runner](https://bun.com/docs/test),
[test discovery](https://bun.com/docs/test/discovery),
[test configuration](https://bun.com/docs/test/configuration),
[Jest gaps](https://github.com/oven-sh/bun/issues/1825),
[bundler](https://bun.com/docs/bundler).

## Contents

- [Script runtime](#script-runtime)
- [Node compatibility boundary](#node-compatibility-boundary)
- [Test runner](#test-runner)
- [Setup, coverage, and reports](#setup-coverage-and-reports)
- [Bundler target](#bundler-target)
- [Rollback](#rollback)

## Script runtime

- `bun run SCRIPT` runs the script but an explicit `node` command or a
  `node`-shebang CLI still runs on Node. `bun --bun run SCRIPT` puts a
  `node` symlink to Bun first on the path, so the same script text runs on
  Bun.
- Never add `--bun` while only the package manager moves; it silently
  switches the runtime. Log `process.versions.bun` at startup to show
  which runtime ran.
- `bun entry.ts` runs a file directly and is a runtime switch. Bun strips
  types without checking, so keep `bunx tsc --noEmit` in CI.

## Node compatibility boundary

- Before a runtime switch, list the Node APIs the code and dependencies
  use (POSIX sh with `rg` and `fd`; on Windows run them in Git Bash or WSL):

```sh
rg -n "(from |import\(|require\().node:" src
rg -n "(child_process|worker_threads|node:vm|node:v8|inspector)" src
fd -HI -e node . node_modules
```

- The status page lists known differences per
  module; "Fully implemented" is not a result for this project.
- Node-API addons load in Bun; addons using V8 internals are a separate
  case. Run each boundary module's tests on both runtimes, and keep Node
  for a tool that needs an API marked partial or missing.

## Test runner

- `bun test` runs `*.test.*`, `*_test.*`, `*.spec.*`, and `*_spec.*`, with
  a Jest-like API from `bun:test` (`mock`, `spyOn`, snapshots). Missing
  Jest features are tracked in the Jest gaps issue.
- Do not move a suite that needs `moduleNameMapper`, custom transforms, or
  `testEnvironment: jsdom` without an equivalent (a DOM needs happy-dom
  through preload).
- The test count on Bun must equal the old runner's; fewer means
  discovery patterns differ. A deliberate bug must fail the suite.
- Review each snapshot change; never run `bun test --update-snapshots`
  to get green.

## Setup, coverage, and reports

- `[test] preload = ["./setup.js"]` in `bunfig.toml` replaces Jest
  `setupFiles`. `bun test --coverage --coverage-reporter=lcov` writes
  `coverage/lcov.info`; `--reporter=junit --reporter-outfile=PATH` writes
  JUnit XML.
- Point the CI coverage gate and report upload at the new paths. Never
  drop a gate because the format changed; confirm it still fails below
  its threshold.

## Bundler target

- `bun build --target=browser|node|bun` picks resolution and output for
  the consumer; the default is `browser`. `--target=bun` output starts
  with `// @bun`, and `format: "cjs"` with `target: "bun"` does not run on
  Node. Run the artifact on its real consumer and compare output files,
  sizes, and source maps with the old build.
- esbuild, Rollup, or Vite plugins do not use Bun's plugin API. Port each
  plugin or keep the old bundler.

## Rollback

- One responsibility reverts as one change: lockfile, `packageManager`,
  CI setup step, image, and `bunfig.toml` keys. Try the rollback on a
  scratch branch and run the old CI command on the result, because a
  restored `package-lock.json` beside a CI that runs `bun ci` fails.
