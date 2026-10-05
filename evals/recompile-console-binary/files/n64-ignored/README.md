# N64 Ignored Fixture

`config.toml` drives N64Recomp for a homebrew ROM through `symbols.toml`. The build fails to link
because the recompiler turned the data symbol `D_80041F10` into a function: the symbols file lists
it with a size, but it holds a lookup table, not code. Its bytes are not valid instructions.

`generated/` is recompiler output and is regenerated on every run.
