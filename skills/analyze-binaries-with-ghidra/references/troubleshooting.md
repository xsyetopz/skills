# Troubleshooting Ghidra access

## Contents

- [Project lock](#project-lock)
- [Missing or stale exports](#missing-or-stale-exports)
- [Wrong program name](#wrong-program-name)
- [JDK or Ghidra not found](#jdk-or-ghidra-not-found)
- [MCP server problems](#mcp-server-problems)
- [Sources](#sources)

## Project lock

**Symptom.** A headless open (`ghidra-bridge export`, `pyghidra-mcp`,
`analyzeHeadless`) fails with `Unable to lock project!`, from a
`LockException`.

**Cause.** Another process holds the project's lock: usually the Ghidra GUI
with the project open, sometimes a second MCP server or export.

**Action.** Ask the user to close the project in the GUI, or stop the other
server, then retry. When the GUI must stay open, copy the whole project
directory (the `.gpr` file and its `.rep` directory) and point
`project_dir` or `--project-path` at the copy. A copy does not see later
GUI changes; export again after the user saves.

Do not delete lock files to force the open: the other process still writes
to the project.

## Missing or stale exports

**Symptom.** `ghidra-bridge info` reports nothing, or `search` and
`decompile` find nothing for a function that exists in Ghidra.

**Checks.**

1. `ghidra-bridge info` with the same working directory and environment as
   the failing command. A different directory can load a different
   `ghidra-bridge.yaml`, or `~/.config/ghidra-bridge/`.
1. `echo "$GHIDRA_EXPORT_DIR"`: the environment overrides the YAML file.
1. If `paths.export_dir` is unset, the exports are under
   `~/.ghidra-exports`, not the project.
1. If the directory is empty or the export log ends in an error, fix that
   error and export again.

**Stale.** Renamed symbols or new types in Ghidra do not appear until the
next export. Export only the changed type (`export structs`, `export
decompiled`) when that is enough.

## Wrong program name

**Symptom.** The export or server opens the project but reports that the
program does not exist, or answers about a different binary.

**Action.** List the names inside the project with
`uvx pyghidra-mcp --project-path <path> --list-project-binaries`, or read
them from the Ghidra project window. The name is the one Ghidra shows,
which can differ from the file name on disk if the program was renamed on
import. Check `GHIDRA_PROGRAM_NAME` too, because it overrides the YAML
file.

## JDK or Ghidra not found

**Symptom.** The command fails before any analysis starts, with a JVM,
Java, or Ghidra-installation error.

**Checks.**

1. `java -version` reports the JDK version that the Ghidra release
   requires: 21 (64-bit) for Ghidra 12.1.4.
1. `GHIDRA_INSTALL_DIR` or `ghidra.install_dir` points at the directory
   that contains `ghidraRun` and `support/`.
1. The Python running PyGhidra is inside the supported range (3.9 to 3.14
   for Ghidra 12.1.4) and `ghidra-ai-bridge[headless]` or `pyghidra-mcp` is
   installed in it.

Installing a JDK or Ghidra is a user decision; name the missing piece and
the version instead of installing it.

## MCP server problems

| Symptom | Action |
| --- | --- |
| Tools absent from the session | `claude mcp list`; the server registered at a scope that this project does not load, or the session started before registration |
| Server exits at start | Run the same `uvx pyghidra-mcp ...` command in a terminal and read its error, usually one of the cases above |
| Searches empty right after start | Indexing still running; wait, or restart with `--wait-for-analysis` |
| Several sessions each start a JVM | Switch to one `streamable-http` server and register its URL |
| `--gui` refused | `--gui` needs `--transport streamable-http` |

When the MCP server cannot be made to work within the task, switch to the
`ghidra-bridge` CLI path and tell the user why.

## Sources

- Ghidra `DefaultProjectData.java` and `HeadlessAnalyzer.java` (project
  lock, `LockException`, `Unable to lock project!`):
  <https://github.com/NationalSecurityAgency/ghidra>
- [Ghidra 12.1.4 installation guide][ghidra-install] (JDK 21, PyGhidra
  Python versions).
- pyghidra-mcp README (`--list-project-binaries`, `--gui`, start-up
  defaults): <https://github.com/clearbluejar/pyghidra-mcp>
- ghidra-bridge README and source (configuration lookup and priority):
  <https://github.com/Dryxio/ghidra-bridge>

[ghidra-install]: https://github.com/NationalSecurityAgency/ghidra/blob/Ghidra_12.1.4_build/GhidraDocs/InstallationGuide.md
