# Logging and debugging an official release

Cards for collecting evidence from a running release: DuckStation's own
log, its guest debuggers, and host tools (lldb, macOS crash reports) for
crashes of the emulator process itself. Observations come from release
`v0.1-11826` on macOS 27 arm64 with lldb 21.0.0.

## Contents

- Log to file
- Console logging and early console
- CPU debugger window
- GDB server
- lldb attach to a running release
- lldb launch of a release
- macOS crash report

## Log to file

**Definition.** With `[Logging] LogToFile = true`, DuckStation writes
`duckstation.log` in the user directory. `LogLevel` sets verbosity
(default `Info`; the [wiki][wiki-log] asks for `Debug` in bug reports).
Each `[Logging]` category key (`CPU`, `GPU`, `CDROM`, `BIOS`, `TTY`,
`GDBServer`, and 63 more) is a boolean filter, default `true`.
`LogTimestamps` and `LogFileTimestamps` add times.

**Use when.**

- Any run whose outcome you will report: the log holds the checkpoint
  evidence (`I/Core: Version: ...`, `I/System: Boot Path: ...`).

**Do not use when.**

- Timing or performance is under test: the wiki asks users to turn
  logging off afterwards "to reduce disk wear and restore full
  performance".

**Example.**

```sh
M="$CASE/DuckStation.app/Contents/MacOS"
sed -i '' -e 's/^LogToFile = false/LogToFile = true/' \
  -e 's/^LogLevel = Info/LogLevel = Debug/' "$M/settings.ini"
# ...bounded run...
grep -m1 'I/Core: Version:' "$M/duckstation.log"
grep -E '^\[ *[0-9.]+\] (E|W)\(' "$M/duckstation.log" | head
```

Observed lines (`LogLevel = Debug`, no BIOS present):

```text
[    0.4306] I/Core: DuckStation for macOS (arm64)
[    0.4306] I/Core: Version: 0.1-11826-gfe2306b1f [dev]
[    0.4307] I/System: Boot Path: /.../not-an-exe.exe
[    0.4308] I/System: EXE/PSF Region: Other
[    0.4325] I/System: No game settings found (tried
             'HASH-6C16B2EABF1E2FD.ini')
[    0.4327] I/BIOS: Searching for a NTSC-U BIOS in '/.../MacOS/bios'...
[    0.4338] E(CancelRequestsForOwner): Request for
             'https://api.github.com/repos/stenzek/duckstation/tags'
             cancelled
```

(Two lines wrapped here for width.) Observed prefixes: `I/`, `D/`, `V/`,
and `E(function)` / `W(function)` for errors and warnings. The
`api.github.com` request shows that the release contacts GitHub at
startup. In later runs the `Boot Path` and `BIOS` lines were absent
within 12 s, so a missing line does not prove that boot failed.

**Cost removed.** Unsupported "it booted" or "it hung" claims. Observable:
`duckstation.log` exists and contains the version line of the binary
under test.

**Verify.**

1. `grep -c 'I/Core: Version: 0.1-11826' duckstation.log` prints 1 per
   launch.
1. Tier: Executed (`assets/examples/verify.sh release`).

## Console logging and early console

**Definition.** `[Logging] LogToConsole = true` writes log lines to the
terminal with ANSI colors; `-earlyconsole` "Creates console as early as
possible, for logging" (help text). The wiki pairs "Log To System
Console" with "Log To File" for bug reports.

**Use when.**

- The process dies before `duckstation.log` gets its first line: the
  console showed startup lines (`I/MemMap: Allocated JIT buffer ...`,
  `I/Bus: Fastmem base: 0x7000000000`) that the file log did not.

**Do not use when.**

- You parse the output without stripping ANSI escapes first. On macOS,
  info lines went to stdout and `E(...)`/`W(...)` lines to stderr.

**Example.**

```sh
sed -i '' 's/^LogToConsole = false/LogToConsole = true/' "$M/settings.ini"
"$M/DuckStation" -earlyconsole -batch -nogui -- "$CASE/dummy.exe" \
  >console.out 2>console.err & PID=$!
sleep 8; kill "$PID"; sleep 2; kill -9 "$PID" 2>/dev/null || true
sed 's/\x1b\[[0-9;]*m//g' console.out | grep -m3 'I/Core'
```

