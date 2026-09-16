# Source index and freshness rules

This index is for source discovery and version checking. It is not a substitute
for the operational rules in `SKILL.md` and the other references. Open the
underlying source; do not treat a search snippet, generated summary, or copied
example as authority.

## Source order

1. Inspect the target repository, installed tool versions, lockfiles, generated
   relationships, and existing validation commands.
1. Use the exact product or language version's official documentation and
   source.
1. Use standards and protocol specifications for normative behavior.
1. Use issue trackers and community reports to discover failure patterns, then
   reproduce the relevant behavior locally before changing production code.

For changing products, record the page or source revision and access date in the
work product when the decision depends on it. Do not silently transfer an API or
limit from another version, fork, operating system, runtime, or hosting tier.

## Primary sources

| Source | Applicability |
| --- | --- |
| [Git reference manual](https://git-scm.com/docs/git) | Normative command behavior; use the installed Git version where behavior differs. |
| [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) | Use only when the repository adopts this commit-message convention. |
| [git-scm.com: git.txt GIT INDEX FILE](https://git-scm.com/docs/git#Documentation/git.txt-GIT_INDEX_FILE) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [git-scm.com: git cherry pick](https://git-scm.com/docs/git-cherry-pick) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [git-scm.com: git commit](https://git-scm.com/docs/git-commit) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [git-scm.com: git merge](https://git-scm.com/docs/git-merge) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [git-scm.com: git push](https://git-scm.com/docs/git-push) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [git-scm.com: git rebase](https://git-scm.com/docs/git-rebase) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [git-scm.com: git reflog](https://git-scm.com/docs/git-reflog) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [git-scm.com: git reset](https://git-scm.com/docs/git-reset) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [git-scm.com: git restore](https://git-scm.com/docs/git-restore) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [git-scm.com: git rev parse](https://git-scm.com/docs/git-rev-parse) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [git-scm.com: git revert](https://git-scm.com/docs/git-revert) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [git-scm.com: git stash](https://git-scm.com/docs/git-stash) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [git-scm.com: git status](https://git-scm.com/docs/git-status) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [git-scm.com: git tag](https://git-scm.com/docs/git-tag) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [git-scm.com: git worktree](https://git-scm.com/docs/git-worktree) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [git-scm.com: git write tree](https://git-scm.com/docs/git-write-tree) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [git-scm.com: githooks](https://git-scm.com/docs/githooks) | Use for the exact target version or source revision; verify applicability before copying an API or command. |

## Updating this reference

Update a link only after confirming the replacement covers the same contract. If
a source disappears, preserve the rule supported by local evidence and mark the
external verification gap; do not invent a new behavior from memory.
