# Verify DuckStation build and guest claims

| Claim | Required evidence | Not sufficient |
| --- | --- | --- |
| Source builds | Revision-pinned configure/build command, toolchain/dependencies, build type, and produced binary identity. | A nearby release binary starts. |
| Frontend launches | Isolated data/settings path, process result, log, and no mutation of ordinary user state. | Help text or constructed argv. |
| Guest boots | Legal test input, required firmware provenance, effective settings, and observed guest milestone. | Frontend window or image metadata. |
| Renderer defect reproduces | Same guest state/frame, backend/driver/settings, log plus capture or dump, and a discriminating comparison. | One screenshot without configuration. |
| Patch/texture works | Parsed artifact plus load log and changed guest/rendered behavior at the intended condition. | Generated syntax or files on disk. |

Retain exact DuckStation revision and build type; isolated data directory; legal
test-image identity; BIOS region/hash record where policy permits; effective
per-game settings; renderer/backend/driver; logs, capture or guest debugger
state; clean-state reproduction. Report host-only, parser-only, guest, renderer,
and unexecuted evidence separately. If the environment lacks a supported GPU,
firmware, legal input, or host UI, state that boundary; do not promote a build
or parser result into guest verification.
