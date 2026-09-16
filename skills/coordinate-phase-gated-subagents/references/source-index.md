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
| [Bun rewrite account](https://bun.com/blog/bun-in-rust) | Use as one concrete multi-agent engineering example; do not copy its staffing counts as universal rules. |
| [NASA systems engineering fundamentals](https://www.nasa.gov/reference/2-0-fundamentals-of-systems-engineering/) | Use for phase and verification concepts when applicable, not as mandatory software process governance. |
| [Google engineering review practices](https://google.github.io/eng-practices/review/) | Use for evidence-based review and scoped changes. |
| [www.nasa.gov: 3 0 nasa program project life cycle](https://www.nasa.gov/reference/3-0-nasa-program-project-life-cycle/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [Google Engineering Practices — code review](https://google.github.io/eng-practices/review/reviewer/looking-for.html) | Use for evidence-based review scope and correctness. |
| [GitHub protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches) | Use for real merge/approval enforcement when hosted on GitHub. |
| [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html) | Use for least privilege and mutation authority across workers. |

## Updating this reference

Update a link only after confirming the replacement covers the same contract. If
a source disappears, preserve the rule supported by local evidence and mark the
external verification gap; do not invent a new behavior from memory.
