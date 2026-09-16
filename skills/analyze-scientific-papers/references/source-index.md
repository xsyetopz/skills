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
| [Crossref REST API](https://www.crossref.org/documentation/retrieve-metadata/rest-api/) | Use for DOI metadata discovery, not paper-content claims. |
| [OpenAlex API](https://docs.openalex.org/) | Use for discovery and citation relationships; verify works against primary records. |
| [PRISMA 2020](https://www.prisma-statement.org/prisma-2020) | Use when a systematic-review reporting framework is applicable; do not impose it on a narrow paper question. |
| [help.openalex.org: authentication](https://help.openalex.org/api/authentication/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [info.arxiv.org: index.html](https://info.arxiv.org/help/api/index.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [info.arxiv.org: user manual.html](https://info.arxiv.org/help/api/user-manual.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [pubmed.ncbi.nlm.nih.gov: help](https://pubmed.ncbi.nlm.nih.gov/help/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [www.crossref.org: retrieve metadata](https://www.crossref.org/documentation/retrieve-metadata/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [www.crossref.org: access and authentication](https://www.crossref.org/documentation/retrieve-metadata/rest-api/access-and-authentication/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |

## Updating this reference

Update a link only after confirming the replacement covers the same contract. If
a source disappears, preserve the rule supported by local evidence and mark the
external verification gap; do not invent a new behavior from memory.
