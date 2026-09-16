# DuckStation PS1 emulator: verify guest and graphics behavior

Distinguish a host process address from the emulated PS1 CPU address space.
Record CPU state, relevant instruction/address, memory region, guest input
identity, and the point in execution at which an observation is made. Do not
infer a guest instruction executed merely because a host debugger stepped into
an emulator function.

Use a reproducible checkpoint: boot input plus deterministic steps when
possible, or a compatible save state with identified provenance. Compare
interpreter/recompiler or renderer modes only to answer a concrete diagnostic
question; a difference narrows the cause but does not by itself identify the
defect.

For a code/memory patch, verify the game's identity, address space, value width,
timing, and native patch format for the selected version. Check whether the
guest later overwrites the target and whether recompiler/code-cache behavior
matters. Keep an unpatched baseline and prove the intended guest observation
changes. Do not turn a patch into a claim that the emulator itself is fixed.

For texture replacement/dumping, verify the effective native directory, game
identity, naming/hash convention, enabled settings, and renderer support.
Distinguish a texture asset's presence from it being selected and displayed.
Inspect the actual frame or native debug output; a copied file and successful
launch are insufficient.

A GPU dump/replay exercises rendering input, not necessarily the complete
CPU/game execution path. State exactly which layer the artifact reproduces.
Preserve renderer/backend and relevant settings in comparisons, and avoid
packaging unrelated user saves or copyrighted content into a reproducer.

Sources: [DuckStation source and
documentation][ref-duckstation-source-and-documentation], [PS1
specifications](https://psx-spx.consoledev.net/). Resolve version-specific
patch/texture behavior from the selected implementation.

[ref-duckstation-source-and-documentation]: https://github.com/stenzek/duckstation
