---
name: build-and-debug-pcsx2
description: >-
  Use when building PCSX2, configuring an isolated emulator run, or debugging
  PlayStation 2 guest execution, ELF loading, PNACH patches, textures,
  rendering, or save states. Not for DuckStation or obtaining BIOS and game
  images.
---

# Build and Debug PCSX2

Build, launch, or investigate PCSX2 while keeping emulator build/configuration,
PlayStation 2 guest behavior, media/firmware provenance, rendering, patches,
saves, and host environment as separate evidence layers.

## Operating contract

- Use the exact PCSX2 revision/release and current upstream source/options. Do
  not transfer commands or configuration from the other emulator.
- Use a task-owned isolated data/config/cache/log directory for experiments.
  Preserve ordinary user saves, states, memory cards, settings, textures,
  cheats, and game lists.
- Do not obtain or redistribute BIOS, firmware, copyrighted game images, keys,
  or proprietary assets. Use only user-authorized legally available inputs.
- Separate command construction, emulator process startup, guest boot, specific
  guest behavior, renderer output, and performance. Evidence at one layer does
  not prove another.
- Treat save states as revision/settings-dependent diagnostic artifacts, not
  durable portable correctness evidence. Record provenance before use.

## Build-and-guest execution contract

- Treat the user goal, scope, approval boundary, and required evidence as
  controlling. This skill narrows how to produce a PCSX2 build or guest
  diagnosis; it MUST NOT broaden authority or override repository instructions.
- For GPT-5.6 and GPT-6, provide the PCSX2 revision, PlayStation 2 ELF or disc
  artifact, host, and isolated settings directory, hard constraints, available
  tools, and the finish condition once. Remove repeated directions and examples
  unless a recorded evaluation shows that they prevent a real failure.
- Infer routine, reversible steps from inspected evidence. Ask only when an
  unresolved choice changes an external contract. Stop before an external write,
  destructive action, credential use, or material scope expansion that the user
  did not authorize.
- Load a linked reference only when its subject affects the current decision.
  Use scripts for deterministic mechanics; use model judgment for semantic
  decisions. Inspect tool output before relying on it.
- Validate at the boundary of the claim with build logs, isolated VM runs, GS
  dumps, and state comparisons. Report commands, observed results, and gaps. A
  parser, build, or single green test proves only the property that it can
  discriminate.
- Use **MUST** only for an absolute safety or interoperability requirement,
  **SHOULD** for a default with valid exceptions, and **MAY** for an option.
  Write short active sentences and use one stable term for each concept. This
  style is STE-inspired; it is not a claim of formal ASD-STE100 conformance.

## Workflow

```mermaid
flowchart LR
    Src[PCSX2 source / release] --> Build[Host build and packaging]
    Build --> Launch[Isolated launch + native config]
    Firmware[Authorized firmware/media] --> Launch
    Launch --> Emu[Emulator core and devices]
    Emu --> Guest[PlayStation 2 guest execution]
    Emu --> Render[Renderer / audio / input]
    Patch[Patches / textures / save state] --> Guest
    Guest --> Evidence[Logs, debugger, dumps, exact reproduction]
    Render --> Evidence
```

## Procedure

1. Classify the task: source build, packaged launch, configuration, guest/ELF
   debugging, patch/texture work, rendering, save-state analysis, or upstream
   issue reproduction. Record PCSX2 revision/version, host OS/architecture, and
   authorized inputs.
1. Inspect upstream build files/docs and existing repository changes before
   selecting dependencies, generator, compiler, build type, feature flags, or
   packaging. Do not use remembered commands for a different release.
1. For experiments, create an isolated task-owned data/config/log/cache path.
   Inventory native settings and passthrough options. Use the bundled command
   builder only to construct/validate arguments; inspect the result before
   execution.
1. Establish a minimum reproduction with game/ELF/serial/hash, exact scene or
   frame, settings, renderer, patches/textures, save-state provenance, and
   expected versus actual PlayStation 2 behavior. Reproduce on the same revision
   before changing code.
1. Locate the owning layer: host build/package, configuration/paths,
   core/CPU/devices, guest program/data, patch, save state, renderer/driver,
   audio/input, or external dependency. Use logs/debugger/dumps and controlled
   A/B settings rather than broad toggles.
