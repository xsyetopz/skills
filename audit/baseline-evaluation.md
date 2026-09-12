# Baseline and language-coverage record

## Initial state

Baseline date: 2026-09-11; starting HEAD: `edcf0f2`. `SUMMARY.md` was absent.
The initial worktree already contained extensive uncommitted restructuring;
therefore neither the old committed catalog nor inherited edits were assumed
correct. [The file inventory](baseline-files.txt) records 38 initial skill
entrypoints and 407 files, including generated Gradle cache files.

Read GOAL.md and all seven supporting guidance files. The requested Agent Skills
specification, OpenAI Academy and OpenAI plugin skills sources were reviewed;
[discovery evaluation](catalog-discovery.md) records the portable/client
boundary.

Initial validation from the contemporaneous working log:

- skills-ref revision `69ef37e9424c0a7ea9dd2293b559e43ec8176379` and bundled
  quick_validate both accepted all 38 packages;
- 20 existing Python tests passed across changelog, emulator and Sublime-core
  helpers; these did not establish real editor-host behavior;
- Ruff checks passed, while one embedded Markdown Python example needed
  formatter-owned correction;
- both scripts passed Bash syntax checks; ShellCheck SC1007 was corrected by
  making the empty CDPATH assignment explicit;
- structured parsing covered 38 YAML, seven JSON, five TOML, nine XML and ten
  Python files; binary Gradle caches were not treated as source;
- short-description lengths and default-prompt skill names were checked, without
  claiming a complete client schema validator.

The first Markdown pass was misleading: its `.json` CLI2 configuration filename
was not discovered. The later [configuration evaluation][markdown] records the
real strict-policy failure and fixes. This supersedes the original green claim;
no baseline result is presented as proof of final correctness.

The accumulated temporary progress log is superseded by this baseline record,
the domain evaluations, [source intake](source-intake.md) and the
[completion audit](completion-checklist.md). It is not part of the skill
package.

## Language coverage decision

The September 2026 [TIOBE index][tiobe] was used as a discovery signal, not a
ranking of language suitability, code quality or required skill count. The
supplied ecosystem catalogs and the repository's actual editor, emulator and
performance toolchains supplied additional demand signals. Together they justify
focused general-purpose layout coverage for Python, C/C++, Java, C#/F#, Go,
Rust, JavaScript and TypeScript. Domain references separately cover Lua, Kotlin
and editor/runtime-specific ownership.

The final pass added explicit C/C++ linkage/header and Java package/module
boundaries instead of leaving those major ecosystems under generic advice.
Checked WG14's C23 working draft, the C++ Core Guidelines, and JLS 25. The draft
and guidelines are labeled accurately; they are not silently represented as a
new compiler mandate or the final ISO text. Existing real C++ emulator and JVM
plugin evidence remains scoped in its domain audits. No new uncompiled skeleton
or one-file-per-type template was introduced.

A popularity index does not justify an implementation skill for every listed
language or force a cross-language layout. Other languages retain a discovery
procedure tied to their actual compiler, package and consumer contracts.

[markdown]: markdown-configuration-evaluation.md
[tiobe]: https://www.tiobe.com/tiobe-index/
