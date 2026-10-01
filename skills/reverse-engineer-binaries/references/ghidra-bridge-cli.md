# ghidra-bridge CLI

Commands are POSIX sh; on Windows run them in Git Bash or WSL. In PowerShell, replace `| head -n N`
with `| Select-Object -First N` and `tail -n N FILE` with `Get-Content FILE -Tail N`.

## Contents

- [What it is](#what-it-is)
- [Install](#install)
- [Configuration](#configuration)
- [Export](#export)
- [Commands](#commands)
- [Source-to-address mapping](#source-to-address-mapping)
- [Crash-address lookup](#crash-address-lookup)
- [Sources](#sources)

## What it is

`ghidra-bridge` is the console script of the PyPI package `ghidra-ai-bridge` (MIT, Python 3.10 or
newer; version 0.2.0 when this card was written). It exports data from a Ghidra project once,
through PyGhidra, and then answers queries from those exported files. It is not an MCP server and
does not talk to a running Ghidra. Queries reflect the project as it was at the last export.

## Install

```bash
uv tool install 'ghidra-ai-bridge[headless]'
```

The `headless` extra installs `pyghidra`, which `export` and `dump-asm` need. Without the extra,
only queries over existing exports work. Any PyPI CLI installer, such as `pip` in a virtualenv, also
works; the upstream README documents only `pip`.

Ghidra and a JDK are user installs. Ghidra 12.1.4 requires a 64-bit JDK 21; PyGhidra needs Python
3.9 to 3.14. For another Ghidra version, read that release's installation guide.

## Configuration

`ghidra-bridge.yaml` is read from the current directory, then from `~/.config/ghidra-bridge/`.
`ghidra-bridge init` writes one interactively.

```yaml
ghidra:
  install_dir: /opt/ghidra_12.1.4_PUBLIC
  project_dir: ~/ghidra-projects
  project_name: firmware
  program_name: firmware.bin

paths:
  export_dir: .ghidra-exports
  address_map: .ghidra-exports/address_map.json

binary:                     # optional
  code_range_min: 0x08000000
  code_range_max: 0x08100000
```

| Key | Meaning |
| --- | --- |
| `ghidra.install_dir` | Ghidra installation directory |
| `ghidra.project_dir` | Directory that holds the `.gpr` file |
| `ghidra.project_name` | Project name (the `.gpr` name without extension) |
| `ghidra.program_name` | Program name inside the project |
| `paths.export_dir` | Where exports go; set it, because the code default is `~/.ghidra-exports` |
| `paths.address_map` | Address map from `build-map`; default `<export_dir>/address_map.json` |
| `source.root`, `source.hook_patterns`, `source.stub_patterns` | See [source mapping](#source-to-address-mapping) |
| `binary.code_range_min`, `binary.code_range_max` | Code address range of the binary |

Priority, highest first: command-line flags, environment variables, the YAML file, defaults.
Environment variables: `GHIDRA_INSTALL_DIR`, `GHIDRA_PROJECT_DIR`, `GHIDRA_PROJECT_NAME`,
`GHIDRA_PROGRAM_NAME`, `GHIDRA_EXPORT_DIR`. Global flags: `--config`, `--export-dir`,
`--source-root`.

A stale `GHIDRA_PROGRAM_NAME` in the shell overrides the YAML file; check the environment when the
program name looks right in the file but the export opens the wrong program.

## Export

**Definition.** `ghidra-bridge export [type]` opens the project headless and writes files to the
export directory. Types: `all` (default), `structs`, `decompiled`, `vtables`, `globals`, `strings`,
`source-types`, `create-functions`, `fix-all`.

**Use when.** No export exists, or the Ghidra project changed since the last export.

**Do not use when.** The Ghidra GUI has the project open (the export fails on the project lock), or
only one kind of data changed: export that type.

The export starts a JVM and can run for a long time on a large program; measure it on your program
rather than assuming a duration. In Claude Code, run it in the background and wait for the process
to exit:

```bash
ghidra-bridge export all > ghidra-export.log 2>&1
```

Run that with `run_in_background`, then read only the end of the log
(`tail -n 20 ghidra-export.log`). Ask before adding the export directory to `.gitignore`:

```text
.ghidra-exports/
```

**Verify.** `ghidra-bridge info` prints export statistics with non-zero counts.

## Commands

| Command | Output | Bound it with |
| --- | --- | --- |
| `info` | Export statistics | small |
| `list` | Every function | `head -n 50`, or use `search` |
| `search <pattern>` | Matching function names | `head -n 50` |
| `strings <pattern>` | Matching strings and references | `head -n 50` |
| `decompile <addr\|name>` | Decompiled C for one function | `head -n 200` |
| `xrefs-to`, `xrefs-from <addr\|name>` | Callers, callees | `head -n 50` |
| `struct`, `enum <name>` | Ghidra type definition | `head -n 100` |
| `vtable <class>`, `global <addr\|name>` | Virtual table, global variable | `head -n 100` |
| `containing <addr>` | Function that contains the address | small |
| `context <addr\|name>` | JSON evidence bundle for one function | `jq` |
| `pcode`, `cfg <addr\|name>` | High P-code or control-flow graph JSON | `jq` |
| `asm <addr\|name>` | Assembly captured during the decompiled export | `head -n 200` |
| `decompile-class <class>` | Every method of a class | avoid; decompile one method |
| `unimplemented [pattern]`, `remaining [class]` | Functions not yet reimplemented in source | `head -n 50` |
| `source-struct`, `source-enum <name>` | Type from the reimplemented source | `head -n 100` |
| `dump-asm <target> <output> [--refs-out FILE]` | Assembly to a file (needs PyGhidra) | read the file with `head` |

There are no output-format or limit flags. JSON commands print one object of the form
`{"schema_version": 1, "kind": ..., "target": ..., "data": ...}`:

```bash
ghidra-bridge context FUN_00401a30 | jq '.data | keys'
ghidra-bridge context FUN_00401a30 | jq '.data.<key>' | head -n 80
```

Replace `<key>` with one key from the first command.

## Source-to-address mapping

For projects that reimplement a binary in source, `ghidra-bridge build-map` scans `source.root` with
`source.hook_patterns` (regexes that capture a function name and its original address) and
`source.stub_patterns` (regexes that find calls still going to original addresses). The defaults
match one specific project's macros, so write patterns for your own source. Example for a macro
`HOOK(Name, 0x401a30)`:

```yaml
source:
  root: ./src
  hook_patterns:
    - 'HOOK\s*\(\s*(\w+)\s*,\s*(0x[0-9A-Fa-f]+)\s*\)'
  stub_patterns:
    - 'CALL_ORIGINAL\s*<\s*(0x[0-9A-Fa-f]+)\s*>'
```

**Verify.** After `build-map`, the address map file exists and `remaining` lists only functions you
expect to be unimplemented.

## Crash-address lookup

A crash report gives an address in the running process. When the module was loaded at a different
base than Ghidra's image base (address space layout randomization, a relocated DLL), convert it
first:

```text
ghidra_address = crash_address - module_load_base + ghidra_image_base
```

Then find and read the function:

```bash
ghidra-bridge containing 0x00401a3c
ghidra-bridge decompile 0x00401a30 | head -n 200
ghidra-bridge asm 0x00401a30 | head -n 200
```

Use `asm` to locate the exact instruction at the crash offset, because one decompiled line can cover
several instructions.

## Sources

- ghidra-bridge README (install, configuration, environment variables, priority, commands):
  <https://github.com/Dryxio/ghidra-bridge>
- ghidra-bridge source (`pyproject.toml`, CLI subcommands, config defaults):
  <https://github.com/Dryxio/ghidra-bridge>
- [Ghidra 12.1.4 installation guide][ghidra-install] (JDK 21, PyGhidra Python versions).

[ghidra-install]: https://github.com/NationalSecurityAgency/ghidra/blob/Ghidra_12.1.4_build/GhidraDocs/InstallationGuide.md
