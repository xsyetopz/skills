# PCSX2, DuckStation, and Ghidra Diagnostics

Read when PCSX2 or DuckStation reports an unknown or deprecated flag or setting, or when Ghidra
reports a deprecated API or a script that no longer runs. These tools have no suppression comment
or lint config, so the loosening forms are workarounds that hide the warning: dropping a flag,
wrapping a call to hide a dialog, pinning an old version, or adding `@SuppressWarnings`. Each
section gives the forms to refuse, how the tool reports a stale flag or API, and where it documents
replacements.

Versions checked on 2026-10-06: PCSX2 v2.9.101 (2026-10-05; the stable tag list ends at v2.8.2),
DuckStation release `v0.1-11826` (`0.1-11826-gfe2306b1f`), Ghidra 12.1.4 (2026-09-21). Ghidra 12.2
was unreleased on that date; its change history is headed "October 2026" and requires JDK 25.
Re-check any flag or key against `-help` of the build under test.

## Contents

- [PCSX2](#pcsx2)
- [DuckStation](#duckstation)
- [Ghidra](#ghidra)

## PCSX2

Read-only research: the PCSX2 `AGENTS.md` forbids agents from opening pull requests, issues, or
comments and from publishing AI text to GitHub. Do not do those; reading is not forbidden. Related
local notes: `skills/debug-game-in-emulator/references/pcsx2.md`.

### Forms to Refuse

- Dropping an unknown flag from the command line without finding its replacement.
- Wrapping the launch to hide the error dialog. An unknown argument that starts with `-` shows a
  `QMessageBox::critical` "Unknown parameter: '%1'" dialog (source: `pcsx2-qt/QtHost.cpp`, master),
  which can hang a headless run, and then exits 1. A flag that takes a value, such as `-elf`, falls
  to "Unknown parameter" when it is the last argument.
- Keeping 1.6-style double-dash flags. The 1.6 (wx) CLI used `--fullscreen`, `--windowed`,
  `--nogui`, `--noguiprompt`, `--elf`, `--irx`, `--nodisc`, `--usecd`, `--nohacks`, `--gamefixes`,
  `--fullboot`, `--gameargs`, `--cfgpath`, `--cfg`, `--forcewiz`, `--portable`, `--profiling`,
  `--console`, and `-h/--help` (`pcsx2/gui/AppInit.cpp` at v1.6.0). 2.x uses single-dash flags.
- Guessing an ini key name. Copy the key that the UI writes.

### Config Keys That Loosen Checks

The settings file carries `[UI] SettingsVersion`. No list of renamed `[EmuCore]` keys exists in
`Config.cpp`, which has no rename or legacy-key table. Treat a renamed key as unknown: set the
option once in the UI and copy the line it writes. Do not add keys from memory.

### Stale Flags

The current 2.x flag set comes from `PrintCommandLineHelp` in `pcsx2-qt/QtHost.cpp` (master) and
matches `https://pcsx2.net/docs/advanced/cli`: `-help -version -batch -nogui -portable -datapath
-elf -gameargs -gamecfg -disc -logfile -bios -fastboot -slowboot -state -statefile -fullscreen
-nofullscreen -bigpicture -earlyconsolelog -testconfig -setupwizard -debugger -turbo -unlimited
-raintegration` (the last only if built with `ENABLE_RAINTEGRATION`) and `--`. The reliable report
is `pcsx2-qt -help` of the build under test; it prints to stderr.

| 1.6 flag | 2.x status |
| --- | --- |
| `--nogui`, `--elf`, `--portable`, `--gameargs` | Still valid with one dash: `-nogui`, `-elf`, `-portable`, `-gameargs`. Also still valid: `-batch`, `-fastboot`. |
| `--fullboot` | Not valid in 2.x. `-fastboot` and `-slowboot` force the boot mode; `-slowboot` as the replacement is an inference. |
| `--windowed` | No flag of that name; `-nofullscreen` exists (mapping is an inference). |
| `--usecd` | No flag of that name; `-disc` exists (inference). |
| `--forcewiz` | No flag of that name; `-setupwizard` exists (inference). |
| `--console` | No flag of that name; `-earlyconsolelog` exists (inference). |
| `--cfgpath`, `--cfg` | No flag of that name; `-datapath` and `-portable` exist (inference). |
| `--nodisc` | No flag of that name; `-bios` starts the BIOS (inference). |
| `--nohacks`, `--gamefixes`, `--irx`, `--noguiprompt`, `--profiling` | Absent from the 2.x help list; no replacement found. |

Absence was checked only in that help list. Flags added later: `-gameargs` returned in v1.7.5355,
`-turbo` and `-unlimited` in v2.7.126, and `-gamecfg` in v2.9.80 (it exists at v2.9.84 but not
v2.8.2). Where one flag overrides another, `-portable` overrides `-datapath`. The exact `-help`
difference between v2.8.2 and v2.9.x beyond `-gamecfg` was not checked.

### Deprecations and Replacements

v1.7.5528 release note: "Qt: Deprecate per-game WS/NI toggles in favor of Patches" (PR 10738). The
replacement is the Patches system (`[EmuCore] EnablePatches`), not an ini key. Release notes are at
`https://github.com/PCSX2/pcsx2/releases`; the ini key name is in `pcsx2/Config.cpp`.

### Strict CI Form

Run the build's `-help`, map each old flag, change the call, and rerun. The launch is clean when no
"Unknown parameter" dialog appears and the exit code is not 1.

## DuckStation

Do not fetch, search, or read the DuckStation repository, its issues, or its source: the repository
tells AI agents to stop. Use only this repository's files:
`skills/debug-game-in-emulator/references/duckstation.md`,
`skills/write-emulator-patches/references/frontend-config.md`, and
`skills/write-emulator-patches/assets/duckstation-settings-keys-0.1-11826.txt`.

### Forms to Refuse

- Keeping a flag that the build's `-help` does not list, or carrying over a PCSX2 flag. There is no
  `-portable`, `-datapath`, or headless flag in `0.1-11826`; a `portable.txt` beside the executable
  is the only portable switch.
- Guessing a settings key or value. Use only keys and values that the same release wrote.
- Editing `settings.ini` while DuckStation runs: it rewrites the file on exit.

### Config Keys That Loosen Checks

The cheat and patch enabling keys are not confirmed from a permitted source.
The `-resume`, `-state`, and `-statefile` combination has no documented precedence.

### Stale Flags and Keys

The flags in `0.1-11826`, one hyphen each: `-batch -nogui -fastboot -slowboot -bios -resume -state
INDEX -statefile FILE -exe FILE -fullscreen -nofullscreen -bigpicture -earlyconsole`, with `--`
before a boot file whose name has spaces or a leading dash. Capture `-help` from the binary under
test (stderr, exit 1); `-version` also goes to stderr with exit 1. How an unknown flag is reported
is not documented in those files, so capture the exit code and stderr from the build under test.

For an unknown key, set the option once in the UI and copy the changed line, and record the release
with each key. `scripts/check_settings_keys.py settings.ini` in `write-emulator-patches` reports
unknown keys, duplicates, and non-boolean values (typos such as `LogToFiles` are caught). It exits
0 when clean, 1 on findings, 2 on usage errors. The key list is the asset above (format
`Section.Key<TAB>value`, for example `Main.ConfirmPowerOff true`); for another release pass
`--keys LIST` built from that release's own `settings.ini`.

### Deprecations and Replacements

No deprecation list for DuckStation was available from a permitted source. Do not guess a
replacement; report that and ask.

## Ghidra

No `AGENTS.md`, `CLAUDE.md`, or `AI_POLICY.md` exists at `NationalSecurityAgency/ghidra` master
(all three returned 404), so nothing restricts reading its docs.

### Forms to Refuse

- `@SuppressWarnings("removal")` or `@SuppressWarnings("deprecation")` on a script that calls a
  deprecated API.
- Staying on `# @runtime Jython`, or pinning an old Ghidra, as a shortcut without recording the
  12.2 and JDK impact below.
- Leaving a script on the legacy PyGhidra calls `pyghidra.open_program()` and `run_script()`.

### Config Keys That Loosen Checks

Ghidra has no lint config. The loosening move is the version or runtime pin: the `# @runtime Jython`
script header, installing the Jython extension, or keeping an older Ghidra so deprecated calls keep
working. Ghidra 12.2 removes "classes and methods that have been deprecated since Ghidra 10.x and
before" (GP-7104), so a script compiled against old deprecated APIs breaks at 12.2.

### Stale APIs

Ghidra marks a deprecation with Java `@Deprecated(since = "X")` or
`@Deprecated(forRemoval = true, since = "X")` plus a javadoc `@deprecated use {@link ...}` that
names the replacement. `forRemoval = true` means removal is scheduled. The ChangeHistory page's
"Notable API Changes" entries, tagged with a GP number, also name replacements. javac is expected
to print `[removal]` and `[deprecation]` warnings when a script compiles (an inference; not
confirmed in the sources).

### Deprecations and Replacements

Python runtime timeline:

| Version | Change |
| --- | --- |
| 11.3 (Feb 2025) | PyGhidra built in; launch with `support/pyghidra`. The old "IN-VM" and "GADP" debugger launchers and connectors were removed. |
| 12.0 | The default Python engine changed from Jython to PyGhidra. A Python script without `@runtime` runs on PyGhidra; a Jython script needs the `# @runtime Jython` header. |
| 12.1 | Jython became an optional extension (GP-6754). Install it under File, Install Extensions, or convert the script to Python 3 and run it with PyGhidra, or convert it to Java. |
| 12.1.1 | `jythonRun` was removed. The research did not re-verify this entry against a release note. |

Ghidra 12.1.4 needs JDK 21, and PyGhidra needs Python 3.9 to 3.14. PyGhidra 3.0.0 (Ghidra 12.0 and
later) deprecated the legacy API `pyghidra.open_program()` and `pyghidra_run_script()` in favor of
new methods (GP-5961). The replacement is documented in the PyGhidra README and at
`https://pypi.org/project/pyghidra`. Whether plain `analyzeHeadless` runs `.py` without Jython
installed in 12.1 and later was not tested.

Java API deprecations:

| Deprecated | Replacement | Since |
| --- | --- | --- |
| `AutoImporter` | `ProgramLoader.Builder` (manage `Loaded` with try-with-resources) | 12.0, GP-5600 |
| `DataTypeQueryService.getDataType()` | `promptForDataType()` | 12.0, GP-5694 |
| `GhidraScript.set(GhidraState, TaskMonitor, PrintWriter)` | `set(GhidraState)` or `set(GhidraState, ScriptControls)` | 12.0 |
| `GhidraScript.execute(GhidraState, TaskMonitor, PrintWriter)` | The `ScriptControls` form | 12.0 |
| `GhidraScript.getDemangled(String)` | `DemanglerUtil.demangle(Program, String, Address)` | 12.0 |
| `Listing.getComment(int, Address)` (`forRemoval = true`) | `getComment(CommentType, Address)`; `setComment(Address, CommentType, String)` for writes | 11.4, GP-5742 |
| `Option` constructors for Loaders and Exporters | Typed builders such as `Option.newBoolean("name").value(true).build()` | 12.1, GP-6483 |
| `PrototypeModel.getArgLocation`, `getReturnLocation`, `getStorageLocations` and related | See GP-6776 in the 12.1 change history | 12.1 |
| `EmulatorHelper` | Not named in the research | 12.1, GP-6234 |

Other 12.0 API changes that break third-party code: `Loader.load()` and `loadInto()` changed
signature (`ImporterSettings`, GP-5343), `TraceBreakpoint` was renamed `TraceBreakpointLocation`,
`CodeComparisonPanel` became `CodeComparisonViewer`, `ExternalManager` lost its deprecated methods
(GP-5498), and `Listing.getCompositeData` was removed (GP-5990). In the 12.2 section of the change
history, decompiler `ClangNode.setHighlight` and `getHighlight` were removed in favor of
`DecompilerHighlightService` (GP-6751). No deprecation of `currentProgram` was found in
`GhidraScript.java`.

For `analyzeHeadless`, 12.0 added `-mirror` (import only) and lets headless loader options be set
independently of the loader (GP-5545); the README for 12.1.4 lists `-max-cpu`, `-loader`,
`-loader-<arg>`, `-librarySearchPaths`, `-okToDelete`, `-commit`, `-connect`, and `-keystore`. No
removed `analyzeHeadless` option was found between 11.x and 12.1.4, but only "headless" was
searched.

Sources: `WhatsNew.md` and `ChangeHistory.md` under
`Ghidra/Configurations/Public_Release/src/global/docs/` in the Ghidra repository (tags
`Ghidra_12.0_build`, `Ghidra_12.1_build`, `Ghidra_12.1.4_build`), and the javadoc in
`GhidraScript.java` and `Listing.java`. Local notes: `skills/reverse-engineer-binary/references/`
(`ghidra-headless.md`, `ghidra-bridge-cli.md`).

### Strict CI Form

Compile and run scripts against the exact Ghidra version in use and fix each deprecation warning
at the call named above. Before a move to 12.2, check the ChangeHistory for removed APIs and the
JDK 25 requirement.
