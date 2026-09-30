---
name: write-architecture-md
description: >-
  Writes, updates, and audits ARCHITECTURE.md from the repository, with tree,
  diagram, components, and invariants. Use when documenting how a codebase is
  built or fixing drift. Not for READMEs or ADRs.
---

# Write ARCHITECTURE.md

Give readers the map of a codebase they cannot get from one file: where
each responsibility lives, how the parts connect, which boundaries and
invariants hold, and what the repository does not show. The outline is
the eleven-section [architecture.md][site] template; the durability rules
come from matklad's original ARCHITECTURE.md post. Every claim must trace
to a file in the repository.

## Workflow

1. Find existing architecture documents before creating one:
   `fd -i -d 3 'architecture|adr|decisions'`. The file is always
   `ARCHITECTURE.md` at the repository root; move one kept elsewhere
   (`docs/architecture.md`) there with `git mv`
   ([placement](references/durability.md#placement-and-neighboring-documents)).
1. Gather evidence: `git ls-files | cut -d/ -f1 | sort -u` for the
   top-level layout, then manifests and lockfiles, entry points, imports
   between packages, schemas and migrations, CI workflows, container and
   IaC files, auth and validation code.
1. Write from the [template][template]
   ([section content](references/content.md)). Keep all eleven sections;
   a section without evidence gets one line: "Not evident from the
   repository." Add the prompt's optional sections only with evidence.
1. For an update, audit drift first and edit only the facts that changed
   ([updating](references/durability.md#updating-an-existing-architecturemd)).
1. Check paths and structure:
   `python3 scripts/check_architecture.py ARCHITECTURE.md`.
1. Run every command the document lists:
   `python3 scripts/check_architecture.py --commands ARCHITECTURE.md`,
   then run each line from the stated directory and keep only those that
   pass.
1. Search the code for each technology, service, and control the document
   names; remove or mark any with no match
   ([evidence](references/content.md#evidence-for-every-claim)).
1. Read the diagram against the component list: same names, no extra
   boxes, no missing components.

## Route the task to a card

| Task or symptom | Card |
| --- | --- |
| Template default (AWS, Redis, JWT) with no evidence | [Evidence for every claim](references/content.md#evidence-for-every-claim) |
| Writing the tree, or checker reports a missing path or directory | [Project structure tree](references/content.md#project-structure-tree) |
| Diagram section, Mermaid, or diagram and text disagree | [Diagram](references/content.md#diagram-that-matches-the-components) |
| Describing a package, service, or module | [Core components](references/content.md#core-components) |
| Databases, files, queues, schemas, migrations | [Data flow and stores](references/content.md#data-flow-and-data-stores) |
| Third-party APIs, CI, hosting, security controls | [Integrations, deployment, security](references/content.md#integrations-deployment-and-security) |
| Development section commands | [Commands that run](references/content.md#development-commands-that-run) |
| Layer rules, "X never imports Y" | [Invariants and boundaries](references/content.md#invariants-and-boundaries) |
| Rationale, TODOs, roadmap, recommendations | [Decisions, debt, roadmap](references/content.md#decisions-debt-and-roadmap) |
| Owner, URL, date, glossary | [Identification and glossary](references/content.md#project-identification-and-glossary) |
| Monitoring, performance, testing strategy sections | [Optional sections](references/content.md#optional-sections-from-the-prompt) |
| Links to local files, `file:line` references | [Name, do not link](references/durability.md#name-files-and-symbols-do-not-link-them) |
| "See CONTRIBUTING.md" instead of facts | [Self-contained](references/durability.md#self-contained) |
| Counts, versions, per-function detail; document is long | [Durable facts only](references/durability.md#durable-facts-only) |
| Existing document is stale, or code was renamed or removed | [Updating](references/durability.md#updating-an-existing-architecturemd) |
| File location or name; fact might belong in README, AGENTS.md, or an ADR | [Placement](references/durability.md#placement-and-neighboring-documents) |

## Rules

- Invent nothing. The template's examples (AWS, PostgreSQL, Redis, JWT,
  Kubernetes) are prompts, not defaults; an agent that fills them in
  produces confident false facts that later agents act on. Write "Not
  evident from the repository." and, when the user asked for the missing
  fact, say in the reply where it must come from.
- Do not claim a security control unless code enforces it. A missing
  control is a fact to state; an invented one stops reviewers from
  checking.
- Name files and symbols in backticks; do not link local files or cite
  line numbers. Links and line numbers go stale with the next edit; names
  survive and symbol search finds them.
- State facts instead of pointing to other files. Agents often load only
  this file, and "see CONTRIBUTING.md" gives them nothing.
- Keep only facts a refactor that preserves the architecture would leave
  true. Counts and per-function behavior make the file stale in weeks.
- Write "Rationale not documented" rather than inventing history, and
  label recommendations as recommendations, so no one mistakes a guess
  for a decision record.
- Express invariants with a command that passes now and fails when the
  rule is broken; an unchecked invariant drifts silently.
- When updating, keep the project's structure and correct content; fix
  facts and the date. Rewriting a matklad-style codemap into the template
  loses content the team chose, unless the user asks for the template.
- Remove every placeholder and template instruction sentence; the checker
  errors on them because a leftover `[Insert ...]` signals an unreviewed
  file.
- Name the file `ARCHITECTURE.md`, capitalised, at the repository root
  next to `README.md`, where both sources put it and readers look. Move
  a `docs/architecture.md` there, update links to the old path, and keep
  no second copy; two architecture documents drift apart.

## Bundled tools

- `scripts/check_architecture.py FILE [--json | --commands]`: stdlib
  only; paths resolve from the file's directory. Errors on a file not
  named `ARCHITECTURE.md` or kept in `docs/`, missing or empty template
  sections, leftover placeholders and template text, an unfenced
  diagram, tree and
  backticked paths that do not exist, and undescribed top-level
  directories; warns on local links, `file:line` references, "see X.md",
  and a missing date. `--commands` prints the shell-fence commands. Exit
  0 clean, 1 errors, 2 bad input. It cannot detect invented technology;
  the evidence search does that.
- `assets/ARCHITECTURE.template.md`: the eleven sections with
  `{placeholders}`.
- `assets/examples/shortlinks/`: a runnable stdlib Python project with a
  complete `ARCHITECTURE.md`, including invariant commands.
- `assets/examples/ARCHITECTURE.broken.txt`: the same project documented
  with the common failures (template text, invented Redis and JWT, stale
  paths, links, an empty section).
- `assets/examples/verify.sh`: in a disposable copy, checks the good
  document, runs its commands, shows an invariant command failing after a
  violation, and shows the checker catching each broken-file defect.

## References

- [Section content](references/content.md): evidence, tree, diagram,
  components, data stores, integrations, deployment, security, commands,
  invariants, decisions, identification, glossary, optional sections.
- [Durability and upkeep](references/durability.md): naming instead of
  linking, self-contained facts, durable content, drift audits,
  placement against README, AGENTS.md, and ADRs.

## Completion evidence

The report states: the file written or changed and its path; the checker
output (0 errors, and any remaining warnings with reasons); each listed
command with its exit status; the technologies searched for and whether
each was found; the sections marked "Not evident from the repository";
and whether the Mermaid diagram was rendered or only read.

[site]: https://architecture.md/
[template]: assets/ARCHITECTURE.template.md
