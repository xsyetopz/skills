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
| [Clang optimization reports](https://clang.llvm.org/docs/UsersManual.html#options-to-emit-optimization-reports) | Compiler evidence for selected target/flags. |
| [GCC instrumentation options](https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html) | Profiling and sanitizer-related compiler controls. |
| [C standard drafts/resources](https://www.open-std.org/jtc1/sc22/wg14/www/projects.html) | Use the project-selected C standard; do not infer from latest draft. |
| [Linux perf wiki](https://perfwiki.github.io/main/) | Use for Linux sampling/counter workflows under the target kernel and permissions. |
| [GCC optimization options](https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html) | Use for actual GCC version flags and tradeoffs. |
| [Clang command guide](https://clang.llvm.org/docs/CommandGuide/clang.html) | Use for matching Clang target and optimization settings. |
| [Valgrind Callgrind manual](https://valgrind.org/docs/manual/cl-manual.html) | Use for supported instruction/call profiling; account for instrumentation distortion. |
| [POSIX specification](https://pubs.opengroup.org/onlinepubs/9799919799/) | Use for C/POSIX API behavior when the target contract is POSIX. |

## Updating this reference

Update a link only after confirming the replacement covers the same contract. If
a source disappears, preserve the rule supported by local evidence and mark the
external verification gap; do not invent a new behavior from memory.
