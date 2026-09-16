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
| [Keep a Changelog](https://keepachangelog.com/en/2.0.0/) | Use when the project follows or adapts this format. |
| [Semantic Versioning](https://semver.org/spec/v2.0.0.html) | Use only for projects whose public version policy adopts SemVer. |
| [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) | Use only when the project follows or adopts this human-facing changelog format. |
| [Common Changelog](https://common-changelog.org/) | Alternative changelog convention; preserve the repository-selected format. |
| [GitHub — automatically generated release notes](https://docs.github.com/en/repositories/releasing-projects-on-github/automatically-generated-release-notes) | Use when generating GitHub release notes from verified repository changes. |
| [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/) | Use only when the repository declares this commit convention; commit labels are not release truth by themselves. |

## Updating this reference

Update a link only after confirming the replacement covers the same contract. If
a source disappears, preserve the rule supported by local evidence and mark the
external verification gap; do not invent a new behavior from memory.
