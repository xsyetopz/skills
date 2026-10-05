# Reagent Pipelines

Reagent (`re-agent`, PyPI `auto-re-agent`) reconstructs C and C++ functions from a Ghidra export
with its own LLM loop. It sends decompiled code to the configured provider, so confirm the user
accepts that for this binary. A run inside an agent session spends usage twice: once for the session
that waits and once for Reagent's model calls.

## Preflight

Run from the project root. Run `doctor`, `estimate`, and `plan` in that order and stop at a failing
step. Show the user the `estimate` figure, then stop and ask the user before any `reverse` run,
including a sampling run; it spends paid usage.

```bash
re-agent doctor
re-agent estimate
re-agent plan
```

A sampling run is `re-agent reverse --class CTrain --max-functions 3`. Read
`re-agent <subcommand> --help` first, because options belong to the installed version. Do not invent
flags or config keys. Check that `plan` lists the class the user asked for. If `estimate` gives no
figure, ask the user to choose the cap instead of guessing one.

## Budget

- With `claude-cli`, set `max_budget_usd` in the role block, for example `agents.reverser`.
- With an API provider, set a spend limit at the provider and bound `--max-functions`. No budget key
  is verified for those providers.
- No subscription-cost ratio is published. Measure it: note usage (in Claude Code, `/usage`) before
  and after `--max-functions 3` (after approval), divide by 3, scale to the planned size, and state
  the sample size. Other account activity changes the reading.

## Background Run

After approval, start the full job in the background (Claude Code `run_in_background`, POSIX
trailing `&`, PowerShell `Start-Job`) with output to `re-agent.log`:
`re-agent reverse --class CTrain --max-functions 50`. Check `re-agent status` and
`re-agent-progress.json`. Read outputs under `reports/re-agent/` (`code/`, `logs/`, `candidates/`,
`knowledge-graph.json`) with `head` or `jq`. Do not run two `reverse` jobs on one class. Keep
`reports/`, the progress file, the log, and exports out of git, and ask before editing `.gitignore`.

## Review

A function is accepted when the LLM checker says PASS, the objective verifier finds no strong
structural mismatch, candidate validation meets the acceptance policy, and parity is not blocked.
RED parity signals block by default. YELLOW signals block only with
`validation.parity_fail_on_yellow`, so ask the user which they want. Use
`re-agent parity ... --strict-exit` to fail a script on parity.

The README calls this "conservative verification, not a proof of semantic equivalence". Report
accepted functions as candidates, never as confirmed originals. Review each against the disassembly,
and report rejected and RED or YELLOW functions with the blocking signal. For a byte-matching build,
pass each candidate to `$decompile-to-matching-c-cpp`.

## Configuration

Providers: `claude` (`ANTHROPIC_API_KEY`), `claude-cli` (local login, `cli_path`, `max_budget_usd`,
`effort`), `openai` and `openai-compat` (`OPENAI_API_KEY`), `codex`. A role block is a complete
config and is not merged with top-level settings, so repeat every field it needs. Precedence: CLI
flags, environment, `re-agent.yaml`, defaults. Never put API keys in `re-agent.yaml`. Use
`RE_AGENT_LLM_PROVIDER`, `RE_AGENT_LLM_API_KEY`, `RE_AGENT_LLM_MODEL`, `RE_AGENT_LLM_BASE_URL`, and
refer to keys by name.

Source: <https://github.com/Dryxio/reagent>, `docs/configuration.md`.
