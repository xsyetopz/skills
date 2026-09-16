---
name: write-agents-md
description: >-
  Use when creating, auditing, or updating AGENTS.md or an established
  repository-instruction equivalent for a specific coding-agent client. Verify
  file scope, discovery, commands, and precedence. Not for reusable SKILL.md
  packages, event hooks, or global personality changes.
---


# Write AGENTS.md

Write concise repository-scoped instructions that tell coding agents what is
specific, non-obvious, and authoritative for the files in scope: commands,
architecture, ownership, generated/source boundaries, validation, and
operational constraints.

## Operating contract

- Inspect the target agent/client’s current discovery, scope, precedence,
  filename, and size behavior before creating or moving instruction files.
- Derive commands and rules from the repository, not model memory. Run or
  inspect every critical command and identify its working directory and scope.
- Keep reusable task knowledge in Agent Skills and repository-specific always-on
  context in AGENTS.md. Do not duplicate whole manuals or skill bodies.
- Preserve existing instructions outside the requested scope and resolve
  conflicts explicitly. A nested file narrows its subtree; it does not silently
  override user authority.
- Do not add style/personality/rhetorical guidance unrelated to repository work
  or turn one incident into a universal prohibition.

## Workflow

```mermaid
flowchart TD
    T[Agent and repository] --> D[Inspect discovery, precedence, and files]
    D --> S[Map file-tree scopes and owners]
    S --> E[Extract repository-specific commands and invariants]
    E --> W[Write concise scoped instructions]
    W --> C[Check conflicts, paths, commands, and size]
    C --> A[Run agent discovery / representative task check]
```

## Procedure

1. Identify the exact coding-agent client(s), supported instruction filename(s),
   repository root, nested scopes, and existing global/project/user
   instructions. Read current official client behavior for the installed
   version.
1. Inventory repository structure, build/test/lint/format/type/package commands,
   generated files, language/runtime versions, source-of-truth rules, ownership,
   sensitive areas, and validation gates. Execute or verify critical commands.
1. Decide placement: root instructions for repository-wide facts; nested
   instructions only for genuinely different subtree commands or contracts.
   Avoid duplicate text and contradictory layers.
1. Write direct instructions with scope and rationale where non-obvious. Include
   exact commands with working directory, files that must not be hand-edited,
   required check selection, authority boundaries, and links to durable
   repository docs or skills.
1. Exclude generic advice, transient task state, agent self-management, long
   architecture tutorials, secrets, unsupported future policy, and rules already
   enforced clearly by tooling unless agents need the command/path.
1. Validate Markdown, file paths, command names, and precedence. Test
   representative tasks from affected subdirectories with the target client when
   available; verify which instruction files it actually loads.
1. Review the diff against existing content. Preserve still-valid rules, remove
   stale contradictions only within scope, and report client behavior not
   exercised.

## Read only the material needed

| Situation | Read or use |
| --- | --- |
| Writing evidence-backed concise instructions and client scope | [Format and evidence](references/format-and-evidence.md) |
| Choosing root versus nested instruction placement | [Decision guide](references/decision-guide.md) |
| Using complete monorepo, generated-code, and validation examples | [Worked examples](references/worked-examples.md) |
| Checking discovery, commands, paths, and behavior claims | [Verification and evidence](references/verification-and-evidence.md) |
| Avoiding prompt stacking, stale rules, and skill duplication | [Failure modes](references/failure-modes.md) |
| Applying enterprise ownership and policy boundaries | [Enterprise operation](references/enterprise-operation.md) |
| Checking current AGENTS.md client documentation | [Source index](references/source-index.md) |

## Additional specialized references

Read only the reference whose subject affects the current task.

| Reference | Use when |
| --- | --- |
| [Domain model and authority](references/domain-model.md) | Current implementation is evidence of state, not automatically the desired contract. |
| [Bundled resource catalog](references/resource-catalog.md) | Locate and apply complete native templates without treating them as universal defaults. |

## Evaluation cases

Use [evaluation cases](references/evaluation-cases.md) for realistic activation,
near-miss, and instruction-conformance probes. These are maintained test inputs,
not claimed results.

## Bundled executable helpers

- No bundled script is mandatory. Use the target repository’s established tools.

Run a helper only for the contract it documents. Inspect arguments and output; a
zero exit status proves only the checks implemented by that helper.

## Bundled output material

- `assets/AGENTS.template.md`

Copy or adapt assets into the target workspace. Do not edit the installed skill
as a substitute for changing the requested repository.

## Completion evidence

- Target clients, discovery/precedence behavior, and instruction scopes.
- Repository-specific commands, working directories, generated/source rules, and
  constraints.
- Root/nested instruction files with no unnecessary duplication.
- Validated paths/commands and representative loading behavior when available.
- Preserved out-of-scope instructions and listed untested clients.

## Stop or escalate

- The target client or instruction discovery semantics cannot be established.
- A material organization policy or command is disputed and repository evidence
  cannot resolve it.
- The requested content belongs in a reusable skill, transient task plan, secret
  manager, or external policy system instead.
- Updating a parent/global instruction file is outside authorized scope.

Do not claim completion while a required check is failed, unattempted, or
unavailable. State the exact evidence and the remaining boundary instead of
promoting a narrower result into a broader claim.
