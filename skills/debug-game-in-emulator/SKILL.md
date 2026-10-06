---
name: debug-game-in-emulator
description: >-
  Debugs games and homebrew in PCSX2, DuckStation, Dolphin, RPCS3, PPSSPP, and xemu
  with isolated data roots, logged bounded runs, built-in debuggers, and GDB stubs.
  Use when a game will not boot, renders wrong, or crashes, or to break on guest code.
  Not for writing cheat codes or patches.
---

# Debug Game in Emulator

Run the emulator against a throwaway data root with a file log, and decide which layer owns a
failure before changing anything. Without this, agents touch the user's real profile, report a boot
from an exit status, and attach a debugger for the wrong CPU.

## Rules

- Never download or generate a BIOS, firmware, a game image, or keys. Copy them only from files the
  user supplies and owns (for example into the throwaway data root), or use self-built homebrew.
  Without them, write "Not runnable here" for guest-level steps.
- Never run an emulator against the user's default profile. Use the isolation its reference names
  (PCSX2 `-datapath` or `portable.txt`, DuckStation `portable.txt`). Touch a stamp file first and
  run `find DIR -newer STAMP` afterwards to prove the profile is untouched. In PowerShell:
  `Get-ChildItem DIR -Recurse -File | Where-Object LastWriteTime -gt (Get-Item STAMP).LastWriteTime`
- Do not treat a green build, exit 0, or "still running" as a boot. PCSX2 and DuckStation exit 0
  after a startup error such as a missing BIOS. Quote a log line only a running guest can produce,
  or an artifact.
- Bound every unattended run with an external timeout and always write a log file. A first-run
  wizard or an error dialog hangs the run otherwise. Record a forced kill (SIGKILL, or
  `Stop-Process -Force` on Windows) as forced termination.
- Classify the failure by layer and quote the log line that proves it. The layers are configure,
  compile, package, process start, setup (wizard, BIOS, firmware), guest boot, guest behavior,
  renderer, host crash. Evidence from one layer says nothing about a later one.
- Change one variable per run (renderer, one patch, one setting, one release) and keep an unmodified
  baseline. Turn off cheats, patches, texture replacements, and enhancements before blaming the
  emulator core.
- Name the release tag or commit and its sha256 in every claim. `latest`, `preview`, and nightly
  names move. Label each flag or setting with the version it was seen in, because flags differ
  between releases and between emulators.
- Edit an emulator's settings only while it is stopped, and use only keys and values the same
  release wrote. For an unknown value, set it once in the UI and copy the changed line.
- Do not use save states across releases or as proof of a fix. They capture emulator internals and
  skip the boot path.

### Debuggers and GDB Stubs

- Debug guest code with the emulator's own debugger or GDB stub, and use host `lldb` or `gdb`
  (Windows: WinDbg or `cdb -p PID -c "~*k; qd"`) only for emulator crashes and hangs. Attach only to
  a process you started.
- Match the guest CPU before attaching. The stubs and their targets:

  | Emulator | Guest debugging |
  | --- | --- |
  | PCSX2 | Built-in debugger only, no GDB stub. |
  | DuckStation | GDB server only while a guest runs. |
  | Dolphin | `[General] GDBPort` or `GDBSocket`; 32-bit big-endian PowerPC. |
  | RPCS3 | `Misc: GDB Server`, `127.0.0.1:2345`; PPU only, `Z0` only, ignored under LLVM. |
  | PPSSPP | No stub; WebSocket debugger at `/debugger`, port from the log. |
  | xemu | QEMU `-s` (`localhost:1234`) and `-S`; i386. |

- Keep a stub on loopback or a Unix socket. Dolphin's TCP port binds on all interfaces.
- Expect a debugger to change what it observes. Memory breakpoints slow the JIT or turn off
  fastmem, RPCS3 breakpoints need an interpreter decoder, and Dolphin stops before a watched
  access, not after it.
- Confirm a breakpoint with a quoted hit (address, registers, or a log-only breakpoint line), not
  with "set successfully".

### Upstream Projects

- Never clone, read, build, modify, or package DuckStation source. Its licence (CC-BY-NC-ND-4.0
  plus a packaging restriction on build files) and its repository `CLAUDE.md` ask AI assistants not
  to. Say so, point to the upstream README and releases page, and offer to debug an official
  numbered release.
- Do not open PCSX2 PRs, issues, or comments, and do not write their text (upstream `AGENTS.md`).
- Dolphin's `Contributing.md` accepts only human contributions and forbids LLM use for console
  behavior. Debug the user's own game locally and draft no upstream change.
- RPCS3, PPSSPP, and xemu need an AI disclosure on a PR, and the human sends all communication.

## Workflow

1. Record the exact build: release tag and sha256, or `git rev-parse HEAD` of the checkout. Read
   the emulator's reference below.
1. Make a case directory and an isolated data root. PCSX2: `-datapath DIR` needs an existing `DIR`
   and writes to `DIR/PCSX2`; portable mode overrides it. DuckStation: an empty `portable.txt` next
   to the executable (`Contents/MacOS` on macOS).
1. Create the settings file with one bounded warm-up launch, then turn on file logging. PCSX2 also
   needs `SetupWizardIncomplete = false` in `inis/PCSX2.ini`. Check a DuckStation `settings.ini`
   edit with the `check_settings_keys.py` script from `$write-emulator-patches`.
1. Capture the binary's own `-help` or `--help` (DuckStation prints it to stderr and exits 1) and
   use only flags it lists.
1. Launch with a hard time limit, read the log, and name the failing layer.
1. For guest behavior, attach the emulator's debugger or stub, set one breakpoint or watchpoint,
   and quote the hit.
1. Change one variable, rerun the same oracle, and report each claim with its layer, build, and the
   quoted line.

## References

| Emulator | Reference |
| --- | --- |
| PCSX2 (PS2): build, data root, logging, debugger, renderer, bisecting | [`references/pcsx2.md`](references/pcsx2.md) |
| DuckStation (PS1): releases, portable copy, logging, lldb, textures | [`references/duckstation.md`](references/duckstation.md) |
| Dolphin (GameCube, Wii): debugger UI, breakpoints, GDB stub, symbols | [`references/dolphin.md`](references/dolphin.md) |
| RPCS3 (PS3): logging, debugger, GDB server | [`references/rpcs3.md`](references/rpcs3.md) |
| PPSSPP (PSP): logging, built-in and WebSocket debuggers | [`references/ppsspp.md`](references/ppsspp.md) |
| xemu (Xbox): GDB stub, QEMU monitor, serial output | [`references/xemu.md`](references/xemu.md) |

To write or fix a patch, cheat code, or the settings that enable one, use `$write-emulator-patches`.
