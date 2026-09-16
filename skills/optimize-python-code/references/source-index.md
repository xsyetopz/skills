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
| [Python profiling](https://docs.python.org/3/library/profile.html) | Built-in deterministic profiling. |
| [tracemalloc](https://docs.python.org/3/library/tracemalloc.html) | Python allocation tracing. |
| [pyperf](https://pyperf.readthedocs.io/en/latest/) | Robust Python benchmark runner. |
| [Free-threaded Python HOWTO](https://docs.python.org/3/howto/free-threading-python.html) | Use only for matching Python builds and extensions. |
| [pyperf.readthedocs.io: api.html](https://pyperf.readthedocs.io/en/latest/api.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [pyperf.readthedocs.io: runner.html](https://pyperf.readthedocs.io/en/latest/runner.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |

## Updating this reference

Update a link only after confirming the replacement covers the same contract. If
a source disappears, preserve the rule supported by local evidence and mark the
external verification gap; do not invent a new behavior from memory.
