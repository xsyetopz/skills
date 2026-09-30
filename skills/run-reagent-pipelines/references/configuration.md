# Reagent configuration

Reagent (`re-agent`, MIT, Python 3.10 or newer) is published on PyPI as
`auto-re-agent`, version 0.4.0 at the time of writing.

## Install

```bash
python3 -m pip install --upgrade "auto-re-agent[ghidra-bridge]>=0.4.0"
```

The `[headless]` extra also exists. Use the user's existing Python
environment policy.

## Subcommands

`doctor`, `benchmark`, `plan`, `evidence`, `init`, `reverse`, `parity`,
`status`, and `estimate`. Read `re-agent <subcommand> --help` for the
options of the installed version.

## Providers

| Provider | Uses | Notes |
| --- | --- | --- |
| `claude` | Anthropic SDK | `ANTHROPIC_API_KEY` |
| `claude-cli` | Local Claude Code login | optional `cli_path`, `max_budget_usd`, `effort` |
| `openai` | OpenAI API | `OPENAI_API_KEY` |
| `openai-compat` | OpenAI-compatible endpoint | `OPENAI_API_KEY`, base URL |
| `codex` | Local `codex` CLI | |

Example role block:

```yaml
agents:
  reverser:
    provider: claude-cli
    model: sonnet
    max_budget_usd: 1.0
    effort: high
```

A role block is a complete `LLMConfig`. It is not merged with the top-level
LLM settings, so repeat every field the role needs.

## Environment variables

- `RE_AGENT_LLM_PROVIDER`
- `RE_AGENT_LLM_API_KEY`
- `RE_AGENT_LLM_MODEL`
- `RE_AGENT_LLM_BASE_URL`
- `RE_AGENT_BACKEND_CLI_PATH`
- `RE_AGENT_BACKEND_TIMEOUT`

## Precedence

CLI overrides, then environment, then `re-agent.yaml`, then defaults.

## Outputs

`reports/re-agent/code/`, `reports/re-agent/logs/`,
`reports/re-agent/candidates/`, `reports/re-agent/knowledge-graph.json`,
and `re-agent-progress.json`. The checkpoint path is not confirmed in the
sources below.

## Sources

- Reagent README: <https://github.com/Dryxio/reagent>
- Reagent configuration: `docs/configuration.md` in the same repository.
