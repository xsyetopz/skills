# Package format

What a skill directory contains, what each host reads, and the limits
that apply. Facts come from the [Agent Skills specification][spec],
Anthropic's [authoring best practices][anthropic-bp], the
[Claude Code skills documentation][cc-skills], and OpenAI's
[build-skills guide][codex-skills]; re-check them for the target host
version.

## Contents

- Directory layout
- SKILL.md frontmatter
- Name
- Progressive disclosure budget
- References one level deep
- Scripts: execute or read
- Assets
- Host discovery and invocation
- Claude Code frontmatter extensions

## Directory layout

**Definition.** A skill is a directory whose name equals its `name`, holding
a required `SKILL.md` plus optional `scripts/`, `references/`, `assets/`,
and host-specific metadata such as `agents/openai.yaml` for Codex
([spec][spec], [Codex][codex-skills]).

**Use when.** Creating any skill.

**Do not use when.** Never add README, CHANGELOG, LICENSE sidecars, icons,
or extra top-level folders unless the package or user requires them.
Hosts do not read them, and they cost maintenance.

**Example.**

```text
optimize-csharp-code/
  SKILL.md                 workflow, routing table, rules
  agents/openai.yaml       Codex interface and invocation policy
  evals/evals.json         realistic prompts with checkable assertions
  references/
    allocation.md          construct cards, one domain per file
    measurement.md
  assets/examples/
    constructs/            runnable baseline/candidate pairs
    verify.sh              oracle + benchmark entry point
  scripts/
    compare_benchmarks.py  deterministic helper
    test_compare_benchmarks.py
```

**Cost removed.** Guessing where content lives; hosts and agents
navigate by path.

**Verify.**

1. `skills-ref validate <skill-dir>` prints `Valid skill`
   ([skills-ref][skills-ref]).
1. `python3 scripts/check_reference_structure.py <skill-dir>` prints `OK`.

## SKILL.md frontmatter

**Definition.** YAML between `---` lines at the top of `SKILL.md`. Portable
fields ([spec][spec]):

| Field | Required | Constraint |
| --- | --- | --- |
| `name` | yes | 1-64 chars, `a-z0-9-`, no leading/trailing/double hyphen, equals directory |
| `description` | yes | 1-1024 chars; what it does and when to use it |
| `license` | no | license name or bundled file |
| `compatibility` | no | 1-500 chars; environment requirements |
| `metadata` | no | string-to-string map |
| `allowed-tools` | no | space-separated pre-approved tools (experimental) |

Anthropic also forbids XML tags in `name` and `description`, and the
reserved words `anthropic` and `claude` in `name`
([best practices][anthropic-bp]). Claude Code is more lenient: every field
is optional, `name` defaults to the directory name, and `allowed-tools`
also accepts commas or a YAML list ([Claude Code skills][cc-skills]).
Write to the spec so the skill works on every host.

**Use when.** Every skill.

**Do not use when.** Never upload to claude.ai or the Skills API with
Claude Code-only fields (`argument-hint`, `disable-model-invocation`, and
others); the upload fails with `Unexpected key(s) in SKILL.md frontmatter`
([Claude Code skills][cc-skills]).

**Example.**

```yaml
---
name: write-justfiles
description: >-
  Writes and debugs justfiles for the just command runner: recipes,
  parameters, dependencies, settings, and shell quoting. Use when adding
  or fixing project task recipes. Not for replacing a build system.
compatibility: Requires just 1.x; examples tested with just 1.58.
---
```

A folded scalar (`>-`) wraps long descriptions without embedding
newlines.

**Cost removed.** Skills that fail to load or upload.

**Verify.**

1. `skills-ref validate <skill-dir>`.
1. Parse the frontmatter with a YAML loader and print the description
   length:

   ```sh
   python3 - SKILL.md <<'PY'
   import sys, yaml
   front = open(sys.argv[1]).read().split("---")[1]
   print(len(yaml.safe_load(front)["description"]))
   PY
   ```

