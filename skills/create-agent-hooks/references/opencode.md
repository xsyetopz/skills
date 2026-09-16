# Configure OpenCode coding-agent plugin events

Read the executable's version before selecting a fixture. OpenCode v1
(`opencode`) and v2 beta (`opencode2`) have different plugin interfaces;
TypeScript syntax checking cannot establish that either loads in a host.

## V2 beta

Use `assets/opencode/index.ts`. Import `Plugin` from `@opencode-ai/plugin`,
export `Plugin.define(...)` as the default, and register
`ctx.tool.hook("execute.after", ...)` inside `setup`. Do not import the
nonexistent example package `@opencode/plugin`. A registration is scoped to the
plugin and cleaned up by the runtime. Return a cleanup function only for
resources this plugin owns, such as a timer or socket; do not invent
`.dispose()` on the hook-registration result.

Copy to `.opencode/plugins/local-observe/index.ts` in an isolated test project.
V2 discovers direct plugin files and immediate child directories with an index.
The native config key for explicitly listed plugins is `plugins` (plural).
Provision local dependencies explicitly against the selected beta: local plugin
dependencies are not automatically installed. Do not pin `next` as though it
were a reproducible release. Keep the executable and plugin package compatible.

Verify registration with `opencode2 api get /api/plugin`, exercise a tool, and
inspect runtime diagnostics. The fixture intentionally produces no output; a
lack of output alone is not evidence of registration. An event hook is not an
exactly-once transaction boundary. Do not perform irreversible effects in a
retryable admission callback without a separate idempotency contract.

## V1

Use `assets/opencode-v1/observe.ts`, copied to `.opencode/plugins/observe.ts`.
This exports a named async `Plugin` function returning a hook object with
`"tool.execute.after"`. Its package is also `@opencode-ai/plugin`, but use the
version appropriate for v1. The config key is `plugin` (singular). Do not
combine v1 configuration and v2 source because their package names happen to
match.

Both fixtures are deliberately inert registration examples, not access-control
mechanisms. Inspect imported code and dependencies before loading. Delete only
the fixture file/directory to roll back; do not remove the user's unrelated
plugins.

Sources checked 2026-09-15: [v2 plugins][ref-v2-plugins], [v2
setup](https://opencode.ai/v2/docs/get-started), [v1
plugins](https://opencode.ai/docs/plugins/). Host execution was not available in
this repository's validation environment.

[ref-v2-plugins]: https://opencode.ai/v2/docs/build/plugins
