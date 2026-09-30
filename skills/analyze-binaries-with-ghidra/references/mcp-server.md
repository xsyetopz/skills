# pyghidra-mcp MCP server

## Contents

- [What it is](#what-it-is)
- [Project-scope registration](#project-scope-registration)
- [Transport choice](#transport-choice)
- [Analysis at start-up](#analysis-at-start-up)
- [Tools](#tools)
- [Sources](#sources)

## What it is

`pyghidra-mcp` (PyPI, Apache-2.0, Python 3.10 or newer; version 0.2.7 when
this card was written) starts Ghidra through PyGhidra in its own JVM,
opens or creates a Ghidra project, and serves analysis as MCP tools. It
needs `GHIDRA_INSTALL_DIR` set to the Ghidra installation directory.

`--project-path` takes either a directory together with `--project-name`,
or an existing `.gpr` file. A missing project is created. A positional
binary path imports that binary. `--list-project-binaries` prints the
program names in the project, which is the fastest way to find the right
name.

## Project-scope registration

**Use when.** The repository is about one binary or one Ghidra project and
an agent session will query it.

**Do not use when.** The server would be registered user-wide or in a
plugin: every session then starts a Ghidra JVM, including sessions that
never analyze a binary.

Stdio, one JVM per client session:

```bash
claude mcp add --scope project -e GHIDRA_INSTALL_DIR=/opt/ghidra \
  pyghidra-mcp -- uvx pyghidra-mcp --project-path /abs/path/proj.gpr
```

`--scope project` stores the entry in `.mcp.json` at the repository root,
shared with other contributors. `--scope local` keeps it for this user in
this project only; use it when the paths are private to one machine. Check
the current syntax with `claude mcp add --help`.

**Verify.** `claude mcp list` shows `pyghidra-mcp`; in a new session,
`list_project_binaries` returns the expected program.

## Transport choice

`--transport` (short `-t`, environment `MCP_TRANSPORT`) accepts `stdio`
(default), `streamable-http`, `http`, and `sse` (deprecated).

| Situation | Transport |
| --- | --- |
| One agent session on one machine | `stdio` |
| Several clients or sessions share one Ghidra process and project | `streamable-http` |
| `--gui` (share live state with a running Ghidra GUI) | `streamable-http` (required) |
| The MCP host cannot connect to an HTTP endpoint | `stdio` |

The upstream README recommends `streamable-http` because one long-running
server keeps Ghidra and the project open. Start it once and register the
URL:

```bash
uvx pyghidra-mcp --transport streamable-http \
  --project-path /abs/path/proj.gpr
claude mcp add --scope project --transport http \
  pyghidra-mcp http://127.0.0.1:8000/mcp
```

`--host` defaults to `127.0.0.1` and `--port` to `8000`. Keep the host on
the loopback address unless the user wants the server reachable from other
machines.

## Analysis at start-up

By default (`--no-wait-for-analysis`) the server accepts requests while
Ghidra analysis and the server's own indexing continue. Decompilation,
navigation, renaming, and comments can work during that time, but
`search_strings` and `search_code` may return incomplete results.

- Keep the default when start-up time matters, for example a large project
  where only a few functions are needed.
- Pass `--wait-for-analysis` when complete search results matter more than
  start-up time.
- `--force-analysis` runs analysis again on programs that were already
  analyzed. Use it only when the user asks for re-analysis.

Ghidra analysis state and indexing state are separate: a program can be
fully analyzed while search is still waiting for the index.

## Tools

Read and analysis:

- `search_symbols_by_name(binary_name, query, functions_only, offset,
  limit=25)`: regex or plain symbol search.
- `search_strings(binary_name, query, limit=100)`.
- `search_code(binary_name, query, limit=5, ...)`: semantic or literal
  search over decompiled code; `include_full_code` defaults to true, so
  set it to false or keep `limit` small.
- `decompile_function(binary_name, name_or_address, include_callees,
  include_strings, include_xrefs, timeout_sec=30)`: one target or a list.
- `list_xrefs(binary_name, name_or_address)`: one target or a list.
- `gen_callgraph(binary_name, function_name, direction, ...)`: a Mermaid
  call graph, `calling` or `called`.
- `list_exports`, `list_imports` (regex `query`, `limit=25`),
  `read_bytes(binary_name, address, size=32)`.

Project: `import_binary`, `list_project_binaries`,
`list_project_binary_metadata` (architecture, compiler, format, hashes),
`delete_project_binary`.

Editing (change the project; only on request): `rename_function`,
`rename_variable`, `set_variable_type`, `set_function_prototype`,
`set_comment`.

GUI mode only: `list_open_programs`, `open_program_in_gui`,
`set_current_program`, `goto`.

The documented tool list has no struct, enum, or vtable reader. Read types
from decompiled signatures, or use the `ghidra-bridge` export for them.

## Sources

- `pyghidra-mcp` README (flags, transports, start-up defaults, tools,
  Claude Code configuration):
  <https://github.com/clearbluejar/pyghidra-mcp>
- PyPI package: <https://pypi.org/project/pyghidra-mcp/>
- `claude mcp add --help` for `--scope`, `--transport`, and `-e`.
