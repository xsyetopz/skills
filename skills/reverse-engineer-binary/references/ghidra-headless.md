# Ghidra Headless, PyGhidra, and MCP Servers

Facts read on 2026-10-05. Latest stable Ghidra then was 12.1.4 (2026-09-21). The master branch
mentions "12.2 (October 2026)" but has no 12.2 tag or release, so treat it as unreleased.

## Contents

- [analyzeHeadless](#analyzeheadless)
- [PyGhidra](#pyghidra)
- [Ghidra MCP Servers](#ghidra-mcp-servers)
- [Unverified](#unverified)
- [Sources](#sources)

## analyzeHeadless

The script is `support/analyzeHeadless` under the Ghidra install (not `Common/support`). Syntax:

```text
analyzeHeadless <project_location> <project_name>[/<folder>]
  [[-import [<dir>|<file>]+] | [-process [<project_file>]]]
  [-preScript <Name> [args]] [-postScript <Name> [args]] [-scriptPath "<p1>[;<p2>]"]
  [-scriptlog <path>] [-log <path>] [-overwrite] [-recursive [<depth>]] [-readOnly]
  [-deleteProject] [-noanalysis] [-processor <languageID>] [-cspec <id>]
  [-analysisTimeoutPerFile <sec>] [-max-cpu <n>] [-loader <name>] [-loader-<arg> <value>]
```

Examples from the README:

```sh
analyzeHeadless /proj Project1 -import /bin/*.exe -noanalysis
analyzeHeadless /proj Project1/folderOne -scriptPath /scripts -postScript FixupScript.java \
  -process importedBinA.exe -noanalysis
```

Rules from the README:

- `-import` and `-process` are mutually exclusive.
- `-postScript` takes a script name with its extension, not a path. Repeat the option for several
  scripts. `-scriptPath` accepts `$GHIDRA_HOME` and `$USER_HOME`; on Unix escape them with `\`.
- Analysis is on by default. `-noanalysis` turns it off.
- `-overwrite` applies to import only and is ignored with `-readOnly`. Without it, conflicting files
  are skipped.
- `-readOnly`: on import the files are not saved, and in process mode changes are discarded.
  `-deleteProject` is implied on import, and it deletes only projects created in the current
  session.
- `-processor` takes the exact ID from the `.ldefs` files, for example `x86:LE:32:default`. Use it
  for raw firmware. `-cspec` requires `-processor`.
- `-max-cpu <n>`: 0 or negative means one core.
- Headless may fail if the project is open in the GUI. Files starting with `.` are skipped in bulk
  import.
- Loader names are short: `BinaryLoader`, `ElfLoader`, `PeLoader`, `MachoLoader`. `BinaryLoader`
  takes `-loader-baseAddr`, `-loader-blockName`, `-loader-fileOffset`, `-loader-length`,
  `-loader-applyLabels`, and `-loader-anchorLabels`. `ElfLoader` takes `-loader-imagebase` and
  others.
- In Python scripts `print` goes to stdout and `println` goes to the script log.

Processor IDs listed by the Trail of Bits `ghidra-headless` skill: `x86:LE:32:default`,
`x86:LE:64:default`, `ARM:LE:32:v7`, `AARCH64:LE:64:v8A`, `MIPS:BE:32:default`,
`PowerPC:BE:32:default`. That skill also wraps headless runs with export scripts (`ExportAll` and
others) and advises `export MAXMEM=4G` and a timeout for large inputs. It says not to use headless
when source exists, when interactive debugging or dynamic analysis is needed, or for .NET and Java.

## PyGhidra

- PyPI `pyghidra` was 3.1.0 (2026-05-14); the source on master says 3.3.0. It needs Ghidra 12.0 or
  later for the standalone library, and Python 3.9 to 3.14.
- Install with `pip install pyghidra`. Offline:
  `pip install --no-index -f <GHIDRA>/Ghidra/Features/PyGhidra/pypkg/dist pyghidra`.
- Set `GHIDRA_INSTALL_DIR`, or call `pyghidra.start(install_dir=...)`.
- History: 11.3 made PyGhidra built in. In 12.0 Python scripts without `@runtime` default to
  PyGhidra, and Jython scripts need `# @runtime Jython`. In 12.1 Jython became an optional
  extension, and 12.1.1 removed `jythonRun`.
- Current API: `start`, `started`, `open_project(path, name, create=False)`, `open_filesystem`,
  `consume_program`, `program_context(project, path)` (a context manager), `analyze(program)`,
  `analysis_properties`, `ghidra_script`, `transaction(program, description)`, `walk_programs`,
  `program_loader()` (chain
  `.project().source().name().loaders("BinaryLoader") .language("DATA:LE:64:default").load()`), and
  `task_monitor()`.
- Deprecated but present: `open_program` and `run_script`. With them `nested_project_location=True`
  adds an extra directory level; set it to `False` to open a project created in the GUI.
- The `pyghidra` command takes `binary_path script_path`. Flags: `-v`, `-d`, `-g/--gui`,
  `--install-dir`, `--skip-analysis`, `--project-name`, `--project-path`, `-D`, `-X`. With no script
  it opens a REPL.

## Ghidra MCP Servers

| Server | Mode | State at read time |
| - | - | - |
| `clearbluejar/pyghidra-mcp` | Headless first | v0.2.7 (2026-09-25), on PyPI |
| `bethington/ghidra-mcp` | GUI plugin and headless server | Release v6.0.0 (2026-07-25) |
| `LaurieWired/GhidraMCP` | GUI plugin only | Release 1.4 (2025-06-23), looks stale |

`pyghidra-mcp`:

- Start: `uvx pyghidra-mcp --transport streamable-http --project-path /abs/projects /abs/binary`. It
  serves `http://127.0.0.1:8000/mcp`. stdio is the fallback and SSE is legacy. Docker image:
  `ghcr.io/clearbluejar/pyghidra-mcp`.
- Register: `claude mcp add --transport http pyghidra-mcp http://127.0.0.1:8000/mcp`. A `.mcp.json`
  entry needs `"type":"http"`. `pyghidra-mcp-cli` is an HTTP client.
- `--gui` launches its own Ghidra and does not attach to a running GUI. Startup is asynchronous, so
  analysis runs in the background.
- Read tools: `search_code`, `list_xrefs`, `gen_callgraph`, `decompile_function` (accepts a list;
  options `include_callees`, `include_strings`, `include_xrefs`, `timeout_sec`), `list_exports`,
  `list_imports`, `read_bytes`, `search_strings`, `search_symbols_by_name`. Project tools:
  `import_binary`, `list_project_binaries`, `list_project_binary_metadata`, `delete_project_binary`.
  Write tools: `rename_function`, `rename_variable`, `set_variable_type`, `set_function_prototype`,
  `set_comment`. GUI-only: `list_open_programs`, `open_program_in_gui`, `set_current_program`,
  `goto`.

`bethington/ghidra-mcp` (Apache-2.0):

- The README on main describes 7.0.0 and 253 tools; the latest GitHub release is v6.0.0, and tags
  `v7.0.0-rc.1` and `v5.14.2` exist. It is a GUI plugin (default port 8080) plus a standalone
  `GhidraMCPHeadlessServer`; 27 tools are GUI-only and 14 headless-only.
- Headless: `java -jar GhidraMCPHeadless.jar --bind ... --port 8089`, or
  `docker-compose up -d ghidra-mcp`. MCP bridge: `uv run --directory <repo> bridge-mcp-ghidra`.
- Needs Java 21, Maven 3.9+, Ghidra 12.1.3, and Python 3.10+. Its `.py` ghidra_scripts need the
  Jython extension.
- It has write tools and script execution. Security variables: `GHIDRA_MCP_AUTH_TOKEN`,
  `GHIDRA_MCP_ALLOW_SCRIPTS` (off by default since v5.4.1), `GHIDRA_MCP_FILE_ROOT`. A non-loopback
  bind is refused without a token.

`LaurieWired/GhidraMCP`: a Ghidra plugin serves HTTP on port 8080 and the Python bridge
`bridge_mcp_ghidra.py --ghidra-server http://127.0.0.1:8080/` is the MCP side. Install the extension
through File, Install Extensions, restart, then enable the plugin under File, Configure, Developer.
Last activity was 2025-06-23, so check that it still works with the installed Ghidra.

## Unverified

- That `support/pyghidraRun --headless <analyzeHeadless args>` runs `.py` post-scripts. It was
  inferred from `pyghidra_launcher.py` and never run.

## Sources

- Ghidra releases: <https://github.com/NationalSecurityAgency/ghidra/releases>
- Ghidra repository, master branch, with these files:
  `Ghidra/RuntimeScripts/support/analyzeHeadlessREADME.md`,
  `Ghidra/Features/PyGhidra/src/main/py/README.md`, and `GhidraDocs/GettingStarted.md`:
  <https://github.com/NationalSecurityAgency/ghidra>
- clearbluejar/pyghidra-mcp: <https://github.com/clearbluejar/pyghidra-mcp>
- bethington/ghidra-mcp: <https://github.com/bethington/ghidra-mcp>
- LaurieWired/GhidraMCP: <https://github.com/LaurieWired/GhidraMCP>
- Trail of Bits skills-curated, path `plugins/ghidra-headless`:
  <https://github.com/trailofbits/skills-curated>
