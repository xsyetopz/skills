# Document formats and governance semantics

Research: 2026-09-09. Baselines: Keep a Changelog 1.1.0, SemVer 2.0.0, current
GitHub/GitLab documentation.

## README and contribution workflow

Lead a README with what the project does and one representative result. Follow
with supported prerequisites, installation from a stated directory, the smallest
useful command, expected output location, and links to deeper
configuration/troubleshooting. Derive package names and flags from the
executable/manifests. Separate contributor builds from end-user installation; a
source checkout may require tools that a release binary does not.

State the working directory, exact command, required environment, and expected
output for each procedure. Verify package names, flags, and output paths against
the implementation. Limit platform claims to supported targets.

Write CONTRIBUTING around the supported change path: setup, focused/full checks,
code generation, how to submit a useful issue/PR, and existing review
conventions. Link existing security reporting and licensing policy; do not
create signing, DCO/CLA, conduct or disclosure requirements without authority.
Give an actionable fix for each prerequisite failure.

## Changelog and release notes

Use Keep a Changelog 1.1.0 for `CHANGELOG.md`. Normalize a nonconforming
changelog when it is the requested document. Retain release facts, dates,
version identifiers, and useful history. Put Unreleased first, followed by
releases in reverse chronological order with `YYYY-MM-DD` dates. Organize
user-visible entries under applicable Added, Changed, Deprecated, Removed, Fixed
and Security categories; omit empty categories. Example:

```markdown
# Changelog

## [Unreleased]

### Fixed

- Fix lost empty filters when loading saved searches.

## [2.0.0] - 2026-09-09

### Removed

- Remove `old-search`; use `search --legacy-format` for the previous output
  format.

[Unreleased]: https://github.com/OWNER/REPO/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/OWNER/REPO/compare/v1.9.0...v2.0.0
```

Replace example paths and refs with verified values. Link each release to its
comparison or tag. Mark withdrawn releases `[YANKED]` and retain their entries.
[Keep a Changelog][ref-1].

Apply SemVer 2.0.0 when selecting release versions for a declared public API:
incompatible changes increment major, compatible functionality minor, compatible
fixes patch. `0.y.z` denotes initial development, not an assurance of
compatibility. Prerelease identifiers sort below the corresponding normal
version; build metadata does not affect precedence. A `v` prefix can be a
Git-tag convention but is outside the version grammar. Removing a public
entrypoint can be breaking even if internal compilation succeeds.
[SemVer 2.0.0](https://semver.org/).

Write release notes with trigger, before/after behavior, affected users,
compatibility and migration steps. Use commits/issues as evidence, not a raw log
dump. Distinguish the release tag, artifact version, publication date and
prerelease channel.

## CODEOWNERS is provider-specific

GitHub searches `.github/`, root, then `docs/` and uses the first CODEOWNERS
file found. Patterns generally follow gitignore-style matching, but negation and
bracket ranges are unsupported. The last matching pattern wins; owners for a
single rule belong on the same line. Owners need appropriate repository access.
Review requests use the base branch's file; mandatory approval additionally
requires configured branch protection/rules. [GitHub code owners][ref-2].

```text
* @example/maintainers
/docs/ @example/docs
/docs/security.md @example/security @example/docs
```

Use GitLab sections and approval syntax for GitLab CODEOWNERS. Required Code
Owner approvals depend on the relevant tier/protected-branch settings; writing
the file alone does not activate enforcement. Review its section defaults,
exclusions and number-of-approvals rules before changing them. [GitLab Code
Owners][ref-3].

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
forms][ref-4], [GitLab templates][ref-5].

Use questions that collect reproduction, expected/actual result and relevant
environment without requesting secrets. Distinguish documented policy from
configured enforcement. Retain license terms and attribution.

## Bundled validator contracts

From the skill directory (or using absolute script paths):

```sh
python3 scripts/audit_changelog.py CHANGELOG.md --json
python3 scripts/audit_semver.py 1.2.3 v2.0.0-rc.1 --json
python3 scripts/audit_semver.py --from-changelog CHANGELOG.md
python3 scripts/audit_semver.py --from-tags
```

Helper output: changelog JSON contains `path`, `findings`, and `versions`.
SemVer JSON is a list of records. Errors produce failure status; warnings do
not. Read stderr for CLI/source failures. `--from-tags` reads tags from the
current repository. Check release completeness, public API impact, links, and
factual claims separately.

[ref-1]: https://keepachangelog.com/en/1.1.0/
[ref-2]:
  https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners
[ref-3]: https://docs.gitlab.com/user/project/codeowners/
[ref-4]:
  https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms
[ref-5]: https://docs.gitlab.com/user/project/description_templates/
