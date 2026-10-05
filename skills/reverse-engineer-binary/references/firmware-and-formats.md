# Firmware and File Formats

Facts read on 2026-10-05.

## Unpacking

binwalk v3 (Rust). The latest release was v3.1.0 (2024-10-31); master's `Cargo.toml` says 3.1.1.
Install with Docker, `cargo install binwalk`, or a source build. Do not `pip install binwalk`: the
PyPI package is the stale 2.1.0 (2015).

- `binwalk fw.bin` scans. `binwalk -eM fw.bin` extracts recursively.
- Flags from `src/cliparser.rs`: `-L/--list`, `-s/--stdin`, `-q`, `-v`, `-e/--extract`,
  `-c/--carve`, `-M/--matryoshka` (recursive), `-a/--search-all`, `-E/--entropy` (conflicts with
  `-e`), `-p/--png`, `-l/--log` (`-` for stdout, JSON), `-t/--threads`, `-x/--exclude`,
  `-y/--include`, `-d/--directory` (default `extractions`).

unblob (release 26.6.4, 2026-06-04; Python 3.10+; 78+ formats; runs unprivileged).

- Install `pip install unblob` plus the extractor tools. `unblob --show-external-dependencies`
  checks them. SquashFS needs sasquatch. Docker image: `ghcr.io/onekey-sec/unblob:latest`.
- `unblob fw.bin` writes to `<file>_extract/`. Options: `-e DIR`, `--report report.json`, `-d N`
  (depth, default 10), `-n N` (entropy), `--skip-magic`, `-P ./plugins`.

Extract into a scratch directory, never beside the original, and list the output with `head -n N`.

## Load Base Address

A flat firmware image has no headers, so the loader needs a base address and the processor ID.

- `sgayou/rbasefind` (Rust; last push 2020-09-27; no release): `rbasefind [-b big-endian] [-p
  progress] [-n maxmatches] [-m minstrlen] [-o offset step] [-t threads] <INPUT>`. It intersects
  ASCII-string offsets with 32-bit pointers on a flat 32-bit image. The author says it works "rather
  well on some ARM (non-thumb) binaries". Forks: `soyersoyer/basefind2` and
  `Cossack9989/uni-rbasefind` (both 2022). The lineage goes back to `mncoppola`'s `basefind.py`.
- Treat its output as a candidate list. Confirm a base by checking that pointer tables and string
  references in the disassembly land on real strings and code.
- Pass the result to Ghidra with `-loader BinaryLoader -loader-baseAddr <hex> -processor <id>`. See
  [`ghidra-headless.md`](ghidra-headless.md).

## Peripheral Maps

`leveldown-security/SVD-Loader-Ghidra` (last push 2024-02-01) labels memory-mapped peripherals from
a CMSIS-SVD file. It is a Jython script for the GUI Script Manager, and Ghidra 12.x ships Jython
only as an optional extension, so install that first. Two forks exist that were not examined:
`b1n4ri0/SVD-Loader-PyGhidra-RP2350` (a PyGhidra port, 2026-01-31) and
`veronicakovah/SVD-Loader-Ghidra` (2026-05-11). SVD files come from `posborne/cmsis-svd` or vendor
and Keil packs. Blog: <https://leveldown.de/blog/svd-loader/>.

## Format Parsers

Kaitai Struct: compiler `ksc` 0.11 (2025-09-07). Install the visualizer with
`gem install kaitai-struct-visualizer`.

- `ksv <file> <fmt.ksy>` is an interactive TUI, so agents should not use it.
- `ksdump -f json <file> <fmt.ksy>` is non-interactive (default yaml, also xml). Docker image
  `kaitai/ksv` needs `--entrypoint ksdump`.

ImHex v1.38.1 (2025-12-21). Patterns (`.hexpat`) are in `WerWolv/ImHex-Patterns`.

- Headless: `plcli` from `WerWolv/PatternLanguage`:
  `plcli run -p <pat.hexpat> -i <file> [-I incs] [-b base] [-D define] [-v] [-d]`. Other
  subcommands: `format`, `docs`, `info`.
- The GUI takes `imhex --pattern <file or source>`.

010 Editor is commercial and uses `.bt` templates. Its command-line page confirms that `-template`
and `-noui` exist.

## Unverified

- The Cortex-M heuristic that word 0 of the image is the initial stack pointer, word 1 is the reset
  vector, and an odd reset value means Thumb. It is general knowledge, not checked against a primary
  source.
- Whether ImHex's built-in MCP server code (tools such as `execute_pattern_code` and `read_data`) is
  in a release. It was seen on master only.
- The exact `010editor` invocations (`-template:t.bt`, `-noui -script:<x.1sc>`), seen only in a
  search summary.

## Sources

- ReFirmLabs/binwalk: <https://github.com/ReFirmLabs/binwalk>
- onekey-sec/unblob: <https://github.com/onekey-sec/unblob>
- sgayou/rbasefind: <https://github.com/sgayou/rbasefind>
- leveldown-security/SVD-Loader-Ghidra: <https://github.com/leveldown-security/SVD-Loader-Ghidra>
- posborne/cmsis-svd: <https://github.com/posborne/cmsis-svd>
- kaitai-io/kaitai_struct_visualizer: <https://github.com/kaitai-io/kaitai_struct_visualizer>
- WerWolv/ImHex-Patterns: <https://github.com/WerWolv/ImHex-Patterns>
- WerWolv/PatternLanguage: <https://github.com/WerWolv/PatternLanguage>
- sweetscape.com: <https://sweetscape.com/010editor/manual/CommandLine.htm>
