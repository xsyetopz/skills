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
| [Semantic Versioning 2.0.0](https://semver.org/) | Use when the project declares SemVer-governed public APIs. |
| [Node package entry points](https://nodejs.org/api/packages.html#package-entry-points) | Use for actual Node package export/public-surface analysis. |
| [Go 1 compatibility promise](https://go.dev/doc/go1compat) | Example of an explicit language compatibility contract; apply only to matching Go surfaces. |
| [Rust API evolution and SemVer compatibility](https://doc.rust-lang.org/cargo/reference/semver.html) | Use for Rust public crate compatibility when the project follows Cargo SemVer rules. |
| [Java SE binary compatibility](https://docs.oracle.com/javase/specs/jls/se21/html/jls-13.html) | Use for Java binary compatibility decisions under the matching language version. |
| [.NET library change rules](https://learn.microsoft.com/en-us/dotnet/core/compatibility/library-change-rules) | Use for .NET public library compatibility; do not transfer to private APIs automatically. |

## Updating this reference

Update a link only after confirming the replacement covers the same contract. If
a source disappears, preserve the rule supported by local evidence and mark the
external verification gap; do not invent a new behavior from memory.
