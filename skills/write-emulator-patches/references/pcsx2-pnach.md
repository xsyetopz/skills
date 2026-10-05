# PCSX2 pnach Files

Checked against PCSX2 `v2.8.2` (`fd9d310c`, [`pcsx2/Patch.cpp`][patch-cpp]) and commit `2c804670`
(`v2.9.84`). Re-check a rule against the `Patch.cpp` of the build under test.

## Contents

- [Location and Names](#location-and-names)
- [Line Grammar](#line-grammar)
- [Extended Codes](#extended-codes)
- [Dynamic Patches](#dynamic-patches)
- [Enabling and Errors](#enabling-and-errors)

## Location and Names

- Patches load from `patches/`, cheats from `cheats/` and only with Enable Cheats on, bundled ones
  from `resources/patches.zip`. A patch file on disk wins over the bundled one; cheats never come
  from the zip.
- The loader globs `SERIAL_CRC*.pnach`, then `CRC*.pnach`. The CRC is 8 hex digits, matched
  case-insensitively. Addresses and CRCs differ per region and revision, so each needs its own file.
- A `patch=` line before the first `[group]` is legacy and always on. One in `patches/` also stops
  the loader from reading `patches.zip` for that game. A `[group]` name already loaded is skipped
  ("Skipped loading patch '...' since a patch with a duplicate name was already loaded").
- Groups `Widescreen 16:9` and `No-Interlacing` apply automatically with the matching global
  settings (`EnableWideScreenPatches`, `EnableNoInterlacingPatches`).

## Line Grammar

- Comments start with `//`. Keys: `patch`, `dpatch`, `gsaspectratio`, `gsinterlacemode`, and the
  metadata keys `author`, `description`, `comment`, `gametitle`. Other keys are ignored silently.
- `patch=<place>,<cpu>,<address>,<type>,<data>`. `place` is `0` startup, `1` every vsync, `2` both,
  `3` startup and when enabled in the UI. `cpu` is `EE` or `IOP`, case-sensitive. `address` is at
  most 8 hex digits with no `0x`. `type` is lowercase: `byte`, `short`, `word`, `double`,
  `extended`, `beshort`, `beword`, `bedouble`, `bytes`. `data` is bare hex. Whitespace around
  fields is fine. A value wider than the type is truncated.
- `gsaspectratio` takes only `N:M`. `Stretch` and `Auto 4:3/3:2` appear in the docs but log
  `is an unknown aspect ratio`.
- A patch that should reach every user belongs upstream in GameDB or [`pcsx2_patches`][patches],
  whose README says "We do not create or fix patches". Upstream is a contribution: see the AI policy
  rule in the skill.

## Extended Codes

- `type=extended` RAW codes use the high nibble of `address`: `0`-`2` writes, `3` increment, `4`
  strided, `5` copy, `6` pointer, `7` OR/AND/XOR, `D` and `E` conditionals. `9` and `C` are
  unsupported: the executor at `v2.8.2` handles only `D` and `E` as conditionals.
- Multi-line codes use consecutive `patch=` lines. Do not mix conditionals with non-extended lines.
  A `D` code `Daaaaaaa,nntsvvvv` skips the next `max(n,1)` commands when false.
- Pointer codes of three or more lines were misread up to `v2.7.168`, and `bytes` patches were not
  applied from `v2.7.169` to `v2.7.185`.

## Dynamic Patches

- `dpatch=0,<P>,<R>,<off>,<val>,...` (P pattern pairs, then R replacement pairs, hex) patches code
  that loads at varying addresses. The field count must be `3 + 2*(P+R)`.
- It only runs under the EE recompiler, and a pattern with an absolute address immediate stops
  matching after relocation.

## Enabling and Errors

- Settings: `[EmuCore] EnableCheats`, `EnablePatches`, `EnableWideScreenPatches`,
  `EnableNoInterlacingPatches`. Per-game group toggles are `[Patches] Enable=` and `Disable=`, and
  `[Cheats] Enable=`, in the game's ini under `gamesettings/`.
- A bad line logs `(Patch) Error Parsing: <key>=<value>: <reason>` and is dropped while the rest of
  the file loads. Reasons include `Expected 5 data parameters; only found N`,
  `Invalid 'place' value`, `Malformed address`, `Unrecognized CPU Target`,
  `Unrecognized Operand Size`, and `Malformed data`. A line without `=` logs
  `Malformed patch line`. None of these shows in the UI, so read the log or run `check_pnach.py`.
- RetroAchievements hardcore mode disables cheats ("Cheats have been disabled due to
  RetroAchievements Hardcore Mode.") and skips patch files on disk.

[patch-cpp]: https://github.com/PCSX2/pcsx2/blob/v2.8.2/pcsx2/Patch.cpp
[patches]: https://github.com/PCSX2/pcsx2_patches
