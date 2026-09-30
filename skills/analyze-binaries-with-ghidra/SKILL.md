---
name: analyze-binaries-with-ghidra
description: >-
  Queries Ghidra projects from a coding agent: the pyghidra-mcp MCP server
  first, the ghidra-bridge CLI over exported data as the fallback. Covers
  setup, ghidra-bridge.yaml, the one-time export, the query order (search,
  decompile, xrefs, types), output limits, crash-address lookup, and
  project-lock errors. Use when asked to decompile, list xrefs, or explain a
  function in a binary the user may analyze, or when a ghidra-bridge.yaml
  exists. Not for the tool-independent method of reversing a function
  (calling conventions, type recovery), source-code security audits, or
  licence, DRM, or anti-cheat bypass.
---

# Analyze Binaries with Ghidra

Answer questions about a compiled program from a Ghidra project without
opening the Ghidra GUI. Two paths reach the same data:

- MCP: `pyghidra-mcp` (Apache-2.0) runs Ghidra through PyGhidra and serves
  it as MCP tools. Use it first.
- CLI: `ghidra-bridge` (PyPI `ghidra-ai-bridge`, MIT) reads data that it
  exported from the project once. It is not an MCP server and not a live
  connection to Ghidra. Use it when no MCP server is available or the MCP
  server fails.

Both need a user-installed Ghidra, a JDK (Ghidra 12.1.4 requires JDK 21,
64-bit), and Python 3.10 or newer.

## Scope

Analyze only binaries that the user may analyze: their own programs,
interoperability, preservation, security research they are allowed to do,
and matching-decompilation projects. Refuse, and say why, when the goal is
to bypass a licence check, DRM, or anti-cheat, or to analyze the coding
agent's own binary. The tooling is the same in every case; the purpose
decides.

## Workflow

1. Confirm the scope above and name the program: the Ghidra project
   directory, project name, and program name inside the project.
