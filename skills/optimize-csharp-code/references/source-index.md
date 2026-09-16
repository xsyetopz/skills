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
| [BenchmarkDotNet good practices](https://benchmarkdotnet.org/articles/guides/good-practices.html) | Benchmark design and interpretation. |
| [.NET diagnostics](https://learn.microsoft.com/en-us/dotnet/core/diagnostics/) | Runtime trace/counter/dump tooling. |
| [.NET native interop best practices](https://learn.microsoft.com/en-us/dotnet/standard/native-interop/best-practices) | Interop contracts and marshalling. |
| [C# 14 changes](https://learn.microsoft.com/en-us/dotnet/csharp/whats-new/csharp-14) | Use only when target project actually selects C# 14. |
| [benchmarkdotnet.org: overview.html](https://benchmarkdotnet.org/articles/overview.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub: FontStashSharp/FontStashSharp](https://github.com/FontStashSharp/FontStashSharp) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub: StbSharp/StbImageSharp](https://github.com/StbSharp/StbImageSharp) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub: dotnet/BenchmarkDotNet/releases/tag/v0.15.8](https://github.com/dotnet/BenchmarkDotNet/releases/tag/v0.15.8) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [learn.microsoft.com: system.enum.hasflag](https://learn.microsoft.com/en-us/dotnet/api/system.enum.hasflag) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [learn.microsoft.com: system.enum.hasflag?view=net 10.0](https://learn.microsoft.com/en-us/dotnet/api/system.enum.hasflag?view=net-10.0) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [learn.microsoft.com: system.threading.tasks.valuetask](https://learn.microsoft.com/en-us/dotnet/api/system.threading.tasks.valuetask) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [learn.microsoft.com: dotnet counters](https://learn.microsoft.com/en-us/dotnet/core/diagnostics/dotnet-counters) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [learn.microsoft.com: dotnet trace](https://learn.microsoft.com/en-us/dotnet/core/diagnostics/dotnet-trace) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [learn.microsoft.com: msbuild props](https://learn.microsoft.com/en-us/dotnet/core/project-sdk/msbuild-props) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [learn.microsoft.com: evaluate items and properties](https://learn.microsoft.com/en-us/visualstudio/msbuild/evaluate-items-and-properties) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [learn.microsoft.com: msbuild command line reference](https://learn.microsoft.com/en-us/visualstudio/msbuild/msbuild-command-line-reference) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [wiki.libsdl.org: CategoryAPI](https://wiki.libsdl.org/SDL3/CategoryAPI) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [wiki.libsdl.org: SDL PollEvent](https://wiki.libsdl.org/SDL3/SDL_PollEvent) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [wiki.libsdl.org: SDL RenderGeometry](https://wiki.libsdl.org/SDL3/SDL_RenderGeometry) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [wiki.libsdl.org: SDL RenderPresent](https://wiki.libsdl.org/SDL3/SDL_RenderPresent) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [www.un4seen.com: doc](https://www.un4seen.com/doc/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |

## Updating this reference

Update a link only after confirming the replacement covers the same contract. If
a source disappears, preserve the rule supported by local evidence and mark the
external verification gap; do not invent a new behavior from memory.
