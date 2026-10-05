# Dolphin Debugging

Checked against Dolphin master `0961ec1d`. Dolphin has no tagged GitHub releases, so record the
build string from Help > About.

Dolphin's [`Contributing.md`][contributing] accepts contributions only from humans and forbids LLM
use for console behavior. Debug the user's own game locally, and never draft an upstream change.

## Contents

- [Debugger UI](#debugger-ui)
- [Breakpoints](#breakpoints)
- [GDB Stub](#gdb-stub)
- [Symbols](#symbols)

## Debugger UI

- `-d` or `--debugger` shows the debugger panes. The setting is `[Interface] DebugModeEnabled`
  (Settings > Interface > Enable Debugging UI). The View menu then has Code, Registers, Threads,
  Watch, Breakpoints, Memory, Network, JIT, and Assembler widgets, and the JIT and Symbols menus
  appear.
- Other flags: `-e/--exec`, `-b/--batch`, `-l/--logger`, `-s/--save_state`, and
  `-C/--config <System>.<Section>.<Key>=<Value>` for a one-run setting override.
- The Branch Watch button in the Code widget opens the Branch Watch Tool. It records which branches
  ran, then filters by taken or not taken ("Code Path Was Taken", "Code Path Not Taken"). It finds
  the code that handles an input or event.

## Breakpoints

- The breakpoint dialog takes an instruction or a memory breakpoint (address or range; read, write,
  or both). The action is break, log, or both. A condition expression can use `r0`-`r31`,
  `f0`-`f31`, SPRs, `pc`, `msr`, and functions such as `read_u32()` and `callstack()`.
- A memory breakpoint stops before the access, not after it as in GDB.
- Any memory breakpoint makes the JIT emit checked loads and stores and removes fastmem mappings
  over the watched range, so the game runs slower. Debug mode also turns off the JIT's BLR
  optimization, and single-stepping turns off block linking. JIT > JIT Block Linking Off turns it
  off for a whole run.

## GDB Stub

- Set `[General] GDBPort` (default `-1`, off) to a port above 0, or on non-Windows hosts
  `[General] GDBSocket` to a Unix socket path. The guest starts paused and Dolphin waits in
  "Waiting for gdb to connect...".
- A TCP port binds on all interfaces. Use the Unix socket, or a firewall, on a shared network.
- Hardcore achievements mode skips the stub.
- The target is 32-bit big-endian PowerPC (750). Use a gdb built with PowerPC support (for example
  `gdb-multiarch`, not confirmed). There is no `target.xml`.
- Supported `Z` types: 0 and 1 (execute), 2 write, 3 read, 4 access. Conditions are not supported
  over GDB; use the dialog for those.

## Symbols

- Symbol maps load from `<User>/Maps/<GAMEID>.map`. The Symbols menu loads and saves maps, other
  map files, signature files, and symbols generated from RSO modules.

[contributing]: https://github.com/dolphin-emu/dolphin/blob/0961ec1d/Contributing.md
