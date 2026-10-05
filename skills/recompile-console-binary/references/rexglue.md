# rexglue

Facts read on 2026-10-05 from the repository and its wiki. The README warns of "early development
... significant changes and breaking public API updates", so confirm every key and flag against the
version you install.

## Contents

- [Overview](#overview)
- [Config](#config)
- [Analysis Pipeline](#analysis-pipeline)
- [Overrides](#overrides)
- [Runtime and Legal](#runtime-and-legal)
- [Sources](#sources)

## Overview

`rexglue/rexglue-sdk`: "Xbox 360 Recompilation Runtime and Toolkit". The license is NOASSERTION.
Created 2026-01-22, latest release v0.10.0 (2026-08-21), last push 2026-10-02. It converts Xbox 360
PPC to portable C++23, is "heavily rooted" in Xenia, and is "inspired by XenonRecomp and rexdex's
recompiler". It is both a code generator and a Xenia-derived runtime.

CLI: `rexglue init --app_name --app_root`, `codegen`, `migrate`, and `recompile-tests`. Global flags
include `--force` and `--enable_exception_handlers`.

## Config

- Required: `project_name`, `file_path`, `out_directory_path`.
- Optional: `patch_file_path`, `patched_file_path`, `setjmp_address`, `longjmp_address`, and
  `enable_exception_handlers`. The optimization flags are the same as XenonRecomp's (`skip_lr` to
  `non_volatile_as_local`).
- `[analysis]`: `max_jump_extension`, `data_region_threshold`, `large_function_threshold`,
  `exception_handler_funcs`.
- `[functions]`, keyed by hex address, with `name`, `size`, `end`, and `parent` (`parent` chunks
  describe discontinuous bodies).
- `[[switch_tables]]` with `address` (the `bctr`), `register`, and `labels`.
- `[[invalid_instructions]]` and `[[midasm_hook]]`.

## Analysis Pipeline

From the Codegen-Pipeline-Overview wiki page, seven stages: Register (imports, helper signatures,
PDATA, config), Scan (code and data regions), Discover (iterative, with jump-table detection and an
RTTI vtable scan), GapFill, Discover again, Merge, and Validate.

- Jump-table patterns detected: `lwzx`, `lbzx`, `lhzx`, and `rlwinm` plus `lbzx`.
- Functions from the config have "CONFIG authority" and cannot be overridden. GAP_FILL functions are
  "speculative".
- Data-as-code defenses: `data_region_threshold` and `[[invalid_instructions]]`.

## Overrides

- `REX_HOOK(sub_82003A40, MyAdd)` replaces a function. `REX_HOOK_RAW(name)` gives access to the
  original through `__imp__name`.
- Stubs (logging no-ops) and mid-asm hooks are also available.

## Runtime and Legal

- A 4 GB guest address space, kernel objects, a VFS (`game:`, `d:`, `update:`), and pluggable
  graphics, audio, and input backends (the wiki calls these in flux).
- The disclaimer says it is not affiliated with Microsoft and "not intended to promote piracy".
- Its CONTRIBUTING AI stance was not found. Check it before drafting any contribution.

## Sources

- <https://github.com/rexglue/rexglue-sdk> (`README.md`)
- <https://github.com/rexglue/rexglue-sdk/wiki> (Codegen-Pipeline-Overview and the config pages)
