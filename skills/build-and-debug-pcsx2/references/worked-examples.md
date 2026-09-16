# Worked examples for Build and Debug PCSX2

## Isolated launch contract

Use the selected PCSX2 version’s documented CLI and a task-owned data/config
root. Resolve BIOS/media/ELF paths without copying user saves or global
settings. Construct the argument vector, verify paths and conflicts, then
launch. Report command construction separately from actual emulator/guest
execution.

## GS/rendering investigation

Capture the PCSX2 revision, game serial/CRC, GS dump or exact scene, renderer,
upscaling and hardware hacks, texture-replacement state, driver/GPU, and whether
the issue reproduces with software rendering. A successful GS dump runner check
establishes that dump path, not overall game correctness.

## Evidence matrix

| Observation | Establishes | Does not establish |
| --- | --- | --- |
| command builder test passes | argument conflict/path rules | emulator launched |
| process exits normally | host process lifecycle | guest correctness |
| guest boots title screen | boot path for exact target/settings | later gameplay/render correctness |
| software renderer is correct | guest/core path under software rendering | hardware backend/driver correctness |
| save state reproduces | issue from serialized state on recorded revision | portable normal-boot reproduction |
