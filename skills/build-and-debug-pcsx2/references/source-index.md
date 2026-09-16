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
| [PCSX2 source](https://github.com/PCSX2/pcsx2) | Authoritative upstream source and build/config behavior. |
| [PCSX2 documentation](https://pcsx2.net/docs/) | Official build, CLI, debugger, patch, and GS dump documentation. |
| [GitHub: PCSX2/pcsx2.git](https://github.com/PCSX2/pcsx2.git) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub source: PCSX2/pcsx2 — windows_build_qt.yml](https://github.com/PCSX2/pcsx2/blob/v2.8.2/.github/workflows/windows_build_qt.yml) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub source: PCSX2/pcsx2 — CMakeLists.txt](https://github.com/PCSX2/pcsx2/blob/v2.8.2/CMakeLists.txt) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub source: PCSX2/pcsx2 — test_check_dumps.py](https://github.com/PCSX2/pcsx2/blob/v2.8.2/pcsx2-gsrunner/test_check_dumps.py) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub source: PCSX2/pcsx2 — test_run_dumps.py](https://github.com/PCSX2/pcsx2/blob/v2.8.2/pcsx2-gsrunner/test_run_dumps.py) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub source: PCSX2/pcsx2 — QtHost.cpp](https://github.com/PCSX2/pcsx2/blob/v2.8.2/pcsx2-qt/QtHost.cpp) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub source: PCSX2/pcsx2 — GraphicsTextureReplacementSettingsTab.ui](https://github.com/PCSX2/pcsx2/blob/v2.8.2/pcsx2-qt/Settings/GraphicsTextureReplacementSettingsTab.ui) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub source: PCSX2/pcsx2 — GSTextureReplacements.cpp](https://github.com/PCSX2/pcsx2/blob/v2.8.2/pcsx2/GS/Renderers/HW/GSTextureReplacements.cpp) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub source: PCSX2/pcsx2 — VMManager.cpp](https://github.com/PCSX2/pcsx2/blob/v2.8.2/pcsx2/VMManager.cpp) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [pcsx2.net: building](https://pcsx2.net/docs/advanced/building/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [pcsx2.net: cli](https://pcsx2.net/docs/advanced/cli/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [pcsx2.net: debugger](https://pcsx2.net/docs/advanced/debugger/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [pcsx2.net: gsdumprunner](https://pcsx2.net/docs/advanced/gsdumprunner/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [pcsx2.net: writing patches](https://pcsx2.net/docs/advanced/writing-patches/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |

## Updating this reference

Update a link only after confirming the replacement covers the same contract. If
a source disappears, preserve the rule supported by local evidence and mark the
external verification gap; do not invent a new behavior from memory.
