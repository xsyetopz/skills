# OpenCode hooks

Reviewed 2026-09-12 against the official OpenCode v2 [plugin
documentation](https://opencode.ai/v2/docs/build/plugins).

OpenCode v2 exposes typed in-process plugin hooks, not the stdin/stdout command
schema used by several other harnesses. Project plugins below
`.opencode/plugins/` load automatically. External plugin paths or packages are
listed in `opencode.json(c)`. A plugin uses `Plugin.define`, registers a hook on
the relevant domain such as `ctx.tool.hook("execute.after", callback)`, and
disposes registrations during unload.

Multiple plugins run in plugin order and later hooks observe earlier changes.
Prompt admission can be retried under concurrency and is not an exactly-once
side-effect boundary. Request, HTTP, retry, and tool hooks expose different
typed events. Do not shell out merely to imitate another provider. Review all
plugin imports, package installation, network use, storage, and captured
secrets before loading repository code.

Copy `assets/opencode/index.ts` to
`.opencode/plugins/harmless-hook-observer/index.ts`, start an isolated OpenCode
session, exercise one tool, and inspect debug output for plugin loading. Delete
that plugin directory to roll back. Type-check it against the installed
OpenCode/plugin version; parsing TypeScript alone is not a host smoke test.
