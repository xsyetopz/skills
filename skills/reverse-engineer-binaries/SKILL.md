---
name: reverse-engineer-binaries
description: >-
  Analyzes executables, firmware, and file formats with Ghidra, recovers
  functions, types, and call graphs, and runs reagent pipelines. Use when
  there is no source code. Not for byte-matching rebuilds.
---

# Reverse Engineer Binaries

Answer questions about a compiled program from a Ghidra project, and
recover one function at a time from evidence the user can check. Without
this skill, agents dump whole decompilations into context, trust
decompiler names and prototypes, and guess through unresolved callees.

## Rules

- Work only on binaries the user may analyze: their own programs,
  interoperability, preservation, permitted security research, and
  matching-decompilation projects. Decline when the goal is to bypass a
  licence check, DRM, or anti-cheat, and say why. The tooling is the same
  either way, so the purpose decides.
- Read the disassembly before the decompiler output, and let it win a
  disagreement. The decompiler reconstructs, so a wrong prototype or type
  shows up as a mismatch between the two.
- Treat `FUN_...`, `sub_...`, `param_1`, and `undefined4` as guesses made
  by the tool. Keep them visible until evidence replaces them. A symbol,
  export, RTTI name, or string found in the binary is evidence, so cite
  where.
- Quote an address with every claim, and label anything not shown by an
  instruction as inference. One call site shows one use: write "at
  `0x...` it is called with ...", not "it always ...".
- Take the calling convention from the code, not the tool default. Look
  at which registers are read before written at entry, how callers set up
  the call, and whether `ret N` removes stack arguments. A `ret 0Ch` with
  a `__cdecl` prototype is a wrong prototype. Large return values use a
  hidden pointer that shifts the visible arguments by one.
- Strip compiler idioms before describing logic: stack cookies, inlined
  `strlen` or `memcpy` loops, jump tables, tail calls (`jmp` where
  `call` and `ret` would be), and cold blocks moved to the end. Naming
  them stops the report from describing them as the function's own work.
- Confirm a field only when every xref that touches the offset agrees on
  width and kind. List conflicts instead of averaging them. A store of a
  table address at offset 0 of a new object is a vptr, and a constant
  allocation size before a constructor call gives the object size.
- Stop at the first unresolved dependency the answer needs, such as an
  unknown indirect call, a global with no found writer, or a type the
  xrefs disagree on. List it with its address and what would resolve it.
  Guessing through it makes the rest of the report unreliable.
- Give each name you introduce a level: seen (in the binary), inferred
  (implied by use), or guess. Rename or retype in a shared project only
  when the user asks.
- Convert runtime addresses first: runtime address minus load base plus
  image base. Crash reports use relocated addresses.
- Decompile one function per call, after a search gives the exact name or
  address. Bound every CLI command that can grow with `head -n N` (PowerShell:
  `| Select-Object -First N`) or `jq`, and
  never `cat` an export file, because the output enters the context.
- Do not open a second export or server on a project that is already
  open. The project lock fails it with `Unable to lock project!`. Ask the
  user to close the GUI or export from a copy. Never delete lock files.
- Do not start Reagent for one function or one question. It is a long,
  paid batch job that sends decompiled code to a model provider, so get
  approval first.

## Workflow

1. Name the program: the Ghidra project directory, project name, and
   program name inside it.
1. Check for an MCP server with `claude mcp list` (Claude Code). Use
   `pyghidra-mcp` when it responds. Otherwise use the `ghidra-bridge` CLI.
1. Query in this order and stop when the question is answered: orient
   (`list_project_binaries` or `ghidra-bridge info`), search, decompile
   one function, xrefs, then types (`ghidra-bridge struct`, `enum`,
   `vtable`; the MCP tool list has none).
1. Report the answer with its address, the prototype with evidence for
   each argument and the return, behavior claims with addresses, field
   tables with the address of each supporting access, and open questions.

MCP registration. Each server process starts a Ghidra JVM, so register
per project, never user-wide or in a plugin:

Run this as one line:
`claude mcp add --scope local -e GHIDRA_INSTALL_DIR=<ghidra-install-dir>
pyghidra-mcp -- uvx pyghidra-mcp --project-path <project>.gpr`.

Use `--scope project` only when every path in the command is the same on
all team machines. For several
sessions at once, run one server with `--transport streamable-http` and
register its URL with `claude mcp add --transport http`. Search results
are incomplete until indexing finishes, so pass `--wait-for-analysis`
whenever an answer rests on a search finding nothing. Call editing tools
(`rename_function`, `set_comment`, `delete_project_binary`) only when the
user asks.

CLI path. `ghidra-bridge` reads an export, not a live Ghidra:

1. `uv tool install 'ghidra-ai-bridge[headless]'` (or pip inside a
   virtualenv). The `export` command needs
   PyGhidra.
1. Write `ghidra-bridge.yaml` and set `paths.export_dir` explicitly, since
   the default is `~/.ghidra-exports`, outside the project.
1. Run `ghidra-bridge export all` in the background with output to a log
   file, and wait for it to exit. It can run long on a large program.
1. Ask before adding the export directory to `.gitignore`, then run
   `ghidra-bridge info`
   before any query. Export again only after the project changes.

For a crash address, `ghidra-bridge containing <addr>` names the function,
then `ghidra-bridge decompile <name> | head -n 200`. `ghidra-bridge
context <addr|name>` prints one JSON bundle of callees, strings, globals,
and control flow; select one key with `jq` first.

Failures: `info` empty means exports are missing or `export_dir` points
elsewhere. "Program not found" means `program_name` differs from the name
in the project, so list it with `pyghidra-mcp --list-project-binaries`.
A JVM launch failure usually means a missing or wrong JDK or a bad
`GHIDRA_INSTALL_DIR`. Searches empty right after MCP start mean indexing
is still running.

## References

- Read [`references/ghidra-bridge-cli.md`](references/ghidra-bridge-cli.md)
  when using the `ghidra-bridge` CLI: configuration keys, environment
  overrides, export subcommands, query commands, and source mapping.
- Read [`references/reagent.md`](references/reagent.md) when the user asks
  to run `re-agent` on a class or many functions, or to review its output.
