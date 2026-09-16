# Worked examples for Build and Debug DuckStation

## Isolated launch contract

Construct a command that sets a temporary user/data directory, explicit log
level/file, selected renderer, and guest image/ELF according to current upstream
options. Print and inspect the argument vector before launching. Unknown native
options must remain explicit passthrough or produce an error; do not silently
drop them.

## Guest versus emulator evidence

A guest crash at address X can result from guest code, emulated CPU state,
incorrect patch, media image, or emulator bug. Capture build revision, game
serial/hash, settings, renderer, save state provenance, logs, guest registers,
and whether the behavior reproduces on interpreter/software renderer or a
known-good upstream build. Do not patch emulator code before locating the owning
layer.

## Evidence matrix

| Observation | Establishes | Does not establish |
| --- | --- | --- |
| command builder test passes | argument conflict/path rules | emulator launched |
| process exits normally | host process lifecycle | guest correctness |
| guest boots title screen | boot path for exact target/settings | later gameplay/render correctness |
| software renderer is correct | guest/core path under software rendering | hardware backend/driver correctness |
| save state reproduces | issue from serialized state on recorded revision | portable normal-boot reproduction |
