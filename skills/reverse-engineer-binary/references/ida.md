# IDA, ida-pro-mcp, and idalib

Facts read on 2026-10-05.

## Which Server

- The official Hex-Rays server is `HexRaysSA/ida-mcp` on GitHub. It needs IDA 9.4 or later with
  idalib, Python 3.11+, git, and uv. Install with `uvx ida-hcli mcp install`. For Claude Code:
  `claude plugin marketplace add HexRaysSA/claude-marketplace`, then
  `claude plugin install ida-mcp@HexRaysSA`.
- `mrexodia/ida-pro-mcp` is the community server. Its README header now says to use the official
  Hex-Rays server instead. It needs Python 3.11+, IDA 8.3+ (9 recommended), and uv. Tags 1.5.0
  (2025-11-18) and 1.4.0; PyPI had 1.4.0.
- IDA Free is not supported by either server. See the next section.

## IDA Free

- x86-32 and x86-64 disassembler only. The decompiler is cloud-only and x86 or x64 only. The local
  debugger is x86 or x64 only. Non-commercial use only. Analysis can be saved.
- No Development Kits, so no IDAPython or SDK. idalib is not in Free; it is in Classroom, Home, and
  Pro.
- With Free, use the GUI by hand or switch to Ghidra or rizin. Do not promise an MCP setup.

## ida-pro-mcp

- Recommended install for Claude Code: `claude plugin marketplace add mrexodia/claude-marketplace`,
  then `claude plugin install ida-pro-mcp@mrexodia`. For Codex:
  `codex plugin marketplace add mrexodia/codex-marketplace`, then
  `codex plugin add ida-pro-mcp@mrexodia`. The GUI-plugin path (`ida-pro-mcp --install`) is marked
  "no longer recommended".
- idalib must be activated: `uv run ".../idalib/python/py-activate-idalib.py"`, with the path under
  the IDA install.
- Headless: `uv run idalib-mcp --host 127.0.0.1 --port 8745 <exe>`, or `--stdio [--max-workers 4]`.
- Sessions: `idb_open(input_path, mode="prefer_headless"|"force_headless"|"prefer_gui"|"force_gui",
  run_auto_analysis=True, ..., preferred_session_id="")`, `idb_list`, `idb_close`, `idb_save`. Every
  tool call needs an explicit `database=<session id>`.
- Read tools: `lookup_funcs`, `int_convert` (the README says never convert bases by hand),
  `list_funcs`, `list_globals`, `imports`, `decompile`, `disasm`, `xrefs_to`, `xrefs_to_field`,
  `callees`, `analyze_funcs`, `callgraph`, `basic_blocks`, `find_regex`, `find_bytes`, `find_insns`,
  `find`, `get_bytes`, `get_int`, `get_string`, `stack_frame`, `read_struct`, `search_structs`,
  `infer_types`, `export_funcs`, `py_eval`.
- Write tools: `rename`, `set_comments`, `set_type`, `declare_type`, `declare_stack`,
  `delete_stack`, `patch_asm`, `patch`, `put_int`, `define_func`, `define_code`, `undefine`,
  `add_bookmark`. Call them only when the user asks. The `dbg_*` tools are hidden unless `?ext=dbg`
  is passed.
- Obfuscated code: the README advises removing string encryption, import hashing, control-flow
  flattening, and anti-decompilation tricks first, and using Lumina or FLIRT.

## idalib

- Needs IDA Home, Pro, or Classroom. Install with `uv pip install idapro`. For IDA 9.3 or lower run
  `py-activate-idalib.py`; hcli and the 9.4+ installer do it automatically.
- Example for IDA 9.0+: `import idapro` must come first, then
  `idapro.open_database(path, run_auto_analysis=True)`, `idaapi.auto_wait()`,
  `idautils.Functions()`, and `idaapi.get_func_name(ea)`. `idapro.enable_console_messages(True)`
  turns on console output.
- The IDA Domain API is at <https://github.com/HexRaysSA/ida-domain>.

## Binary Ninja

Community MCP servers only; no official Vector 35 MCP repository was found.

- `mrphrazer/binary-ninja-headless-mcp`: headless, 180 tools, started with `binja_cli server start`.
  It needs a headless-capable licence.
- `fosdickio/binary_ninja_mcp`: a GUI plugin. `ek0/bn-mcp` also exists.
- Check each repository's activity and licence needs before relying on one.

## Unverified

- That `idapro.close_database()` is the exact name of the close call.

## Sources

- HexRaysSA/ida-mcp: <https://github.com/HexRaysSA/ida-mcp>
- mrexodia/ida-pro-mcp: <https://github.com/mrexodia/ida-pro-mcp>
- hex-rays.com: <https://hex-rays.com/ida-free>
- docs.hex-rays.com: <https://docs.hex-rays.com/core/idalib/getting-started>
- HexRaysSA/idalib-example: <https://github.com/HexRaysSA/idalib-example>
- HexRaysSA/ida-domain: <https://github.com/HexRaysSA/ida-domain>
- mrphrazer/binary-ninja-headless-mcp: <https://github.com/mrphrazer/binary-ninja-headless-mcp>
- fosdickio/binary_ninja_mcp: <https://github.com/fosdickio/binary_ninja_mcp>
