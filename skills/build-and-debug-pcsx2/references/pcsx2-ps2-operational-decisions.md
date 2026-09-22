# PCSX2 build and guest-diagnosis decisions

Classify the failing boundary before changing code. Use this guide for a PCSX2
build or an isolated PlayStation 2 guest investigation. Do not use it to obtain
firmware or copyrighted game content, and do not transfer commands from another
emulator.

| Observation | Next action | Do not substitute |
| --- | --- | --- |
| Failure before executable creation | Follow the revision's CMake options, Qt/dependency requirements, and CI build configuration; capture configure and compiler output. | Do not change guest VM settings. |
| ELF/disc boot failure | Separate BIOS/region, ELF loader, disc image, per-game settings, and patch state. | Do not call it a GS renderer failure. |
| Rendering mismatch | Reproduce with the same VM state; use GS dumps/GSRunner and compare supported renderers. | Do not infer EE/VU correctness from one screenshot. |
| Guest-code investigation | Use the PCSX2 debugger and symbols; distinguish EE/IOP/VU/GS state and host frames. | Do not transfer DuckStation options or PS1 address assumptions. |

Change one boundary at a time. A command that parses proves only command
construction. A frontend launch proves only host startup. Claim guest or
renderer behavior only after the corresponding legal input executed in an
isolated state directory.
