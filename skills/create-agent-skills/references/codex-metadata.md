# Codex 0.154.0 skill metadata

Read this when creating or updating `agents/openai.yaml` for Codex 0.154.0. The
portable entrypoint remains `SKILL.md`. This native host file supplies interface
metadata, invocation policy, and concrete MCP dependencies; it is not a
replacement instruction file or a custom skill schema.

Version basis: OpenAI's [build-skills guide][guide] and the [`rust-v0.154.0`
bundled field reference][fields], [interface resolver][interface], [metadata
loader][loader], and [skill model][model]. Use the installed client's version
when targeting another release. Do not infer support from an unversioned example
or a permissive YAML parser.

## Interface

```yaml
interface:
  display_name: "Optimize Python Code"
  short_description: "Profile and optimize Python without changing behavior"
  default_prompt:
    "Use $optimize-python-code to profile this workload before changing it."

```

Use the actual directory-matching skill name in `default_prompt`. Keep the
prompt to a short starting request; it does not grant permission to mutate
resources, change project scope, or override higher-priority instructions. Quote
string values; keep booleans typed and keys unquoted.

- `display_name`: concise human label; the resolver accepts at most 64
  characters after whitespace normalization.
- `short_description`: the bundled authoring guidance recommends 25-64
  characters. The runtime accepts up to 1024; that broader acceptance is not a
  reason to use the UI field as another instruction body.
- `default_prompt`: a helpful invocation example containing `$skill-name`; the
  resolver's limit is 1024 normalized characters.
- `icon_small`, `icon_large`, and `brand_color` are optional presentation
  fields. Add them only when the user or product package explicitly requires
  visual branding. Do not generate icons, logos, or colors merely to populate
  optional metadata. When requested, keep icon paths under `assets/`, reject
  absolute or parent-traversal paths, verify that files exist, and use exactly
  `#RRGGBB` for the color.

Appearance fields do not improve the model's instructions, force skill
selection, or establish affiliation. Implicit matching depends on the `SKILL.md`
description, not an icon or UI blurb.

## Invocation policy

`allow_implicit_invocation` defaults to `true`. Preserve that behavior unless
explicit-only selection is requested or an intentional catalog decision is made.
`false` removes the skill from default model context while leaving explicit
`$skill-name` invocation available. It is not an execution permission, approval
mechanism, or security boundary. Keep consequential-operation limits in the
actual procedure.

The 0.154.0 parser also accepts `policy.products`; the skill model contains a
TODO about enforcing product gating in selection/injection. Do not use that
field as an enforced product restriction or security control. Omit it when there
is no verified need. Parsing a field is not evidence of enforcement.

## MCP dependencies

Declare a dependency only when this skill genuinely requires that specific MCP
server. Do not install a provider merely to populate optional metadata. Python,
Bun, Git, compilers, CLIs, and operating-system prerequisites are not MCP
dependencies; state them in instructions or standard `compatibility` metadata.
Do not label them as invented dependency types.

For a workflow that actually requires the OpenAI documentation server:

```yaml
dependencies:
  tools:
    - type: "mcp"
      value: "openaiDeveloperDocs"
      description: "OpenAI documentation MCP server"
      transport: "streamable_http"
      url: "https://developers.openai.com/mcp"
```

This is a conditional authoring example, not a dependency to copy into every
skill. A workflow supporting several providers must not require all of them.
When the task can use existing native APIs or CLI access, do not invent a fixed
MCP dependency. The metadata has no documented per-workflow conditional
expression to use as an escape hatch.

The tagged loader additionally reads `command` and `oauth.callbackPort`
(`callback_port` is accepted as an alias). Use them only for a verified MCP
transport and OAuth callback requirement. A callback port is an unsigned 16-bit
integer; never invent a port, command, endpoint, credential, or account.
Metadata declaration does not establish installation, authentication, or
successful tool registration. Verify the connection in the actual host before
claiming it works.

## Update and verification

1. Read the existing descriptor. Update intended fields in place and preserve
   unrelated policy or dependencies. Do not add icons, branding, license text,
   or comments unless the user or packaging contract requires them.
1. Parse YAML with duplicate-key rejection, check the target version's field
   names and scalar types, and resolve every local asset path.
1. Check the display/prompt limits, `$skill-name`, color format, complete
   dependency identity, and absence of embedded secrets. Do not use a generator
   that overwrites the file as a validator.
1. Use the repository's existing validation commands. In an actual Codex 0.154.0
   installation, inspect `/skills`, explicit invocation, implicit selection, and
   any required MCP tools. Keep static and host results separate.

The 0.154.0 loader fails open on missing or malformed optional metadata: it can
load `SKILL.md` while ignoring the descriptor. A visible skill therefore does
not prove that its policy, dependencies, or interface settings were accepted.
Invalid optional strings can also be discarded by the resolver. Report
unsupported or rejected requested settings instead of silently dropping them.

[guide]: https://learn.chatgpt.com/docs/build-skills
[fields]: https://github.com/openai/codex/blob/rust-v0.154.0/codex-rs/skills/src/assets/samples/skill-creator/references/openai_yaml.md
[interface]: https://github.com/openai/codex/blob/rust-v0.154.0/codex-rs/skills/src/interface.rs
[loader]: https://github.com/openai/codex/blob/rust-v0.154.0/codex-rs/ext/skills/src/loader/metadata.rs
[model]: https://github.com/openai/codex/blob/rust-v0.154.0/codex-rs/skills/src/model.rs