## Name

**Definition.** The directory name and `name` field identify the skill
and become its invocation (`/name` in Claude Code, `$name` in Codex).

**Use when.** Creating a skill. Prefer an action and object
(`optimize-csharp-code`, `write-justfiles`); Anthropic suggests gerund
forms (`processing-pdfs`) or action forms, applied consistently across a
collection ([best practices][anthropic-bp]).

**Do not use when.** Renaming a published skill breaks callers,
documentation, and `$name` references in other skills; treat a rename as
a migration.

**Example.** `debug-software-failures`, not `git-helper` (vague) or
`claude-bisect` (reserved word).

**Cost removed.** Ambiguous invocation and collisions.

**Verify.**

1. `rg -n '\$old-name\b|/old-name\b'` across the collection finds no stale
   references after any rename.

## Progressive disclosure budget

**Definition.** Hosts load a skill in three levels: metadata (name and
description) of every installed skill at startup, the `SKILL.md` body
when the skill is selected, and bundled files only when read or executed
([spec][spec]). The spec recommends a body under 5,000 tokens and under 500
lines; Anthropic and Claude Code say the same 500-line figure
([best practices][anthropic-bp], [Claude Code skills][cc-skills]).
Descriptions are normally in context. Claude Code caps the combined
`description` and `when_to_use` at 1,536 characters, budgets the listing
at 1% of the context window, and drops the descriptions of the
least-invoked skills when it overflows; `disable-model-invocation: true`
keeps a description out entirely ([Claude Code skills][cc-skills]). Codex
budgets 2% of the context window in tokens, or 8,000 characters when the
window is unknown, and removes descriptions before omitting skills
([render.rs][codex-render]).

**Use when.** Deciding what goes in the description, the body, and the
references.

**Do not use when.** Never use disclosure as a reason to keep content
thin. A reference costs nothing until read, so put the complete technical
detail there and have `SKILL.md` route to it precisely.

**Example.** Body: workflow, routing table from symptom to card, rules,
completion evidence. References: one card per construct with complete code.
Assets: runnable projects. A repository may set a stricter body limit (this
collection: 220 lines, validated by `scripts/validate_repository.py`).

**Cost removed.** Context spent on detail irrelevant to the current task,
and listing truncation that drops trigger words.

**Verify.**

1. Body line count:
   `awk 'c>=2; /^---$/{c++}' SKILL.md | wc -l`.
1. The description is under the host limit. For a large catalog, the
   sum of all descriptions is compared with the listing budget.

## References one level deep

**Definition.** `SKILL.md` links every reference file directly. Agents
may preview a file reached through another reference (for example with
`head -100`) instead of reading it whole, so nested chains lose content
([best practices][anthropic-bp]). References over 100 lines start with a
table of contents, so a partial read still shows the scope.

**Use when.** Always.

**Do not use when.** Adding cross-links between references for
navigation; they are fine as long as SKILL.md also links every file
directly.

**Example.**

```text
## References

- Allocation (references/allocation.md, linked): 18 allocation cards.
- Measurement (references/measurement.md, linked): BenchmarkDotNet,
  counters.
```

**Cost removed.** Content an agent never reads.

**Verify.**

1. `python3 scripts/check_reference_structure.py <skill-dir>` reports
   unlinked references and missing `## Contents` sections.

## Scripts: execute or read

**Definition.** Scripts carry deterministic mechanics (parsing,
comparing, validating). Instructions say whether to **run** a script
(only its output enters context) or **read** it as reference
([best practices][anthropic-bp]).

**Use when.** The same mechanical logic would otherwise be regenerated
per task, or correctness depends on exact handling (exit codes, units,
row identity).

**Do not use when.** A native command already does it (`skills-ref`,
`markdownlint-cli2`, `just --fmt --check`); do not wrap it.

**Example.**

```markdown
Run `python3 scripts/compare_benchmarks.py base.csv candidate.csv`;
it exits 0 within threshold, 1 on regression, 2 on incomparable input.
```

