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
| [Google SRE incident response](https://sre.google/workbook/incident-response/) | Use for incident discipline and evidence handling, not as a mandatory organizational process. |
| [Clang AddressSanitizer](https://clang.llvm.org/docs/AddressSanitizer.html) | Use for supported native memory-error investigations. |
| [Clang ThreadSanitizer](https://clang.llvm.org/docs/ThreadSanitizer.html) | Use for supported data-race investigations. |
| [GDB manual](https://sourceware.org/gdb/current/onlinedocs/gdb.html/) | Use for native process state, breakpoints, stacks, watchpoints, and core files. |
| [LLDB tutorial](https://lldb.llvm.org/use/tutorial.html) | Use for LLDB-native debugging on supported targets. |
| [Valgrind manual](https://valgrind.org/docs/manual/manual.html) | Use for supported dynamic analysis; account for overhead and platform limits. |
| [rr project](https://rr-project.org/) | Use for record/replay debugging on supported Linux workloads. |

## Updating this reference

Update a link only after confirming the replacement covers the same contract. If
a source disappears, preserve the rule supported by local evidence and mark the
external verification gap; do not invent a new behavior from memory.
