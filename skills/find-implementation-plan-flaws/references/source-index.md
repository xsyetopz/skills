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
| [Google engineering code review](https://google.github.io/eng-practices/review/reviewer/looking-for.html) | Use for evidence-based correctness, complexity, and scope review. |
| [Google Engineering Practices — small changes](https://google.github.io/eng-practices/review/developer/small-cls.html) | Use for dependency-local, reviewable plan steps and avoiding unrelated work. |
| [Microsoft Azure Architecture Center — design principles](https://learn.microsoft.com/en-us/azure/architecture/guide/design-principles/) | Use to evaluate whether architecture decisions address actual quality attributes and constraints. |
| [SEI Architecture Tradeoff Analysis Method](https://insights.sei.cmu.edu/library/architecture-tradeoff-analysis-method-collection/) | Use for risk- and scenario-based architecture evaluation; do not impose ATAM ceremony on routine changes. |
| [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) | Use when interpreting normative requirement language in applicable specifications. |
| [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174) | Use with RFC 2119 for the capitalization convention and updated interpretation. |

## Updating this reference

Update a link only after confirming the replacement covers the same contract. If
a source disappears, preserve the rule supported by local evidence and mark the
external verification gap; do not invent a new behavior from memory.
