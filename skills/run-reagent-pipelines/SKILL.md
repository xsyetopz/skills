---
name: run-reagent-pipelines
description: >-
  Runs Reagent (`re-agent`, PyPI `auto-re-agent`) from a coding agent as a
  budgeted batch job: `doctor`, `estimate`, `plan`, then a small `reverse`
  run, with provider and `re-agent.yaml` setup, a measured usage check for
  `claude-cli`, background execution, and review of the parity and acceptance
  results as candidates. Use when asked to run re-agent or Reagent, or to
  auto-reverse a class or many functions from a binary the user may analyze.
  Not for single-function questions, the method of reversing a function, the
  Ghidra export itself, or licence, DRM, or anti-cheat bypass.
---

# Run Reagent Pipelines

Reagent reconstructs C and C++ functions from a binary. It runs its own LLM
loop and uses `ghidra-bridge` exports as evidence. From a coding agent it is
a long batch job, not a tool to call for each question. A run started inside
an agent session spends usage twice: once for the session that waits on it,
and once for the model calls that Reagent makes.

For one function or one question, do not start Reagent. Use
`$analyze-binaries-with-ghidra` and `$reverse-engineer-functions`.

## Scope

Run Reagent only on binaries that the user may analyze: their own programs,
interoperability, preservation, allowed security research, and
matching-decompilation projects. Refuse, and say why, when the goal is to
bypass a licence check, DRM, or anti-cheat. Reagent sends decompiled code
to the configured model provider, so confirm that the user accepts that
for this binary.

## Workflow

1. Confirm the scope above. Name the program, the target class or function
   set, and the money or usage the user accepts for this run.
1. Check that the Ghidra export exists (`ghidra-bridge export`). Reagent
   depends on it; `$analyze-binaries-with-ghidra` covers setup and the
   export. Do not start a second export against a project that is open in
   Ghidra.
1. Write or review `re-agent.yaml`. See
   [configuration](references/configuration.md) for providers, environment
   variables, precedence, and role blocks.
1. Run the [preflight order](#preflight-order). Stop at any failing step.
1. Run a small `reverse` job and [measure its cost](#measure-the-cost).
1. Run the full job [in the background](#run-in-the-background).
1. [Review the results](#review-the-results) as candidates.

## Preflight order

Run these from the project root, in this order:

```bash
re-agent doctor
re-agent estimate
re-agent plan
re-agent reverse --class CTrain --max-functions 10
```

- `doctor` checks the installation and its dependencies. Fix what it
  reports before anything else.
- `estimate` reports the expected cost of a run. Read
  `re-agent estimate --help` first, because the options belong to the
  installed version. Give the user the figure before `reverse`.
- `plan` shows what `reverse` would work on. Check that the class or
  function set is the one the user asked for.
- `reverse` starts the model calls. Always bound it with `--max-functions`
  for the first run.

Never run `reverse` without an estimate and a budget:

- With `claude-cli`, set `max_budget_usd` in the role block (for example
  `agents.reverser`).
- With an API provider, set a spend limit at the provider as well as
  `--max-functions`. Reagent's config has no budget key that this skill
  has verified for those providers.

If `estimate` fails or gives no figure, report that and ask the user to
choose the cap. Do not guess one.

## Measure the cost

The usage cost of `claude-cli` runs against subscription limits has no
published figure. Do not quote a ratio from memory or from a forum.
Measure it on a small run:

1. Record the current usage from the account's usage view (in Claude
   Code, `/usage`) before the run.
1. Run `re-agent reverse --class <name> --max-functions 3`.
1. Record the usage after the run and the `max_budget_usd` that applied.
1. Divide by the number of functions to get a per-function figure, scale
   it to the planned size, and tell the user the result with the sample
   size. Three functions is a rough sample: say so.

Other work in the same account during the run changes the reading. Run it
while the account is otherwise idle, or say that it was not.

## Run in the background

- Start the full job as a background process with its output sent to a
  log file, so the agent session does not wait on it and does not spend
  usage while it runs:

  ```bash
  re-agent reverse --class CTrain --max-functions 50 > re-agent.log 2>&1 &
  ```

- Check on it with `re-agent status` and `re-agent status --manifest`.
  Read `re-agent-progress.json` for progress.
- Read the outputs under `reports/re-agent/`: `code/`, `logs/`,
  `candidates/`, and `knowledge-graph.json`. Read them with `head`, `jq`,
  or by file. Do not paste the whole tree into the session.
- Checkpoint files are not documented where this skill can confirm them.
  Use `re-agent status` to find what a run saved, and read
  `re-agent reverse --help` for resume options.
- Keep `reports/`, `re-agent-progress.json`, the log, exports, and the
  binaries out of git. Check `git status` before any commit and add the
  ignore entries only if the user agrees.

## Review the results

Reagent accepts a function when all four hold:

1. The LLM checker says PASS.
1. The objective verifier finds no strong structural mismatch.
1. Candidate validation satisfies the acceptance policy.
1. Parity is not blocked by the RED or YELLOW policy.

Parity has 11 signals. RED blocks by default: missing source, stub
markers, a trivial stub, or a large assembly body with tiny source. YELLOW
signals are plugin-call heavy, a short body (under 6 lines), low call
count, floating-point sensitivity, call-count mismatch, and NaN logic.
They block only with `validation.parity_fail_on_yellow`. Ask the user
whether YELLOW should block, and set it in `re-agent.yaml`. For a check
that fails a script on the parity result, use
`re-agent parity ... --strict-exit` (see `re-agent parity --help`).

The README says: "This is conservative verification, not a proof of
semantic equivalence." Report accepted functions as candidates that passed
these checks, never as confirmed originals.

- Review every candidate against the decompiled function before it enters
  the user's tree. `$reverse-engineer-functions` covers the method.
- When the goal is a byte-matching build, send each candidate through
  `$build-matching-decompilations`. Acceptance by Reagent is not a match.
- Report rejected and RED or YELLOW functions with the signal that
  blocked them, so the user can decide what to redo by hand.

## Rules

- Never run `reverse` without an estimate and a budget.
- Do not call Reagent for a single function or a quick question.
- Do not set API keys in `re-agent.yaml` or commit them. Use the
  environment variables in [configuration](references/configuration.md)
  and refer to them by name.
- Do not invent `re-agent` flags or config keys. Read `--help` of the
  installed version and the [configuration](references/configuration.md)
  reference.
- Do not run several `reverse` jobs on the same class at once.

## References

- [Configuration](references/configuration.md): install, providers,
  environment variables, precedence, role blocks, and sources.

## Completion evidence

The answer names the program and class run, the `doctor`, `estimate`, and
`plan` results, the budget set, the measured usage for the small run (or
why it was not measured), the number of functions accepted, rejected, and
blocked by RED or YELLOW, the `reports/re-agent/` paths to read, and any
step that could not run and why.