**Cost removed.** Blind spots before file logging starts. Observable:
`console.out` has lines with timestamps earlier than the first line of
`duckstation.log`.

**Verify.**

1. `grep -c 'Fastmem base' console.out` is 1 (Executed without
   `-earlyconsole`; the flag's effect was not compared here).

## CPU debugger window

**Definition.** The Qt frontend has an integrated guest CPU debugger
("Integrated and remote debugging", [README][readme]). Release notes date
its features: debugger button in the toolbar
(`v0.1-11391`), VRAM and SPU VRAM in the memory editor (`v0.1-11295`),
"Patch Instruction" and "Nop Instruction" (`v0.1-11515`), cop0 breakpoint
fixes (`v0.1-10570`); call stack, threads view, and breakpoints saved to
ini files arrived after `v0.1-11826` (in the `latest` release of
2026-09-12).

**Use when.**

- Stepping guest MIPS code, setting execution breakpoints, or inspecting
  guest RAM while a game or homebrew program runs.

**Do not use when.**

- The emulator process itself crashed: that is host code; use lldb.
- You need a feature newer than the release under test (for example the
  call stack in 0.1-11826): check the release notes first.
- You would patch instructions and then report guest behavior: the patch
  changes the experiment, so restart from a cold boot.

**Example.** Procedure (UI; Not runnable here: needs a booted system,
which needs a BIOS):

```text
1. Boot the homebrew EXE in the portable copy; pause (Space).
2. Toolbar: Debugger. Note PC and the disassembly line.
3. Set a breakpoint on the address of interest; resume.
4. On hit: record PC, registers, and the memory bytes you rely on.
5. Close the debugger; power off; relaunch cold before any claim.
```

**Cost removed.** Guessing guest control flow from symptoms. Observable:
a recorded PC and register set at the breakpoint.

**Verify.**

1. The breakpoint hits at the same PC on two cold boots.
1. Tier: Not runnable here (no BIOS may be used in this session).

## GDB server

**Definition.** DuckStation can serve the GDB remote protocol for the
guest CPU. Keys: `[Debug] EnableGDBServer` (default `false`) and
`GDBServerPort` (default `2345`), observed in 0.1-11826 `settings.ini`.
Release `v0.1-11752` notes list 25 `GDBServer:` changes, including
watchpoints, single-step and continue addresses, target memory map and
registers, and GTE registers. Observed: with the key on and no system
running (BIOS missing), nothing listened on the port.

**Use when.**

- Scripted guest debugging with symbols from your own homebrew ELF.

**Do not use when.**

- No guest is running: the port stays closed (observed).
- Your GDB lacks MIPS support: host `lldb` and a native `gdb` cannot
  debug the guest. No MIPS GDB was installed here.

**Example.**

```ini
[Debug]
EnableGDBServer = true
GDBServerPort = 2345
```

```sh
lsof -nP -iTCP:2345 -sTCP:LISTEN     # must list DuckStation first
gdb-multiarch ./homebrew/hello.elf \
  -ex 'target remote 127.0.0.1:2345' \
  -ex 'info registers' -ex 'x/4i $pc'
```

User docs cover neither the bind address nor the `gdb-multiarch`
behavior: connect from the same host and confirm with `lsof`.

**Cost removed.** Manual stepping in the UI for repeatable guest checks.
Observable: `info registers` prints guest registers.

**Verify.**

1. `lsof` lists a listener on the port while the guest runs.
1. Tier: settings keys and "no listener without a system" Executed;
   client session Not runnable here.

## lldb attach to a running release

**Definition.** Attach the host debugger to the emulator process to see
host threads and stacks when DuckStation itself hangs or deadlocks. The
0.1-11826 macOS binary is ad-hoc signed, and lldb 21 attached without
extra entitlements.

**Use when.**

- The process hangs, spins, or ignores SIGTERM.

**Do not use when.**

- You want guest state: host frames are emulator code, not the game.
- The process is the user's own DuckStation (on this machine
  `/Applications/DuckStation.app` was running); attach only to your PID.

**Example.**

