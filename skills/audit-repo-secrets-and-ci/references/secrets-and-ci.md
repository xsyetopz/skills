# Secrets and CI

Checked against gitleaks 8.30.1, trufflehog 3.98.0, and zizmor 1.30.1 (October 2026). Run
`<tool> --version` and read the docs for the installed version before you trust a flag here.

## Contents

- [Secret Scanning](#secret-scanning)
- [A Secret Was Found](#a-secret-was-found)
- [GitHub Actions Audit](#github-actions-audit)
- [Repository Settings](#repository-settings)

## Secret Scanning

- `gitleaks git --redact .` scans every ref in the clone: with no `--log-opts` it runs
  `git log -p -U0 --full-history --all`. Passing `--log-opts` replaces that default, so a range
  needs `--log-opts="--all A..B"`. A shallow clone (`fetch-depth: 1` in CI) hides the history;
  check with `git rev-parse --is-shallow-repository` and run `git fetch --unshallow` first
  ([gitleaks][gitleaks], [git.go][gitleaks-git]).
- `gitleaks dir --redact .` scans the working tree, including untracked and ignored files that a
  history scan never sees (`.env`, local build output).
- Exit codes: 0 no leaks, 1 leaks or error, 126 unknown flag. Write a report with
  `-f json -r gitleaks.json` and read it instead of parsing the console output.
- Suppressions to review, not trust: `gitleaks:allow` comments, `.gitleaksignore` fingerprints,
  `[[allowlists]]` in `.gitleaks.toml`, and a `--baseline-path` report. Each one can hide a live
  secret. List each one in the report with what it hides.
- trufflehog is a second detector with different rules:
  `trufflehog git file://. --no-verification --json` and
  `trufflehog filesystem . --no-verification --json`. Verification sends each candidate secret to
  its provider's API (for AWS, a `GetCallerIdentity` call), so never run it without
  `--no-verification`. `--fail` exits 183 on results; `trufflehog:ignore` comments suppress
  ([trufflehog][trufflehog]).
- Look beyond the scanners' rules: `.env*`, `*.pem`, `*.p12`, `id_rsa*`, `*.tfstate`, `*.kdbx`,
  kubeconfig, `.npmrc` and `.pypirc` with tokens, CI variables printed in committed logs, and
  secrets baked into Docker image layers or test fixtures that ship.

## A Secret Was Found

- Report the rule, the file, the line, and the commit, with the value redacted to a prefix. Take
  the commit from the redacted `gitleaks git` JSON (`Commit`, `File`, `StartLine`), not from
  `git log -S` with the value, which puts the secret in the shell history and the transcript.
- Rotation comes first. GitHub's guide says to revoke or rotate a leaked secret as the first step,
  and that rewriting history may not be needed once it is rotated ([removing sensitive
  data][gh-remove]). Rotation is the owner's step: never test whether the secret still works.
- Deleting the line does not remove the secret. After a history rewrite (`git filter-repo`) and a
  force push, the commits stay reachable in clones and forks, by SHA in GitHub's cached views, and
  through pull requests that reference them. Only GitHub Support can clear cached views and PR
  refs.
- Before a repository goes public, every secret anywhere in its history counts, because the
  history goes public with it.
- Prevention to recommend: push protection ([push protection][gh-push]), a gitleaks pre-commit or
  CI job, and secrets in the CI secret store or an OIDC trust instead of files.

## GitHub Actions Audit

- Run `zizmor --persona=auditor --format=json .` over the whole repository; it also reads
  `action.yml` files and Dependabot config. Without a token it runs offline and skips
  `impostor-commit`, `known-vulnerable-actions`, `ref-confusion`, and `stale-action-refs`; pass
  `--gh-token "$(gh auth token)"` to run them, and name the skipped audits when you cannot. Exit
  codes 11 to 14 mean findings at informational to high severity ([zizmor audits][zizmor]).
- `# zizmor: ignore[<audit>]` comments and `zizmor.yml` rules are suppressions; list them like
  gitleaks allows.
- Trace each finding to the attacker: who controls the input (a fork PR author, an issue commenter,
  anyone who can open a PR), which secret or token scope the job holds, and what the job can write.
  A `dangerous-triggers` finding on a workflow that never checks out PR code and holds no secrets
  is a hardening note.
- The pwn request: `pull_request_target` or `workflow_run` plus a checkout or run of PR code.
  Since 2025-12-08, `pull_request_target` always takes the workflow file and default checkout from
  the default branch ([changelog][gh-prt]). An explicit checkout of
  `github.event.pull_request.head.sha` still runs the attacker's code with the base repository's
  secrets and cache.
- Script injection: `${{ github.event.* }}` text (titles, bodies, branch names, commit messages)
  inside `run:` or `actions/github-script` `script:` is code. Prove it with a local copy of the
  step: render the expression with a payload title and show the shell runs it.
- A tag or branch pin can be repointed by whoever controls the action; tj-actions/changed-files
  (CVE-2025-30066, March 2025) moved its tags to code that printed runner secrets into logs ([CISA
  alert][cisa]). Only a full commit SHA is immutable ([secure use][gh-secure]).
- Other audits that are findings when an attacker path exists: `artipacked` (token persisted by
  `actions/checkout` and uploaded as an artifact), `cache-poisoning` (a release job restores a cache
  that PR jobs write), `github-env` (untrusted data written to `GITHUB_ENV` or `GITHUB_PATH`),
  `secrets-inherit`, `excessive-permissions`, `self-hosted-runner`.
- Fixing a workflow follows `$write-ci-workflow`'s rules. Rerun zizmor after the fix; a finding is
  closed when zizmor no longer reports it and the job still does its work.

## Repository Settings

Workflow files are half of the attack surface. Read the settings with `gh` on repositories the user
administers; each is a finding only with the attacker path that it opens:

- Default token permissions and whether Actions may approve pull requests:
  `gh api repos/OWNER/REPO/actions/permissions/workflow`.
- Allowed actions and SHA-pinning enforcement (GitHub added the pinning policy on 2025-08-15,
  [changelog][gh-pin]): `gh api repos/OWNER/REPO/actions/permissions`.
- Fork pull request settings: whether fork workflows get write tokens or secrets, and whether
  first-time contributors need approval. Check under Settings > Actions > General.
- Self-hosted runners on a public repository: GitHub says they should almost never be used there,
  because any fork PR can run code on them ([secure use][gh-secure]).
- Environments that hold deploy secrets: required reviewers and branch rules
  (`gh api repos/OWNER/REPO/environments`).

[gitleaks]: https://github.com/gitleaks/gitleaks/blob/master/README.md
[gitleaks-git]: https://github.com/gitleaks/gitleaks/blob/master/sources/git.go
[trufflehog]: https://github.com/trufflesecurity/trufflehog/blob/main/README.md
[gh-remove]: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository
[gh-push]: https://docs.github.com/en/code-security/secret-scanning/introduction/about-push-protection
[zizmor]: https://docs.zizmor.sh/audits/
[gh-prt]: https://github.blog/changelog/2025-11-07-actions-pull_request_target-and-environment-branch-protections-changes/
[cisa]: https://www.cisa.gov/news-events/alerts/2025/03/18/supply-chain-compromise-third-party-github-action-cve-2025-30066
[gh-secure]: https://docs.github.com/en/actions/reference/security/secure-use
[gh-pin]: https://github.blog/changelog/2025-08-15-github-actions-policy-now-supports-blocking-and-sha-pinning-actions/
