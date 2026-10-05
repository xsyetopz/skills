# Host Metadata

Facts that differ by host. Re-check them for the installed version.

## Contents

- [Portable Frontmatter](#portable-frontmatter)
- [Claude Code Extensions](#claude-code-extensions)
- [Codex agents/openai.yaml](#codex-agentsopenaiyaml)
- [Other Hosts](#other-hosts)
- [Install Locations](#install-locations)

## Portable Frontmatter

| Field | Constraint |
| --- | --- |
| `name` | 1-64 of `a-z0-9-`, no leading, trailing, or double hyphen, equals the directory name |
| `description` | 1-1,024 characters |
| `license` | optional |
| `compatibility` | optional, 1-500 characters, environment requirements |
| `metadata` | optional string map |
| `allowed-tools` | optional, experimental |

Source: [specification][spec]. Anthropic also forbids XML tags in both fields and the words
`anthropic` and `claude` in `name`. Uploads to claude.ai and the Skills API reject any other key
with `Unexpected key(s) in SKILL.md frontmatter`.

## Claude Code Extensions

Claude Code only ([skills docs][cc-skills]).

- `disable-model-invocation: true` removes the skill from the model's listing, so only `/name`
  starts it. Use it for side-effecting workflows such as deploys, and for skills that only
  orchestrate other skills.
- `when_to_use` adds trigger text. It counts toward the 1,536-character entry cap.
- `paths` limits automatic activation to matching files.
- `allowed-tools` pre-approves tools while the skill runs, for example
  `Bash(python3 scripts/check.py *)`. Never pre-approve deploy, push, or publish commands.
- `${CLAUDE_SKILL_DIR}` expands to the skill's directory, so scripts can be called by absolute path.
  `$ARGUMENTS` expands to the user's arguments.
- Personal skills in `~/.claude/skills/` take priority over project skills with the same name.

## Codex agents/openai.yaml

Sources: [build skills][codex-skills] and the Codex [field reference][codex-fields].

```yaml
interface:
  display_name: "Write Justfiles"
  short_description: "Write and fix just recipes"
  default_prompt: "Use $write-justfile to add a test recipe."
policy:
  allow_implicit_invocation: true
```

- `short_description` is 25 to 64 characters and is what the Codex app shows. `default_prompt` must
  contain `$<skill-name>`.
- `allow_implicit_invocation: false` keeps the skill out of automatic selection while `$name` still
  works. It is a selection setting, not a permission boundary.
- `dependencies.tools` declares a required MCP server. Do not use it for CLIs or runtimes. State
  those in `compatibility`.
- The loader fails open. A misspelled key such as `allow_implict_invocation` is ignored without an
  error. Check behavior in Codex, not only that the skill appears.

## Other Hosts

- Microsoft Agent Framework loads skills through `load_skill`, `read_skill_resource`, and
  `run_skill_script` tools, which need approval by default. It only serves resources ending in
  `.md`, `.json`, `.yaml`, `.yml`, `.csv`, `.xml`, or `.txt`, and scripts need a configured runner
  ([Agent Framework skills][msaf]). Do not rely on a script being runnable there.
- Antigravity reads `.agents/skills/` in the workspace. Only `description` is required there, and
  `name` defaults to the folder ([Antigravity skills][antigravity]).

## Install Locations

| Host | Locations, highest priority first | Invoke |
| --- | --- | --- |
| Claude Code | managed, `~/.claude/skills/`, `.claude/skills/`, plugin `skills/` | `/name` |
| Codex | `.agents/skills` from cwd up to the repo root, `~/.agents/skills` | `$name` |

[spec]: https://agentskills.io/specification
[cc-skills]: https://code.claude.com/docs/en/skills
[codex-skills]: https://learn.chatgpt.com/docs/build-skills
[codex-fields]: https://github.com/openai/codex/blob/rust-v0.154.0/codex-rs/skills/src/assets/samples/skill-creator/references/openai_yaml.md
[msaf]: https://learn.microsoft.com/en-us/agent-framework/agents/skills
[antigravity]: https://antigravity.google/docs/skills/
