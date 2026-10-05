# PPSSPP Debugging

Checked against PPSSPP `v1.20.4` (`fa50bb19`). No GDB stub was found in `Core/Debugger/`. Use the
built-in debuggers or the WebSocket remote debugger.

## Contents

- [Launch and Logging](#launch-and-logging)
- [Built-in Debuggers](#built-in-debuggers)
- [Remote Debugger](#remote-debugger)
- [Breakpoints](#breakpoints)
- [Symbols and Addresses](#symbols-and-addresses)

## Launch and Logging

- Flags ([`UI/NativeApp.cpp`][native-app]): `--log=FILE`, `--loglevel=N`, `--state=FILE`,
  `--escape-exit`, `--pause-menu-exit`, `--fullscreen`, `--windowed`, `--root=`,
  `--gamesettings`, `--developertools`, `--appendconfig=INI`. Windows adds `--config` and
  `--controlconfig`. The list is not complete. No flag opens a debugger.
- HLE calls log on the `HLE` channel, which shows the guest's OS calls and their errors.

## Built-in Debuggers

- Windows: Debug > Disassembly (Ctrl+D), Memory View, GE Debugger, Log Console, Load/Save Map
  File, and `.sym` load and save. The docs say the Qt debugger is broken and SDL and mobile builds
  have no native debugger.
- ImDebugger (Dear ImGui): toggle with F12 (`Toggle Debugger`) or Debugger in the developer menu.
  It has CPU, registers, callstacks, breakpoints, watch, JIT viewer, memory, HLE, and graphics
  windows. Whether every platform build includes it was not confirmed.

## Remote Debugger

- Turn on Settings > Tools > Developer tools > "Allow remote debugger" (`RemoteDebuggerOnStartup`).
  The port is `RemoteISOPort`, default `0`, so the OS picks it. Read the INFO line "Entering web
  server loop. Listening on port N" from the log.
- The handler is at `/debugger` on that port (so `ws://127.0.0.1:N/debugger`), with sub-protocol
  `debugger.ppsspp.org`. Send a `version` event first. Messages are JSON `{"event": "NAME", ...}`
  with an optional `ticket` that the reply echoes. Errors come back as `{"event": "error", ...}`.
- Useful events: `cpu.stepping`, `cpu.resume`, `cpu.status`, `cpu.getAllRegs`, `cpu.stepInto`,
  `cpu.stepOver`, `cpu.stepOut`, `cpu.evaluate`, `memory.read` (base64 reply), `memory.write`,
  `memory.disasm`, `hle.backtrace`, `hle.thread.list`, `game.reset` (with `"break": true` to stop at
  start, then `cpu.resume`), `game.status`.

## Breakpoints

- `cpu.breakpoint.add`: `address`, optional `enabled`, `log`, `condition`, and `logFormat` with
  `{expression}` parts. It replaces a breakpoint at the same address.
- `memory.breakpoint.add`: `address`, `size`, `read`, `write`, `change` (only writes that change
  data), plus `enabled`, `log`, `condition`, `logFormat`.
- A log-only breakpoint (`log` on, `enabled` off) traces without stopping.

## Symbols and Addresses

- On game start, a build with a native debugger (only Windows was seen) loads `<game>.ppmap` or
  `<game>.map`, and `<game>.sym` (No$ format), named after the game file. ImDebugger's Symbols menu
  loads and saves `.ppmap` and No$ `.sym` files.
- User RAM starts at `0x08800000` and ends at `0x0A000000` with 32 MB (`0x0C000000` with 64 MB).
  VRAM is `0x04000000`-`0x04800000`.

[native-app]: https://github.com/hrydgard/ppsspp/blob/fa50bb19/UI/NativeApp.cpp
