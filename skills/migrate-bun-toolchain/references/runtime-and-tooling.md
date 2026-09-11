# Runtime, tests, and build contracts

Research: 2026-09-11. Verify changed behavior on the selected Bun release.

## Runtime switch

Compare the existing invocation with `bun path/to/entry.ts`.
`bun run script-name` executes the package script; it does not guarantee a
script's explicit `node` invocation or a CLI's Node shebang uses Bun.
`bun --bun run script-name` forces Bun for Node-based executables reached
through that mode; use it only when that runtime change is intended.
[Runtime commands](https://bun.com/docs/runtime).

Exercise public behavior at compatibility boundaries: CommonJS/ESM export
shapes, conditional exports, native Node-API modules, child-process signals and
exit codes, stream backpressure, TLS certificates, filesystem errors, and
shutdown with pending work. Verify each affected dependency against the APIs it
calls. Keep Node for a subprocess or tool that relies on an unsupported API.
Native addons using V8 internals are a different compatibility problem from
Node-API addons.
[Node compatibility](https://bun.com/docs/runtime/nodejs-compat),
[Node-API](https://bun.com/docs/runtime/node-api).

For a server, launch on an available local port with disposable storage, send
representative successful and failing requests, then exercise graceful
termination. Compare response status, headers, bytes and persisted effects. Test
startup configuration separately: fail on missing required environment values
instead of selecting a production database. Complete server compatibility checks
before switching deployment entrypoints.

## Test-runner migration

Map discovery patterns, setup order, mock isolation, snapshots, timers, coverage
consumers and reporter output before replacing the runner. Run the affected
suite when changing discovery, setup, mocks, or runner behavior.
`bun test --coverage` requests coverage; preserve required thresholds and
formats rather than removing CI consumers. Configure setup through
`[test] preload = ["./test/setup.ts"]` in `bunfig.toml` when needed. Bun
provides Jest-like APIs, not complete Jest configuration compatibility. DOM
tests require the chosen DOM environment; executing TypeScript does not supply a
browser. [Test runner](https://bun.com/docs/test),
[configuration](https://bun.com/docs/test/configuration).

Run `tsc --noEmit` or the configured checker separately from transpiled tests.
Do not regenerate all snapshots to conceal semantic differences; inspect
expected changes individually.

## Bundler migration

Build an entrypoint deployed on Bun:

```sh
bun build ./src/server.ts --target=bun --outdir=./dist --sourcemap=external
```

Select `browser`, `node` or `bun` according to the consumer. Map entrypoints,
module format, externals, splitting, loaders, asset paths, and source maps to
Bun build options. Browser output must not import server APIs. Inspect bundled
resources and run the packaged entrypoint to check runtime-loaded files.
Existing esbuild/Rollup/Vite plugins do not automatically implement Bun's plugin
API. [Bundler contracts](https://bun.com/docs/bundler).

Verify each changed command and its output artifact. Report remaining
compatibility failures. Roll back pins, lockfile and consumers together if the
requested switch fails; preserve intentional independent changes. Refresh only
the particular unsupported API/plugin or a different target-version contract.
