# PCSX2 PS2 emulator: verify CPU and graphics behavior

Specify whether the question concerns the Emotion Engine, IOP, GS, recompiler,
renderer, or host process. EE and IOP observations refer to distinct guest
contexts; a host pointer is not automatically a guest address. Record the
relevant CPU/register state, address/width, executable/disc identity, and
checkpoint.

For PNACH or another supported patch mechanism, verify the selected game's
identity, native patch naming/lookup, target CPU/address space, data width,
application timing, and enabled settings. Check the actual memory or guest
behavior after application. A parsed patch line does not prove the intended
address was changed at the right time; the guest may overwrite it later.

Keep an unpatched baseline and isolate the patch set. Verify whether a code
change interacts with recompiler caches or execution timing. Do not infer that a
working game patch fixes an emulator defect.

For texture dumping/replacement, verify effective directories, native
naming/hash rules, game identity, renderer support, and settings at the chosen
version. Inspect a concrete frame or native diagnostics that demonstrate
selection of the asset. Copying files into a guessed folder is not proof of use.

A GS dump and runner reproduce a graphics command stream, not necessarily full
EE/IOP gameplay. Use them for rendering/regression questions they can observe.
Record renderer/backend, resolution and relevant options; changing them
simultaneously with the emulator revision weakens attribution.

Use a compatible state or reproducible boot sequence and record its identity.
Distinguish a performance comparison from a correctness check. Do not package
user saves, memory-card contents, or guest assets unrelated to the reproducer.

Sources: [PCSX2 debugging](https://pcsx2.net/docs/), [GS dump
runner][ref-gs-dump-runner], [PCSX2 source](https://github.com/PCSX2/pcsx2).

[ref-gs-dump-runner]: https://pcsx2.net/docs/advanced/gsdumprunner/
