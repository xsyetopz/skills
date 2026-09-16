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
| [PEP 20 — The Zen of Python](https://peps.python.org/pep-0020/) | Normative text for the aphorisms; cross-language application is this skill’s policy, not a PEP requirement. |
| [Google Engineering Practices — code review](https://google.github.io/eng-practices/review/reviewer/looking-for.html) | Use for concrete maintainability and complexity review considerations. |
| [docs.python.org: contextlib.html](https://docs.python.org/3/library/contextlib.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [docs.python.org: errors.html](https://docs.python.org/3/tutorial/errors.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [Google C++ Style Guide](https://google.github.io/styleguide/cppguide.html) | Example of language/project-specific conventions that outrank Python syntax or naming. |
| [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/) | Use for Rust public API idioms when applicable. |
| [.NET Framework Design Guidelines](https://learn.microsoft.com/en-us/dotnet/standard/design-guidelines/) | Use for .NET public API design and naming when applicable. |
| [Go Code Review Comments](https://go.dev/wiki/CodeReviewComments) | Use for Go idioms; do not interpret PEP 20 as permission to replace them. |

## Updating this reference

Update a link only after confirming the replacement covers the same contract. If
a source disappears, preserve the rule supported by local evidence and mark the
external verification gap; do not invent a new behavior from memory.
