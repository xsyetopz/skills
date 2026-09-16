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
| [ISO/IEC/IEEE 29148 overview](https://www.iso.org/standard/72089.html) | Use only when the organization adopts this requirements-engineering standard. |
| [NASA systems engineering fundamentals](https://www.nasa.gov/reference/2-0-fundamentals-of-systems-engineering/) | Useful for requirements and verification concepts in suitable projects. |
| [NASA Systems Engineering Handbook](https://www.nasa.gov/reference/systems-engineering-handbook/) | Use for requirement characteristics, traceability, verification, and validation in systems work. |
| [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) | Use for normative terminology in specifications that adopt it. |
| [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174) | Use for the current BCP 14 capitalization convention. |
| [Google SRE — Service Level Objectives](https://sre.google/sre-book/service-level-objectives/) | Use when reliability targets and user-visible indicators are part of the authorized requirement. |
| [OWASP Abuse Case](https://owasp.org/www-community/Abuse_Case) | Use when security requirements need attacker-goal and misuse-case analysis. |

## Updating this reference

Update a link only after confirming the replacement covers the same contract. If
a source disappears, preserve the rule supported by local evidence and mark the
external verification gap; do not invent a new behavior from memory.
