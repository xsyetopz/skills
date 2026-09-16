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
| [Git bisect documentation](https://git-scm.com/docs/git-bisect) | Normative Git behavior for start, run, skip, log, and reset. |
| [Git worktree documentation](https://git-scm.com/docs/git-worktree) | Use for isolated checkouts while preserving the active tree. |
| [Git revisions manual](https://git-scm.com/docs/gitrevisions) | Use to select and record unambiguous good/bad revisions. |
| [Git rev-parse manual](https://git-scm.com/docs/git-rev-parse) | Use for repository discovery and resolved revision identity. |
| [Git clean manual](https://git-scm.com/docs/git-clean) | Consult before any cleanup; do not use destructively without explicit authority. |

## Updating this reference

Update a link only after confirming the replacement covers the same contract. If
a source disappears, preserve the rule supported by local evidence and mark the
external verification gap; do not invent a new behavior from memory.
