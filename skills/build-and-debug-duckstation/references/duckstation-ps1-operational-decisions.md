# DuckStation build and guest-diagnosis decisions

Classify the failing boundary before changing code. Use this guide for a
DuckStation build or an isolated PlayStation 1 guest investigation. Do not use
it to obtain firmware or copyrighted game content, and do not transfer commands
from another emulator.

| Observation | Next action | Do not substitute |
| --- | --- | --- |
| Failure before executable creation | Follow the revision's CMake presets/options and dependencies; capture configure and compiler output. | Do not change guest settings or BIOS. |
| Frontend starts but title fails | Isolate BIOS, legal test image, per-game settings, patches, saves, and renderer. | Do not call it a build failure. |
| Visual defect | Reproduce with the same frame/state, compare hardware and software renderers where supported, and collect a capture/log. | Do not infer guest CPU correctness from one renderer. |
| Guest-code investigation | Use the revision-supported debugger/GDB server and symbols; distinguish host and guest addresses. | Do not attach a host debugger and label host frames as guest state. |

Change one boundary at a time. A command that parses proves only command
construction. A frontend launch proves only host startup. Claim guest or
renderer behavior only after the corresponding legal input executed in an
isolated state directory.
