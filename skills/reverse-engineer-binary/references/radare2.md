# radare2, rabin2, r2pipe, and r2mcp

Facts read on 2026-10-06: radare2 6.2.4 (2026-10-05), r2ghidra 6.2.2 (2026-09-06), r2dec 6.2.0
(2026-08-16), r2mcp 1.8.8 (2026-09-06), r2pipe for Python 1.9.8. The commands below were run on
radare2 6.2.2 (macOS, Homebrew) against a static x86-64 ELF with debug info.

## Install

- Linux: the release has `.deb` packages for amd64, arm64, and i386. The README recommends a source
  build: `git clone https://github.com/radareorg/radare2` then `radare2/sys/install.sh`. Check a
  distribution package's version with `r2 -v`, because r2 plugins must match the r2 version.
- macOS: `brew install radare2`, or the release `.pkg` (`radare2-arm64-*.pkg` or
  `radare2-x64-*.pkg`). Homebrew had 6.2.2 when 6.2.4 was out.
- Windows: the release zips (`radare2-*-w64.zip`, `-w64-arm64.zip`, `-w32.zip`) hold
  `bin\radare2.exe`. A source build uses meson and MSVC: `preconfigure.bat`, `configure.bat`,
  `make.bat`.
- Plugins come from `r2pm`: `r2pm -U` updates the package list, `r2pm -ci PKG` does a clean
  install, `r2pm -l` lists installed packages. Packages install into the user's home; `-g` installs
  system-wide.

## Commands

The commands are the same on every OS. Double quotes around `-c` work in sh, PowerShell, and cmd;
single quotes do not work in cmd.

- `r2 -2 -q -e scr.color=0 -c "aaa; afl" bin` lists functions after analysis. `-2` closes stderr,
  which drops the `INFO:` analysis lines. `-q` quits after the `-c` commands. `scr.color=0` drops
  the ANSI color codes that r2 prints even into a pipe.
- `aflj` gives the function list as a JSON array, and `iIj` gives file info as JSON.
- `pdf @ sym.main` disassembles a function. With debug info, functions are named `dbg.main` and the
  `sym.main` flag still resolves.
- `axt @ sym.add` lists the callers of a function (`dbg.main 0x100123e [CALL:--x] call dbg.add`).
- `afi @ sym.add` shows function info; `afi~callconv` filters it to the calling convention line.
  `afvj @ sym.add` gives register and stack arguments as JSON. Both are r2's guesses, so check them
  against the disassembly.
- `pdc` is the built-in pseudo-C. It rewrites each instruction (`eax += dword [b]`) and does not
  recover structure, so treat it as annotated disassembly.
- `-A` runs `aaa` on load. `-AA` and `aaaa` add experimental analysis.
- `-n` skips loading binary info, for raw input. Give the load address of a flat image with `-m`
  and the architecture with `-a` and `-b`. `-B` sets the base of a PIE binary.
- `-w` opens the file for writing, so never use it on the user's file.
- Sandbox: `-e cfg.sandbox=true` blocked a `!` shell command run with `-c`; `-S` did not.
- For a Mach-O object (`.o`), r2 warns that relocations are not applied and names functions
  `fcn.ADDR`. Pass `-e bin.relocs.apply=true`, or analyze the linked binary.
- `rabin2` reads headers without analysis: `-I` info, `-z` strings from data sections, `-zz` raw
  strings, `-j` JSON (`-zj` gives `{"strings":[...]}`), `-S` sections, `-SS` segments, `-i`
  imports, `-E` exports, `-s` symbols, `-l` libraries, `-e` entrypoint, `-M` main, `-H` headers,
  `-R` relocs, `-d` debug info, `-x` extract sub-binaries.
- Bound every listing with `head -n N`, `jq`, or the r2 filter `~` (`afl~main`). In PowerShell use
  `| Select-Object -First N`.

## Decompilers

Plain r2 has no `pdg`. It prints `You need to install the plugin with r2pm -ci r2ghidra`.

- r2ghidra: `r2pm -U`, then `r2pm -ci r2ghidra`. It needs a C++ compiler and pkg-config, and it does
  not need Ghidra installed. Run `af` (or `aaa`) first, then `pdg`. Variants: `pdgj` (JSON), `pdgo`
  (with offsets), `pdga` (side by side with the disassembly), `pdg*` (as r2 comments), `pdgs`
  (Sleigh languages), `pdgss` (the matched Sleigh language ID).
- r2dec: `r2pm -i r2dec`, then `pdd`.
- Both must match the r2 version, and the disassembly wins any disagreement.

## Scripting with r2pipe

`pip install r2pipe` (MIT). The same calls work on every OS.

```python
import r2pipe

r2 = r2pipe.open("bin", flags=["-2"])
r2.cmd("aaa")
funcs = r2.cmdj("aflj")
r2.quit()
```

`cmd` returns text and `cmdj` parses JSON. This example was run with r2pipe 1.9.8.

## MCP

- `radareorg/radare2-mcp` (`r2mcp`) is the official radare2 MCP server, written in C (MIT).
  Install with `r2pm -Uci r2mcp`. Config:
  `{"mcpServers":{"radare2":{"command":"r2pm","args":["-r","r2mcp"]}}}`. HTTP mode: `r2mcp -H 8765`
  with `-a <token>` or `-A` for auth. `-R` is read-only, and it offers a sandbox and tool
  restrictions. Prefer `-R` for analysis.

## Unverified

- `r2pm` on Windows. The README documents only the `.bat` source build and the release zips.
- r2ghidra and r2dec output, because neither plugin was installed.
- `-S` may sandbox only later commands; the test above ran one `-c` command.

## Sources

- radareorg/radare2: <https://github.com/radareorg/radare2>
- radareorg/r2ghidra: <https://github.com/radareorg/r2ghidra>
- wargio/r2dec-js: <https://github.com/wargio/r2dec-js>
- radareorg/radare2-r2pipe: <https://github.com/radareorg/radare2-r2pipe>
- radareorg/radare2-mcp: <https://github.com/radareorg/radare2-mcp>
