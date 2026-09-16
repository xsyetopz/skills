# Distinguish repository rules from enforced permissions

Read the project's existing ownership, contribution, security-reporting, and
release policies. Add only the governance mechanism the request needs; do not
generate a standard file bundle by default.

`CODEOWNERS` associates paths with owners under provider-specific matching and
precedence rules. Verify the exact provider, location, syntax, branch, and
referenced identities. Ownership declarations do not automatically require
review. Required reviews, status checks, push restrictions, and bypass
permissions live in provider settings or rulesets with their own scope.

For a branch rule, establish the exact protected branches/patterns, actor
permissions, required checks and their names, and how merge queues or generated
checks affect them. Avoid creating an impossible-to-satisfy check or
unexpectedly blocking the process that updates the branch. Do not broaden bypass
access merely to get a rule change through.

A security policy describes a reporting channel; it must not invent a mailbox,
support SLA, private disclosure program, or maintainer identity. A contribution
guide should state actual commands and expectations, not claim every contributor
has access to a private system.

Use native controls and leave access to provider-specific features. When
permissions are insufficient, separate a prepared file/change proposal from a
setting actually applied. Verify enforced settings through an authoritative read
where possible; a repository file or screenshot of intended configuration is not
equivalent.

Sources: [GitHub CODEOWNERS][ref-github-codeowners], [GitHub
rulesets][ref-github-rulesets], [GitLab protected
branches][ref-gitlab-protected-branches], [Bitbucket branch
permissions][ref-bitbucket-branch-permissions].

[ref-github-codeowners]: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners
[ref-github-rulesets]: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets
[ref-gitlab-protected-branches]: https://docs.gitlab.com/user/project/repository/branches/protected/
[ref-bitbucket-branch-permissions]: https://support.atlassian.com/bitbucket-cloud/docs/use-branch-permissions/