1. Change one causal factor and preserve a known-good comparison. For source
   fixes, add the narrowest suitable test or repeatable reproduction; for guest
   patches, record target identity and address/condition constraints. Do not
   suppress emulator errors or reset user state.
1. Re-run the exact reproduction and relevant build/core/renderer/guest checks.
   Clean task-owned state only after preserving useful evidence. Report which
   layer was executed and what remains unverified.

## Choose the emulator evidence reference

| Situation | Read or use |
| --- | --- |
| Building from source and inspecting upstream requirements | [Source builds](references/pcsx2-ps2-source-builds.md) |
| Using documented CLI options and isolated data paths | [Native launch](references/native-launch.md) |
| Building exact command lines and data paths | [Commands and data paths](references/commands-and-data-paths.md) |
| Debugging guest execution, GS dumps, rendering, and evidence | [Debugging evidence](references/pcsx2-ps2-debugging-and-evidence.md) |
| Debugger and rendering behavior | [Debugger and rendering](references/debugging-and-rendering.md) |
| PNACH patches and texture replacement | [Patches and textures](references/patches-and-textures.md) |
| Choosing build, launch, guest, renderer, or patch evidence | [Operational decisions](references/pcsx2-ps2-operational-decisions.md) |
| Using complete build/launch/debug examples | [Worked scenarios](references/pcsx2-ps2-worked-scenarios.md) |
| Matching process, guest, and renderer claims to evidence | [Verification and claim evidence](references/pcsx2-ps2-verification-and-claim-evidence.md) |
| Avoiding user-state damage and layer conflation | [Failure patterns and recovery](references/pcsx2-ps2-failure-patterns-and-recovery.md) |
| Applying enterprise provenance and sandbox controls | [Organizational controls and scale](references/pcsx2-ps2-organizational-controls-and-scale.md) |
| Checking current upstream sources | [Standards, APIs, and authorities](references/pcsx2-ps2-standards-apis-and-authorities.md) |

## Emulator diagnosis references

Read only the reference whose subject affects the current task.

| Reference | Use when |
| --- | --- |
| [PCSX2 PS2 emulator: select the source-build task](references/pcsx2-ps2-build.md) | Resolve the requested source revision and read its build documentation, CMake options, dependency provisioning, and supported host/target architectures. |
| [Concepts, contracts, and invariants](references/pcsx2-ps2-concepts-contracts-and-invariants.md) | Use when distinguishing the requested PCSX2 build or guest diagnosis from observed repository state. |
| [Bundled resource map](references/pcsx2-ps2-bundled-resource-map.md) | Use when locating bundled resources for the PCSX2 build or guest diagnosis. |

## Behavioral evaluation

Run [the maintained Agent Skills evaluations](evals/evals.json) in clean
target-client contexts. Compare this revision with a no-skill or prior-skill
baseline. Review commands, diffs, and artifacts; do not grade prose alone. The
checked-in cases are test inputs, not claimed results.

## Bundled executable helpers

- `scripts/build_command.py --help`
- `scripts/test_build_command.py`

Run a helper only for the contract it documents. Inspect arguments and output; a
zero exit status proves only the checks implemented by that helper.

## Bundled output material

- No output template is mandatory. Preserve the repository's established format.

Copy or adapt assets into the target workspace. Do not edit the installed skill
as a substitute for changing the requested repository.

## Completion evidence

- Exact PCSX2 revision/release, host/toolchain, build options, and produced
  artifact when building.
- Isolated data/config/log paths and inspected native argument vector.
- Authorized firmware/media/ELF/patch/texture/save-state identities without
  redistributing them.
- Minimum reproduction with expected/actual behavior and owning-layer analysis.
- Executed host build, emulator launch, guest, renderer, debugger/dump, and
  regression checks distinguished.
- Task-owned cleanup and preserved user data/settings.

## Stop or escalate

- Required firmware/media/input is unavailable or not authorized.
- The only available experiment would overwrite user data/configuration or
  require unapproved system access.
- The exact upstream version/options cannot be established.
- A result depends on an unavailable physical GPU/driver/game scene and narrower
  evidence would be misleading if promoted.

Do not claim completion while a required check is failed, unattempted, or
unavailable. State the exact evidence and the remaining boundary instead of
promoting a narrower result into a broader claim.
