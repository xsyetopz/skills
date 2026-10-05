# xemu Debugging

Checked against xemu `v0.8.136` (`fc24584c`) and the [guest debugging docs][guest-docs]. xemu is
built on QEMU, so guest debugging uses QEMU's gdbstub and monitor.

## Contents

- [GDB Stub](#gdb-stub)
- [Monitor and Tracing](#monitor-and-tracing)
- [Serial Output](#serial-output)

## GDB Stub

- Append `-s` to the launch command for a GDB server on `localhost:1234` (`-s` is
  `-gdb tcp::1234`). Add `-S` to freeze the CPU at startup until gdb continues or the monitor gets
  `c`. Arguments xemu does
  not know go to QEMU ([CLI docs][cli-docs]).
- Launch paths: Windows `xemu.exe`, macOS `./xemu.app/Contents/MacOS/xemu`, Linux
  `./xemu.AppImage`.
- The target is i386 (a Pentium III), so any gdb with x86 support works. IDA connects as a Remote
  GDB debugger to `localhost:1234` (the docs show IDA on Windows) and needs a memory map end
  address of `FFFFFFFE`.

## Monitor and Tracing

- Open the QEMU monitor with the backtick key or Debug > Monitor. It needs no GDB server. Use
  `info registers`, `x/20i ADDR`, and `x/100 ADDR` (100 units in the default format).
- `trace-event NAME on|off` turns a QEMU trace event on or off. Output goes to stderr, so start
  xemu from a terminal and redirect it to a file.

## Serial Output

- `-device lpc47m157 -serial stdio` (or `-serial tcp:127.0.0.1:5558`) gives the guest a serial
  port. Homebrew that prints to it gives a log line only a running guest can produce.

No patch or cheat feature was found in the xemu docs or menus. Use the monitor or gdb to change
memory while testing.

[guest-docs]: https://xemu.app/docs/dev/debug/guest/
[cli-docs]: https://xemu.app/docs/cli/