1. Check for a registered MCP server (`claude mcp list` in Claude Code). If
   `pyghidra-mcp` is listed and responds, use the
   [MCP path](#mcp-path). If it is missing, register it at project scope
   when the user agrees; otherwise use the [CLI path](#cli-path).
1. Run the [query order](#query-order): orient, search, decompile one
   function, follow xrefs, then read types. Stop when the question is
   answered.
1. Answer with the evidence: the function address and name, the decompiled
   lines that support each claim, and which parts are inference.

## MCP path

Register the server for this project only. Each server process starts a
Ghidra JVM, so a user-wide or plugin-wide registration starts one in every
session, including sessions that never touch a binary.

```bash
claude mcp add --scope project -e GHIDRA_INSTALL_DIR=/opt/ghidra \
  pyghidra-mcp -- uvx pyghidra-mcp --project-path /abs/path/proj.gpr
```

`--scope project` writes `.mcp.json` at the repository root, which other
contributors receive. Use `--scope local` when the paths exist only on one
machine.

- Transport: stdio is the default, and each client that launches the
  command gets its own JVM. When several clients or sessions should share
  one Ghidra process, start one server with `--transport streamable-http`
  and register its URL with `claude mcp add --transport http`.
- Analysis: by default the server starts before analysis and indexing
  finish, so `search_code` and `search_strings` can return incomplete
  results at first. Pass `--wait-for-analysis` when complete results
  matter more than start time.
- Editing tools (`rename_function`, `set_comment`, `delete_project_binary`,
  and others) change the Ghidra project. Call them only when the user asks
  for that change.

Registration, transports, and the tool list:
[MCP server card](references/mcp-server.md).

## CLI path

1. Install with the `headless` extra, because `export` needs PyGhidra:
   `pip install 'ghidra-ai-bridge[headless]'`, or any PyPI CLI installer
   such as `uv tool install`.
1. Write `ghidra-bridge.yaml` in the working directory (or run
   `ghidra-bridge init`). Set `paths.export_dir` explicitly: when it is
   unset the code default is `~/.ghidra-exports`, outside the project.
   Keys and environment overrides:
   [configuration](references/ghidra-bridge-cli.md#configuration).
1. Export once with `ghidra-bridge export all`. It starts the JVM and can
   run for a long time on a large program. In Claude Code, run it with
   `run_in_background`, send its output to a log file, and wait for the
   process to exit before querying.
1. Add the export directory to `.gitignore`. Exports are large and derived
   from the binary.
1. Check the result with `ghidra-bridge info` before any other query.

Export again only after the Ghidra project changes (new analysis, renamed
symbols, new types). Commands and output shapes:
[CLI card](references/ghidra-bridge-cli.md).

## Query order

Use the same order on both paths. Each step narrows the next one.

| Step | MCP tool | `ghidra-bridge` command |
| --- | --- | --- |
| 1. Orient | `list_project_binaries`, `list_project_binary_metadata` | `info` |
| 2. Search | `search_symbols_by_name`, `search_strings`, `search_code` | `search <pattern>`, `strings <pattern>` |
| 3. Decompile | `decompile_function` with one target | `decompile <addr\|name>` |
| 4. Xrefs | `list_xrefs`, `gen_callgraph` | `xrefs-to`, `xrefs-from` |
| 5. Types | none in the documented tool list | `struct`, `enum`, `vtable`, `global` |

For step 5 on the MCP path, read types from the decompiled signature or
switch to the CLI export.

## Output size

Tool output enters the context window, and one large function or a full
function list can crowd out the rest of the task.

- Search before decompiling. Decompile an exact name or address from the
  search result, not a guess.
- Decompile one function per call. `decompile_function` accepts a list,
  but a list multiplies the output; use it only for a few small functions
  that are already known.
- Keep MCP `limit` parameters small (`search_symbols_by_name` defaults to
  25, `search_strings` to 100).
- The CLI has no output-limit flags. Bound every command that can grow:
  `ghidra-bridge list | head -n 50`, `ghidra-bridge decompile X | head -n
  200`. JSON commands (`context`, `pcode`, `cfg`) print
  `{"schema_version":1,"kind",...,"data"}`; read `jq '.data | keys'` first,
  then select one key.
- Never `cat` a file from the export directory.

## Crash addresses and context bundles

A crash address from a running process is usually relocated. Subtract the
module's load base from the crash report and add the image base that
`ghidra-bridge info` or `list_project_binary_metadata` shows, then:

```bash
ghidra-bridge containing 0x00401a3c
ghidra-bridge decompile <function from the previous line> | head -n 200
```

`ghidra-bridge context <addr|name>` prints one JSON evidence bundle for a
function (callees, strings, globals, and control flow). Use it when a
question needs several of those at once, and bound it with `jq`. Details:
[crash lookup](references/ghidra-bridge-cli.md#crash-address-lookup).

## Failures

| Symptom | Cause and action |
| --- | --- |
| `Unable to lock project!` (`LockException`) | The Ghidra GUI or another process has the project open. Close it, or export from a copy of the project directory. |
| `info` shows nothing, or queries find nothing | Exports are missing or `export_dir` points elsewhere. Run `ghidra-bridge --export-dir <dir> info`; export again if empty. |
| Export or server cannot find the program | `program_name` does not match the name inside the project. List the names with `pyghidra-mcp --list-project-binaries` or the Ghidra project window. |
| JVM or Ghidra launch fails before analysis | The JDK is missing or not 21, or `GHIDRA_INSTALL_DIR` is wrong. Check `java -version` and the install path. |
| MCP search returns nothing right after start | Indexing is still running. Wait, or restart with `--wait-for-analysis`. |

More cases and checks:
[troubleshooting](references/troubleshooting.md).

## Rules

- Keep the MCP registration at project or local scope, because every
  server process holds a JVM.
- Do not run a second export or server against a project that is already
  open; the project lock makes the second one fail.
- Present decompiler output as Ghidra's reconstruction, not as the
  original source. Names such as `FUN_00401a30` and `param_1` are Ghidra's.
- Quote the address with every claim so the user can check it in Ghidra.
- For the method of reversing a function once its code is on screen
  (calling conventions, compiler idioms, type and vtable recovery), use
  `$reverse-engineer-functions`. To write source that compiles to the same
  bytes, use `$build-matching-decompilations`. For a security review of
  source code, use `$find-vulnerabilities`.

## References

- [MCP server](references/mcp-server.md): `pyghidra-mcp` registration,
  transports, analysis flags, tools, and sources.
- [ghidra-bridge CLI](references/ghidra-bridge-cli.md): install,
  `ghidra-bridge.yaml`, environment priority, export, commands, source
  mapping, crash lookup, and sources.
- [Troubleshooting](references/troubleshooting.md): project lock, missing
  exports, program names, JDK, and MCP start-up.

## Completion evidence

The answer names the program and path used (MCP or CLI), the commands or
tool calls run, the address and name of each function cited, the
decompiled lines behind each claim, and any step that could not run and
why.
