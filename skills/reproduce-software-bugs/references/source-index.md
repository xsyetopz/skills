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
| [Stack Overflow minimal reproducible example](https://stackoverflow.com/help/minimal-reproducible-example) | Useful completeness/minimality guidance; repository and disclosure rules still control the artifact. |
| [LLVM — How to submit a bug](https://llvm.org/docs/HowToSubmitABug.html) | Use for compiler/toolchain reproductions and preprocessed or reduced test cases. |
| [Mozilla Bugzilla — Bug writing guidelines](https://bugzilla.mozilla.org/page.cgi?id=bug-writing.html) | Use for observed/expected result, environment, and reproduction quality. |
| [GitHub issue forms schema](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-githubs-form-schema) | Use only when the target repository uses GitHub issue forms. |
| [C-Reduce](https://embed.cs.utah.edu/creduce/) | Use for semantics-preserving reduction of C-family and other text-based test cases when applicable. |

## Updating this reference

Update a link only after confirming the replacement covers the same contract. If
a source disappears, preserve the rule supported by local evidence and mark the
external verification gap; do not invent a new behavior from memory.
