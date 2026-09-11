# Language assets, debugger adapters and other contributions

Research: 2026-09-11; Zed 1.19.2 documentation with published extension API
0.7.0. Use assets and APIs supported by the selected host.

## Grammar and query ownership

`languages/example/config.toml` supplies `name="Example"`, `grammar="example"`,
`path_suffixes=["ex"]` and comment/indent metadata. `path_suffixes` is not a
glob language. Register `[grammars.example]` in `extension.toml` with a real
Tree-sitter repository and immutable `rev`, plus `path` for a grammar below
repository root. A grammar update can change node names even if the manifest
still parses. [Language contract](https://zed.dev/docs/extensions/languages).

In `highlights.scm`, `(comment) @comment` is valid only if that grammar defines
a named `comment` node. `outline.scm` uses `@item` for the structural range and
`@name` for its label. `brackets.scm` uses `@open`/`@close`; `indents.scm` uses
indentation ranges; `injections.scm` maps embedded content and language
identity. Do not copy a query from another grammar with similar syntax. Test
malformed/incomplete input, nested constructs, strings/comments containing
delimiters and injected languages.

For language-specific settings, prefer configuration and scope overrides to a
procedural hook when supported. A query parses against a grammar, while visual
correctness depends on representative source and theme capture support. Keep
optional query files absent when the language has no meaningful corresponding
structure.

## Debug adapter registration

Register `[debug_adapters.example]` with
`schema_path="debug_adapter_schemas/example.json"`; a configuration schema is
mandatory even when the path defaults. Implement `get_dap_binary` to return the
adapter command/configuration, honoring a user-provided adapter path.
`dap_request_kind` must distinguish launch from attach and error on an
indeterminate request rather than silently launching a process.
`dap_config_to_scenario` maps the generic new-process UI into adapter-specific
configuration.
[Debugger extensions](https://zed.dev/docs/extensions/debugger-extensions).

A debug locator maps a build/run task to a debug scenario. Reject unrelated
tasks cheaply in `dap_locator_create_scenario`. For a compiled target, return a
build task and use `run_dap_locator` after successful build to resolve the
actual artifact path; do not guess hashed build-output names. For an interpreted
program with a known path, omit the build phase. Launching a debuggee and
attaching to an existing process have different ownership/termination contracts.

Validate the schema's required fields, adapter path, program/cwd/arguments,
initialization and disconnect behavior in a Dev Extension. Protocol support does
not imply every host UI exposes every DAP capability. Preserve stderr for
diagnostics and keep protocol stdout clean.

## Themes, icons, snippets and MCP

Theme JSON describes a family and theme entries with names, appearance and style
values. Use the current schema and semantic style keys; test selection,
diagnostics, inactive UI and contrast rather than recoloring only the editor
background. Icon themes map file/directory identities to bundled assets. Keep
referenced paths inside the package and provide meaningful fallback icons.
[Themes](https://zed.dev/docs/extensions/themes),
[icon themes](https://zed.dev/docs/extensions/icon-themes).

Snippets under `snippets/` use named entries with prefix/body/description and
language-specific files where appropriate. Preserve tab-stop/placeholder
semantics and test insertion in the target language; a syntax-highlighting
package does not automatically register snippets.
[Snippets](https://zed.dev/docs/extensions/snippets).

MCP contributions register a context server and implement the compatible
`context_server_command`/configuration hooks. The host launches the returned
command; validate settings and keep credentials in the intended secure user
mechanism, not manifest defaults. Declare required inputs in the configuration
schema and return actionable validation errors. Do not promise arbitrary
in-editor UI from an MCP server.
[MCP extensions](https://zed.dev/docs/extensions/mcp-extensions).

Keep user state migration explicit when a setting/adapter ID changes: read and
validate old data, convert once, and preserve unsupported/unknown fields rather
than silently resetting them. Document unsupported parity as a capability
boundary. For a new hook present only in unpublished source, label it separately
and do not make it a stable install dependency.
