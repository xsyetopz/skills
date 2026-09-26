# Codex metadata

`agents/openai.yaml` holds Codex interface metadata, invocation policy,
and MCP dependencies. `SKILL.md` stays the portable entry point; this
file is not a second instruction body. Field facts come from OpenAI's
[build-skills guide][guide] and the Codex `rust-v0.154.0` sources:
[field reference][fields], [interface resolver][interface],
[metadata loader][loader], [skill model][model]. Re-check them for the
installed Codex version.

## Contents

- Interface fields
- Invocation policy
- MCP dependencies
- Loader behavior on bad metadata

## Interface fields

**Definition.** `interface.display_name` (label; the resolver accepts at
most 64 characters after whitespace normalization),
`interface.short_description` (UI blurb; the bundled guidance recommends
25-64 characters), `interface.default_prompt` (an example invocation that
must contain `$skill-name`; resolver limit 1,024 characters), and optional
`icon_small`, `icon_large`, `brand_color` (`#RRGGBB`).

**Use when.** Every skill intended for Codex. This repository's
validator requires the three string fields and `$<name>` in
`default_prompt`.

**Do not use when.** Icons or colors without a product requirement.
Appearance fields do not affect selection, which depends on the
`SKILL.md` description.

**Example.**

```yaml
interface:
  display_name: "Optimize C# Code"
  short_description: "Profile and optimize C# and .NET workloads"
  default_prompt: >-
    Use $optimize-csharp-code to profile this workload, apply a measured
    optimization, and report matched evidence.
```

**Cost removed.** A skill that loads without a usable UI entry or
example prompt.

**Verify.**

1. `python3 -c "import yaml,sys; d=yaml.safe_load(open(sys.argv[1]));
   print(d['interface'])" agents/openai.yaml` parses and shows the fields.
1. In Codex, `/skills` lists the skill with the display name.

## Invocation policy

**Definition.** `policy.allow_implicit_invocation` defaults to `true`;
`false` removes the skill from automatic selection while keeping explicit
`$skill-name` invocation ([guide][guide]).

**Use when.** A skill should run only on explicit request (multi-agent
coordination, destructive workflows).

**Do not use when.** Never treat it as a permission or security
boundary; it controls selection only, so keep operation limits in the
procedure. The 0.154.0 parser also accepts `policy.products`, but the
skill model marks its enforcement as a TODO; do not rely on it.

**Example.**

```yaml
policy:
  allow_implicit_invocation: false
```

**Cost removed.** Automatic activation of workflows the user must start.

**Verify.**

1. The value is a YAML boolean (`false`), not the string `"false"`.
1. A matching prompt without `$skill-name` does not load the skill in
   Codex.

## MCP dependencies

**Definition.** `dependencies.tools` declares MCP servers the skill
requires: `type: "mcp"`, `value`, `description`, `transport`, `url` (the
0.154.0 loader also reads `command` and an OAuth callback port).

**Use when.** The skill cannot work without that specific server.

**Do not use when.** The dependency is a CLI, compiler, or runtime
(state those in instructions or `compatibility`), or several providers
are alternatives; the metadata has no conditional form.

**Example.**

```yaml
dependencies:
  tools:
    - type: "mcp"
      value: "openaiDeveloperDocs"
      description: "OpenAI documentation MCP server"
      transport: "streamable_http"
      url: "https://developers.openai.com/mcp"
```

**Cost removed.** A skill failing mid-task on a missing server.

**Verify.**

1. In Codex, the server shows as connected with its tools listed before
   the skill is used; declaration alone does not prove registration.

## Loader behavior on bad metadata

**Definition.** The 0.154.0 loader fails open: it ignores missing or
malformed optional metadata and still loads `SKILL.md`, and the resolver
can discard invalid optional strings.

**Use when.** A policy or dependency seems to have no effect.

**Do not use when.** Taking a visible skill as proof that its metadata
was accepted.

**Example.** A typo `allow_implict_invocation: false` leaves implicit
invocation enabled with no error.

**Cost removed.** Silent misconfiguration.

**Verify.**

1. Parse with duplicate-key rejection and compare keys against the field
   reference for the installed version.
1. Observe the behavior in Codex (implicit selection, UI fields).

[guide]: https://learn.chatgpt.com/docs/build-skills
[fields]: https://github.com/openai/codex/blob/rust-v0.154.0/codex-rs/skills/src/assets/samples/skill-creator/references/openai_yaml.md
[interface]: https://github.com/openai/codex/blob/rust-v0.154.0/codex-rs/skills/src/interface.rs
[loader]: https://github.com/openai/codex/blob/rust-v0.154.0/codex-rs/ext/skills/src/loader/metadata.rs
[model]: https://github.com/openai/codex/blob/rust-v0.154.0/codex-rs/skills/src/model.rs
