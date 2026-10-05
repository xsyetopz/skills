# rizin and rz-ghidra

Facts read on 2026-10-05: Rizin v0.9.1 (2026-06-29), rz-ghidra v0.9.0 (2026-06-21), Cutter v2.5.0
(2026-06-30). The commands below were run on Rizin 0.9.1.

## Commands

- `rizin -q -c 'aaa; afl' bin` lists functions after analysis.
- `rizin -q -c 'aaa; aflj' bin` gives the same list as a JSON array.
- `rizin -q -c 'iIj; izj' bin` gives file info and strings as JSON.
- `rizin -q -c 'aaa; pdf @ main' bin` disassembles `main`.
- Warnings go to stderr, and `-2` closes stderr.
- `rizin -h` flags: `-q`, `-c`, `-i file`, `-A` (runs `aaa`), `-a arch`, `-b bits`, `-B baddr`,
  `-e k=v`, `-N`, `-w` (write mode, so avoid it on the user's file).
- `rz-bin` flags: `-I` info, `-z` strings from data sections, `-zz` raw strings, `-zzz` dump, `-j`
  JSON (`-zj` gives `{"strings":[...]}`), `-q`, `-S` sections, `-i` imports, `-E` exports, `-s`
  symbols, `-l` libraries, `-e` entrypoint, `-M` main, `-H` headers, `-c` classes, `-R` relocs, `-x`
  extract, `-A` sub-binaries, `-N min:max`.
- Pipe every listing through `head -n N` or `jq`, as with any other tool.

## rz-ghidra

Plain rizin has no `pdg`: it prints `ERROR: Command 'pdg' does not exist.` The decompiler comes from
rz-ghidra, which is LGPLv3 and does not need Ghidra installed.

- Commands: `pdg`, `pdgd`, `pdgx`, `pdgj` (JSON), `pdgo`, `pdgs` (Sleigh languages), `pdg*`.
- Config: `ghidra.lang` and `ghidra.sleighhome`. `e ghidra.lang=...` overrides Sleigh detection.
- Build: `cmake -DCMAKE_INSTALL_PREFIX=~/.local ..`, then `make && make install`. The install step
  is needed because it installs the Sleigh files.
- Its version must match Rizin. The release asset is only a source tarball
  (`rz-ghidra-src-v0.9.0.tar.gz`), and there is no Homebrew `rz-ghidra` formula. The Homebrew
  `cutter` formula was renamed `cutter-cli`.
- The Ghidra decompiler can disagree with the disassembly, so the usual rule applies: the
  disassembly wins.

## MCP

- `r2mcp` is for radare2, not rizin; see `radare2.md`.
- No official Rizin MCP was found. `kd992102/rizin-mcp` (rizin plus capa rules) is community-made
  and small (3 stars, pushed 2026-08-12).

## Unverified

- `rz-pm -ci rz-ghidra` (the README mentions an rz-pm package, but `rz-pm` was not installed).
- Kali's `apt install rz-ghidra`, seen only in a search result.

## Sources

- rizinorg/rizin: <https://github.com/rizinorg/rizin>
- rizinorg/rz-ghidra: <https://github.com/rizinorg/rz-ghidra>
- rizinorg/rz-pm: <https://github.com/rizinorg/rz-pm>
- kd992102/rizin-mcp: <https://github.com/kd992102/rizin-mcp>