```sh
lldb --batch -p "$PID" -o 'thread list' -o 'bt all' -o 'detach' \
  > lldb-attach.txt 2>&1
grep -E "name = '(CoreThread|TaskQueue Worker)'" lldb-attach.txt
```

Observed with no BIOS: 14 threads, including `CoreThread` (in `poll`),
`TaskQueue Worker`, `HTTPDownloaderCurl Worker Thread`, and
`com.apple.NSEventThread`; the main thread was in `QCoreApplication::exec`
called from `DuckStation`main`.

**Cost removed.** Guessing why a process hangs. Observable: `bt all`
output with named threads.

**Verify.**

1. `grep -q 'DuckStation`main' lldb-attach.txt` succeeds (verify.sh).
1. `kill -0 "$PID"` still succeeds after `detach`.

## lldb launch of a release

**Definition.** Start the release under lldb so the first host crash
stops in the debugger with the faulting stack.

**Use when.**

- A crash reproduces within one launch and you need registers or locals
  at the fault.

**Do not use when.**

- The first stop is `EXC_BAD_ACCESS` inside JIT code: the release uses
  fastmem (console line `Fastmem base: 0x7000000000`) and the
  `v0.1-11826` notes list macOS arm64 page-fault handler changes, so
  DuckStation may handle such faults itself (inference). Continue once,
  or ignore the exception as below.

**Example.**

```sh
IGN='settings set platform.plugin.darwin.ignored-exceptions EXC_BAD_ACCESS'
lldb -o "$IGN" -o run -k 'bt all' -- \
  "$M/DuckStation" -batch -nogui -- ./homebrew/hello.exe
```

`platform.plugin.darwin.ignored-exceptions` exists in lldb 21
(`settings show` printed it). It also skips a genuine segfault; drop it
once you know the fault is real.

**Cost removed.** Crash stacks lost when the process exits. Observable:
lldb prints the stop reason and `bt all`.

**Verify.**

1. The stop reason repeats on a second launch.
1. Tier: Not runnable here (needs a booted guest).

## macOS crash report

**Definition.** When a macOS process crashes, the system writes
`~/Library/Logs/DiagnosticReports/<name>-<date>.ips`: one JSON header
line, then a JSON body with the exception, the faulting thread, and
symbolicated frames ([Apple: diagnosing issues using crash
reports][apple-crash]).

**Use when.**

- The emulator process died with a signal (exit status 134 = SIGABRT,
  139 = SIGSEGV) during an unattended run.

**Do not use when.**

- The guest crashed or hung while the process stayed alive: macOS writes
  no report, so use the DuckStation log and debugger.

**Example.** Observed on a first run in a fresh portable copy:
exit status 134 and `DuckStation-2026-09-25-192835.ips`.

```sh
F=$(ls -t ~/Library/Logs/DiagnosticReports/DuckStation-*.ips | head -1)
python3 - "$F" <<'EOF'
import json, sys
header, body = open(sys.argv[1]).read().split("\n", 1)
report = json.loads(body)
print(json.loads(header)["app_version"], report["exception"]["signal"])
thread = report["threads"][report["faultingThread"]]
for frame in thread["frames"][:16]:
    image = report["usedImages"][frame["imageIndex"]]
    print(image.get("name"), frame.get("symbol"))
EOF
```

Output, abridged: `0.1-11826-gfe2306b1f SIGABRT`, then
`std::__1::mutex::lock()` throwing `system_error`, called from
`INISettingsInterface::Save` in `INISettingsInterface::~INISettingsInterface`
in `Core::(anonymous namespace)::CoreLocals::~CoreLocals` during `exit`:
a host crash at shutdown, unrelated to guest code, on 1 of 4 fresh-copy
first runs.

**Cost removed.** Re-running to "catch" a crash that already left a
report. Observable: the report's `app_version` and symbolicated frames.

**Verify.**

1. `app_version` equals the tested version string.
1. The report time matches the run (`ls -lT`).

[wiki-log]: https://github.com/stenzek/duckstation/wiki/Enabling-Logging
[readme]: https://github.com/stenzek/duckstation/blob/master/README.md
[apple-crash]:
https://developer.apple.com/documentation/xcode/diagnosing-issues-using-crash-reports-and-device-logs
