# Catalog discovery and skill-maintenance audit

Evaluated 2026-09-11 against the current 40-skill worktree. This is a discovery
and boundary evaluation, not acceptance of all technical content or pending
renames. The initial worktree and earlier audit decisions are not authoritative.

## Discovery defect and correction

Thirty-three metadata files disabled implicit invocation. Only
`format-github-markdown` and `interrogate-plan` also declared an explicit-only
contract in their descriptions. The initial Git commit had no
`allow_implicit_invocation` fields; the blanket additions were inherited
uncommitted edits, except for the changelog policy accepted in a later commit.
There was no user instruction requesting this blanket restriction.

Removed that restriction from the other 31 worktree packages. Preserved the two
coherent explicit-only contracts rather than guessing that their intentional
interaction mode should change. Restoring discovery does not authorize commits,
publication, settings changes, or emulator execution independently of a user's
request and the active permissions.

The current [Codex skills guide](https://learn.chatgpt.com/docs/build-skills)
confirms that omitted `allow_implicit_invocation` defaults to true and false
blocks implicit matching while retaining explicit invocation. The bundled
skill-creator guidance separately warns against inferring explicit-only policy
from the consequences of a workflow. A good description cannot compensate for a
policy that disables its use.

The same correction removes the unsupported changelog restriction previously
accepted during this rebuild. That earlier narrow validation did not prove
catalog discovery was correct.

## Skill-maintenance guidance

The `maintain-agent-skills` package keeps two substantive references and a
compact entrypoint. It now distinguishes portable specification checks from
documented client metadata checks; no published JSON Schema is assumed and a
generator is not described as an existing-file validator. It requires meaningful
routing and behavioral evidence, current source intake, and maintained
standards/tooling before custom mechanisms. It distinguishes capability
selection from readiness to execute after gathering missing inputs.

The [Agent Skills specification](https://agentskills.io/specification),
[OpenAI plugin authoring guidance][source-1],
and [Academy guide](https://openai.com/academy/skills/) were reopened for this
pass. Client discovery and portable package format remain separate contracts. No
new schema, test framework, or script was introduced for this metadata edit.

## Independent routing evaluation

Two fresh-context reviewers each evaluated 20 skills with all 40 metadata
entries as candidates. Each recorded direct, paraphrased, incomplete, adjacent,
unrelated, ambiguous, and combined prompts: 280 exact-prompt cases in total.
They read metadata before skill bodies and did not receive expected routes. Four
additional coordinator cases distinguish genuinely ambiguous input from a
known-domain request that lacks execution details. Their provenance is explicit
in the second-half report; they are not independent reviewer runs.

- [First 20 skills](catalog-routing-first-half.md)
- [Last 20 skills](catalog-routing-second-half.md)

Integration rejected an initial evaluation shortcut: missing execution details
were being treated as missing skill identity. For example, a request to repair a
Neovim plugin can select Neovim guidance before its failure reproduction is
known. Reviewers corrected these cases rather than counting every request for
clarification as a successful routing outcome. The maintenance guidance now
makes that distinction explicit. These are reviewer classification results, not
telemetry from the Codex loader or guarantees about every model/client.

## Remaining boundary decisions

The evaluation exposes candidate coverage gaps: release-binary emulator
installation, Bun-only upgrades, and local Git tagging. These are not evidence
that three more micro-skills are needed. Resolve them while reviewing the
corresponding workflows and references; consider an existing cohesive owner
before adding another skill. In particular, the pending Node-to-Bun rename
narrows the earlier Bun migration capability and needs an explicit decision.

Explicit metadata boundaries alone do not establish good granularity. The
pending hosted-repository, local Git, and emulator splits still need workflow
and duplication review. This evaluation must not be used to approve their
technical content or the whole suite simply because their descriptions can be
distinguished.

## Validation and limits

All 40 frontmatter and client metadata documents parsed as YAML. Names match
folders, default prompts reference their actual skill names, interface values
are strings, and the two retained invocation-policy values are Booleans. These
checks cover used documented fields, not an invented complete client schema.

Official skills-ref, the bundled quick validator, Markdown rules, and local
reference checks pass for `maintain-agent-skills`. The changed Markdown and
`git diff --check` pass. No production implementation, editor asset, emulator,
or hosting operation is proven by these metadata checks.

The metadata corrections to uncommitted renamed packages remain in the worktree
for integration with their owning domain. This audit does not commit incomplete
metadata-only directories or accept unrelated inherited changes.

[source-1]: https://developers.openai.com/plugins/build/skills
