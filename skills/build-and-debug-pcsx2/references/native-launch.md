# PCSX2 PS2 emulator: select boot mode and isolated data

Verify the selected binary's CLI. These command patterns correspond to the
linked v2.8.2 source anchor from the supplied material; they are not a universal
version guarantee.

```sh
# Standalone ELF with an explicit data root.
pcsx2-qt -datapath /case/data -elf /fixtures/test.elf
# ELF override with disc context available to the guest.
pcsx2-qt -datapath /case/data -elf /fixtures/test.elf -- /fixtures/game.iso
# Native guest argument string: one argument, not shell expansion.
pcsx2-qt -datapath /case/data -elf /fixtures/test.elf \
  -gameargs 'level=2 mode=test'
# Configuration check; no guest boot is implied.
pcsx2-qt -datapath /case/data -testconfig
```

Verify the effective data directory rather than assuming every file lands
directly in the `-datapath` argument. Platform/version behavior can introduce
another directory level. Inspect native logs/settings and check copied
configuration for absolute paths to ordinary memory cards and saves.

Choose explicit data-path isolation or the supported portable-mode mechanism; do
not combine them without establishing precedence. Preserve native options and
report rejected flags. A custom wrapper should not silently limit the emulator's
supported grammar.

`-nogui`/batch behavior is not a guarantee of a display/graphics-free runtime.
Check required Qt platform, GPU, audio, and first-run setup state. Keep
`-testconfig` separate from guest modes; do not add batch/no-GUI constraints
that require a boot target to a configuration-only task without verifying their
interaction.

For save-state slots/files, verify game and version compatibility and whether
the selected mode needs disc context. Do not treat loading a state as identical
to a fresh boot. Pass paths and guest arguments as separate process arguments;
do not execute a game-argument string as shell syntax.

Sources: [native CLI documentation][ref-native-cli-documentation], [v2.8.2
QtHost parser][ref-v2-8-2-qthost-parser], [v2.8.2
VMManager][ref-v2-8-2-vmmanager].

[ref-native-cli-documentation]: https://pcsx2.net/docs/advanced/cli/
[ref-v2-8-2-qthost-parser]: https://github.com/PCSX2/pcsx2/blob/v2.8.2/pcsx2-qt/QtHost.cpp
[ref-v2-8-2-vmmanager]: https://github.com/PCSX2/pcsx2/blob/v2.8.2/pcsx2/VMManager.cpp
