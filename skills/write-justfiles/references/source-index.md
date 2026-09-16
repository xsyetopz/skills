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
| [Just programmer’s manual](https://just.systems/man/en/) | Current syntax and command behavior; match installed version. |
| [Just releases](https://github.com/casey/just/releases/latest) | Check feature availability and changes. |
| [just.systems: functions.html](https://just.systems/man/en/functions.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [Bash manual](https://www.gnu.org/software/bash/manual/bash.html) | Use only when the selected recipe shell is Bash. |
| [PowerShell about parsing](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_parsing) | Use for recipes executed by PowerShell; do not apply Bash quoting rules. |
| [POSIX shell command language](https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html) | Use for portable sh recipes under a POSIX shell. |

## Updating this reference

Update a link only after confirming the replacement covers the same contract. If
a source disappears, preserve the rule supported by local evidence and mark the
external verification gap; do not invent a new behavior from memory.
