# Repository governance formats

Reviewed 2026-09-12 against the linked provider documentation. File syntax,
owner eligibility, and hosted enforcement are separate checks.

## CODEOWNERS is provider-specific

GitHub searches `.github/`, root, then `docs/` and uses the first CODEOWNERS
file found. Patterns generally follow gitignore-style matching, but negation and
bracket ranges are unsupported. The last matching pattern wins; owners for a
single rule belong on the same line. Owners need appropriate repository access.
Review requests use the base branch's file; mandatory approval additionally
requires configured branch protection/rules. Draft pull requests do not trigger
automatic owner requests until marked ready. Teams must be visible and have
explicit write access; member access alone does not establish team eligibility.
[GitHub code owners][source-1].

```text
* @example/maintainers
/docs/ @example/docs
/docs/security.md @example/security @example/docs
```

The two owners on `/docs/security.md` are alternatives for GitHub's required
code-owner approval; this does not require both teams to approve. If the user
requires both, report the mismatch and investigate a supported enforcement
mechanism separately. Do not promise that duplicating a pattern combines owners.
Use exact path case even on a case-insensitive local filesystem. Inspect which
CODEOWNERS file the provider selects before editing a shadowed file.

Use GitLab sections and approval syntax for GitLab CODEOWNERS. Required Code
Owner approvals depend on the relevant tier/protected-branch settings; writing
the file alone does not activate enforcement. Review its section defaults,
exclusions and number-of-approvals rules before changing them.
[GitLab Code Owners](https://docs.gitlab.com/user/project/codeowners/).

[source-1]:
  https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners

## Templates and policy

GitHub YAML issue forms are **public preview** as of the research date. Use
Markdown issue templates when preview features are excluded. PR templates use
Markdown.

GitHub issue forms use YAML under `.github/ISSUE_TEMPLATE/`, with `name`,
`description` and a `body` list of typed controls. A text input uses
`type: input`, `id`, `attributes.label` and optional `validations.required`.
Markdown issue/PR templates are a separate format. GitLab description templates
live in `.gitlab/issue_templates/` and `.gitlab/merge_request_templates/` as
Markdown. Ask for reproduction evidence in required fields. [GitHub
forms][source-2],
[GitLab templates](https://docs.gitlab.com/user/project/description_templates/).

Use questions that collect reproduction, expected/actual result and relevant
environment without requesting secrets. Distinguish documented policy from
configured enforcement. Retain license terms and attribution.

[source-2]:
  https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms

## Validation and policy boundaries

Use the provider's documented syntax and error reporting, not a home-grown
CODEOWNERS matcher. A generic gitignore library does not prove provider parity.
Test representative paths: a default-owned file, a narrower override, and an
intentionally unowned path when one exists. Check owner identity and access
through authorized read-only provider access when available; otherwise label
those checks unverified. Local parsing cannot establish hosted approvals.

For forms, YAML parsing is only the first check. Verify supported control types,
unique IDs, labels, required-field behavior, and referenced existing labels or
assignees against the provider. Do not invent a private schema version. An
issue-form required field is input assistance, not an authorization or permanent
completeness guarantee: users can edit the resulting issue body.

Review the rendered template on the intended provider when authorized and
available. Do not create test issues or mutate settings merely to validate local
files. Distinguish unsupported syntax from unavailable account access and from
policy choices requiring user approval. Preserve existing policy unless the task
authorizes changing it; documentation does not itself enforce merge conditions.

For GitHub policies requiring approval from each of several teams, current
[ruleset required reviewers][reviewers] provide per-team approval counts and
file patterns for organization-owned repositories. This is not CODEOWNERS
syntax: those ruleset patterns support ordered negation. Confirm plan
availability, team write access, active rules and bypasses before claiming
enforcement. Do not change hosted settings as an incidental consequence of
editing governance files.

[reviewers]:
  https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets#required-reviewers
