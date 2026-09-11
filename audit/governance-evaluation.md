# Repository governance evaluation

Evaluated 2026-09-12. Integrated explicit-only `configure-repository-governance`
and consolidated three references into one. Retired the original
`repository-docs` umbrella after its documentation, changelog, and governance
responsibilities acquired separate accepted owners. The old duplicate
changelog/SemVer helpers are replaced by the previously validated
`maintain-changelog` implementation, not a new parser.

## Source and boundary review

Rechecked official GitHub CODEOWNERS, issue-form and form-schema documentation,
and GitLab Code Owners/description-template documentation. File selection,
pattern semantics, owner access, and hosted enforcement are separate contracts.

Added explicit distinctions for GitHub's first-file selection, case-sensitive
paths, draft review requests, team eligibility, and any-owner approval
semantics. GitHub [ruleset required reviewers][reviewers] can require approval
counts from multiple teams on matching files; their pattern rules differ from
CODEOWNERS. This supported option avoids inventing an approval bot, but account
availability, bypasses, and actual settings still require authorized inspection.

## Independent forward task

A fresh-context evaluator audited a scenario with root and `.github` CODEOWNERS,
two owners on one security-document rule, a request for both teams' approvals,
and a requested bug form. It correctly identified the shadowed root file,
last-match semantics, and why duplicated patterns do not combine owners. It
proposed required reviewers as separate hosted enforcement, with no account
access or mutations. Integration checked that option against current official
documentation rather than accepting the agent's remembered feature name.

The proposed issue form uses supported textarea controls, unique IDs, and a
required reproduction field. YAML parsing succeeded. The answer distinguishes
submission-time validation from later edits and flags unverified repository
visibility. No form was submitted and no provider-rendering or account-level
approval test is claimed. Team visibility guidance for CODEOWNERS is not itself
proof of every required-reviewer eligibility rule.

## Validation and limits

Both skill validators and strict Markdown pass. Metadata preserves named manual
invocation. Local links resolve. Search found no live references to the retired
umbrella's scripts or references in current skills; historical audit records are
not runtime consumers.

No custom CODEOWNERS matcher was added. Semantic evidence comes from official
provider rules and the independent scenario, not a generic gitignore parser.
GitLab hosted enforcement, live ownership eligibility, issue rendering, and real
merge rejection remain untested. These limitations do not justify external
writes outside the task's authorization.

Raw evaluation: `/tmp/governance-forward-result.md`.

[reviewers]:
  https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets#required-reviewers
