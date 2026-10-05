# RPCS3 Debugging

Checked against RPCS3 `v0.0.43` (`53d44aa4`).

## Contents

- [Launch and Logging](#launch-and-logging)
- [Debugger](#debugger)
- [GDB Server](#gdb-server)

## Launch and Logging

- Flags: `--no-gui`, `--decrypt`, `--installfw`, `--savestate`, `--styles`, `--stylesheet`, and
  `--qDebug` (logs Qt debug output to `RPCS3.log`). No flag opens the debugger.
- The log is `RPCS3.log` in the log directory. The settings dialog has a Log tab; per-channel level
  controls there were not confirmed.

## Debugger

- View > Show Debugger. Press F1 in the debugger for keys: Ctrl+G go to address, Ctrl+B
  breakpoint settings, Ctrl+F find thread, F10 and F11 step, Alt+S capture an SPU image, Alt+F5 the
  SPU disassembler. A combo box picks the PPU, SPU, or RSX thread. "Pause All Threads On Hit"
  chooses whether a hit pauses the whole emulator or only the thread.
- Execute breakpoints need an interpreter: `ppu_breakpoint()` refuses an address under the LLVM
  decoder, and the GUI says "Cannot set breakpoints on non-interpreter decoders." (also for SPU
  local breakpoints). Switch the PPU decoder to Interpreter (static) before setting one, and expect
  the game to run far slower.
- The GUI offers memory read, write, and read-write breakpoints. Hooks were found only on PPU paths;
  whether SPU or RSX accesses trigger them was not confirmed.

## GDB Server

- `Misc: GDB Server` in `config.yml`, default `127.0.0.1:2345`. It must be an IPv4 `a.b.c.d:port`.
  An empty value disables it ("GDB Server is disabled.").
- PPU only. The server supports software execute breakpoints (`Z0`) and no conditions, hardware
  breakpoints, or watchpoints. Under the LLVM decoder the server still answers `OK` to `Z0`, but
  no breakpoint is set, so switch to the interpreter first and confirm a hit.
- Use a gdb that supports 64-bit PowerPC (for example `gdb-multiarch`, not confirmed).