**Cost removed.** Inconsistent regenerated logic and the tokens spent
writing it. See [executable resources](executable-resources.md).

**Verify.**

1. Each script has `--help` or a usage docstring and a `test_*.py` that
   runs standalone.

## Assets

**Definition.** Files used in outputs or executed as examples: templates,
complete example projects, fixtures.

**Use when.** A snippet would omit what makes it run (project file, lock
or version pin, test fixture, harness).

**Do not use when.** The file would be a nested `SKILL.md`, which
installers and hosts may discover as a separate skill. Name templates
`SKILL.template.md`.

**Example.** `assets/examples/constructs/Constructs.csproj` plus the source
files it builds, run by `assets/examples/verify.sh`.

**Cost removed.** Agents rebuilding missing project scaffolding.

**Verify.**

1. The asset's verifier runs in a disposable copy and leaves no build
   output in the skill (`git status --short <skill-dir>` is unchanged).

## Host discovery and invocation

**Definition.** Where hosts look for skills and how users call them.

| Host | Locations (highest priority first) | Invoke |
| --- | --- | --- |
| Claude Code | enterprise managed dir, `~/.claude/skills/`, `.claude/skills/` (and nested subdirectories), plugin `skills/` | `/name`, `/plugin:name` |
| Codex | `$CWD/.agents/skills`, repo root `.agents/skills`, `$HOME/.agents/skills`, `/etc/codex/skills`, built-ins | `$name` |

Sources: [Claude Code skills][cc-skills], [Codex][codex-skills].

**Use when.** Telling users how to install and invoke a skill, or
testing one locally.

**Do not use when.** Never assume every host exposes the same metadata or
loads skills identically; test each target host.

**Example.** Install this collection for detected agents with
`bunx skills add https://github.com/xsyetopz/skills`, or copy one skill
directory into `.claude/skills/` for a project.

**Cost removed.** "Skill not found" debugging.

**Verify.**

1. In Claude Code, the skill appears in the `/` menu and in `/skills`; in
   Codex, `/skills` lists it.

## Claude Code frontmatter extensions

**Definition.** Claude Code reads extra fields (`when_to_use`,
`argument-hint`, `arguments`, `disable-model-invocation`, `user-invocable`,
`disallowed-tools`, `model`, `effort`, `context: fork`, `agent`, `paths`,
`shell`, `hooks`) and substitutes `$ARGUMENTS`, `$0`, named arguments,
and `${CLAUDE_SKILL_DIR}` in the body ([Claude Code skills][cc-skills]).

**Use when.**

- `disable-model-invocation: true` for side-effecting workflows the user
  must start (deploy, commit).
- `paths` to limit automatic activation to matching files.
- `${CLAUDE_SKILL_DIR}` to reference bundled scripts by absolute path.

**Do not use when.** The skill must stay portable: claude.ai uploads and
the Skills API accept only `name`, `description`, `license`,
`compatibility`, `metadata`, and `allowed-tools`
([Claude Code skills][cc-skills]).

**Example.**

```yaml
---
name: deploy-staging
description: Deploys the current branch to staging. Manual use only.
disable-model-invocation: true
allowed-tools: Bash(./scripts/deploy.sh *)
---

Run `${CLAUDE_SKILL_DIR}/scripts/deploy.sh $ARGUMENTS` and report the URL.
```

**Cost removed.** Accidental automatic invocation of side-effecting
workflows, and permission prompts for the one script the skill needs.

**Verify.**

1. With `disable-model-invocation: true`, the description no longer appears
   in the model's skill listing (check `/context`).

[spec]: https://agentskills.io/specification
[anthropic-bp]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
[cc-skills]: https://code.claude.com/docs/en/skills
[codex-skills]: https://learn.chatgpt.com/docs/build-skills
[skills-ref]: https://github.com/agentskills/agentskills/tree/main/skills-ref
[codex-render]: https://github.com/openai/codex/blob/e72da2b/codex-rs/ext/skills/src/render.rs
