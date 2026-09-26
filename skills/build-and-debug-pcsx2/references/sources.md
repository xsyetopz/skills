# Sources and verification record

Pinned sources behind the cards, and the verification tier of each example
set. Re-check any card whose source file changed after these revisions.

## Pinned revisions

| Source | Revision |
| --- | --- |
| [PCSX2 repository][repo] | `2c804670c5f2c99d6a6b842904dd222de89aa493` (tag `v2.9.84`, 2026-09-25) |
| [PCSX2 v2.8.2 release][rel] | macOS asset sha256 `3ed9eb40a33eae67134142c24255a079be444f0616ca29575a04a37981f7d426` |
| [pcsx2.net docs][www] | `3e9fea9ef3338b2d1b0ccedc237659642b51f9a7` |
| [lldb Darwin properties][lldb] | `main`, read 2026-09-25 |

## Files read at the pinned commit

| Topic | Files |
| --- | --- |
| Policy, licence | `AGENTS.md`, `CLAUDE.md`, `COPYING.GPLv3`, `pcsx2/Patch.cpp` SPDX line |
| Build | `CMakeLists.txt`, `CMakePresets.json`, `cmake/BuildParameters.cmake`, `cmake/SearchForStuff.cmake`, `pcsx2/CMakeLists.txt` |
| CI | `.github/workflows/macos_build.yml`, `linux_build_qt.yml`, `windows_build_qt.yml`, `scripts/macos/build-dependencies.sh` |
| CLI, data | `pcsx2-qt/QtHost.cpp`, `pcsx2/Pcsx2Config.cpp` (`EmuFolders`) |
| Logging | `pcsx2/VMManager.cpp` (`UpdateLoggingSettings`, `SetFileLogPath`) |
| Patches | `pcsx2/Patch.cpp`, `pcsx2/Patch.h`, `common/StringUtil.cpp`, `tests/ctest/core/patch_tests.cpp` |
| Renderer, textures | `pcsx2/Config.h`, `pcsx2/GS/Renderers/HW/GSTextureReplacements.cpp`, `pcsx2/GS/GS.cpp` |
| States | `pcsx2/SaveState.h`, `pcsx2/SaveState.cpp`, `pcsx2-qt/AutoUpdaterDialog.cpp` |
| Debugger | `pcsx2-qt/Debugger/Breakpoints/BreakpointDialog.ui`, `pcsx2/DebugTools/Breakpoints.h` |
| Host faults | `common/Darwin/DarwinMisc.cpp`, `common/CrashHandler.cpp` |
| GS runner | `pcsx2-gsrunner/Main.cpp`, `test_run_dumps.py`, `test_check_dumps.py` |

Docs read: [building][d-build], [CLI][d-cli], [debugger][d-dbg],
[writing patches][d-patch], [GS dump runner][d-gs], and
[diagnosing and reporting][d-id].

## Where the docs and the source disagree

- `gsaspectratio`: the docs list `Stretch` and `Auto 4:3/3:2`. The loader
  parses only `N:M` and logs `is an unknown aspect ratio` for anything
  else.
- GS runner renderers: the docs omit `metal`; `Main.cpp` accepts it on
  Apple.
- `test_check_dumps.py`: the docs add a `/pcsx2-gsrunner` level to
  `-baselinedir`; `test_run_dumps.py` does not create one.
- Linux configure line: the guide has `-fuse-ld` with no value for module
  linker flags; `AGENTS.md` and the presets use `-fuse-ld=lld`.

## Verification tiers

| Example set | Tier | Command | Result |
| --- | --- | --- | --- |
| PNACH checker, fixtures, command builder | Executed | `sh assets/examples/verify.sh` | `VERIFY PASSED` |
| Release CLI, isolation, logging, exit status | Executed | `sh assets/examples/verify.sh release` | `VERIFY PASSED` |
| macOS deps and configure | Executed with 2 local deviations | macOS build card | configure passed |
| PCSX2 compile | Executed, blocked | `ninja -k 0` | 904/1006; Metal Toolchain missing |
| Upstream unit tests | Executed | `ninja unittests` | 2/2 suites, 60 `Patch.*` tests |
| lldb on release copy | Executed | lldb card | breakpoint hit |
| Linux, Windows builds | Not runnable here | platform cards | no host |
| ccache | Not runnable here | ccache card | not installed |
| Guest debugging, renderer, textures, states | Not runnable here | their cards | needs a PS2 BIOS |
| GS runner | Not runnable here | GS runner card | needs the Metal shaders; no GS dumps bundled |

[repo]: https://github.com/PCSX2/pcsx2/tree/2c804670c5f2c99d6a6b842904dd222de89aa493
[rel]: https://github.com/PCSX2/pcsx2/releases/tag/v2.8.2
[www]: https://github.com/PCSX2/pcsx2-net-www/tree/3e9fea9ef3338b2d1b0ccedc237659642b51f9a7
[lldb]: https://github.com/llvm/llvm-project/blob/main/lldb/source/Plugins/Platform/MacOSX/PlatformMacOSXProperties.td
[d-build]: https://pcsx2.net/docs/advanced/building/
[d-cli]: https://pcsx2.net/docs/advanced/cli/
[d-dbg]: https://pcsx2.net/docs/advanced/debugger/
[d-patch]: https://pcsx2.net/docs/advanced/writing-patches/
[d-gs]: https://pcsx2.net/docs/advanced/gsdumprunner/
[d-id]: https://pcsx2.net/docs/troubleshooting/identify/
