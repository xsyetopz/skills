# Frontend Settings for Patches

Settings files decide whether a patch or cheat loads at all. Edit them as carefully as the codes.

## Contents

- [Editing Rules](#editing-rules)
- [PCSX2](#pcsx2)
- [DuckStation](#duckstation)
- [Dolphin, RPCS3, and PPSSPP](#dolphin-rpcs3-and-ppsspp)
- [OpenEmu](#openemu)

## Editing Rules

- Edit an emulator's settings only while it is stopped. A running emulator keeps its own copy and
  can save it over the file, which drops the edit.
- Use only keys and values that the same release wrote. For an unknown key, set the option once in
  the UI and copy the changed line. Record the release with each key.
- Back up the file first, and change one key per test run.

## PCSX2

Checked against `v2.8.2` `Patch.cpp`, `Pcsx2Config.cpp`, `VMManager.cpp`, and
`INISettingsInterface.cpp`.

- In `inis/PCSX2.ini`, `[EmuCore]`: `EnableCheats`, `EnablePatches`, `EnableWideScreenPatches`, and
  `EnableNoInterlacingPatches`. The first two can also be set in a per-game file. PCSX2 deletes the
  last two from per-game files, so set them only globally.
- Per game, in `gamesettings/<SERIAL>_<CRC>.ini`, with the CRC as eight uppercase hex digits
  (`SLUS-12345_ABCDEF01.ini`). A game with no serial uses `<CRC>.ini`, which is also the legacy
  name PCSX2 still reads.
- In that file, `[Patches] Enable=<group>` and `Disable=<group>`, and `[Cheats] Enable=<group>`,
  one line per group (the key repeats). The value must equal the `.pnach` `[group]` name exactly.
- RetroAchievements hardcore mode disables cheats and skips patch files on disk.

## DuckStation

Checked against release `v0.1-11826` and the `settings.ini` it wrote.

- `python3 scripts/check_settings_keys.py settings.ini` checks a `settings.ini` against the keys
  that release wrote (`assets/duckstation-settings-keys-0.1-11826.txt`). It reports unknown keys,
  duplicates, and non-boolean values such as `yes`. Exit 0 clean, 1 findings, 2 usage error.
- For another release, pass `--keys LIST` with a key list made from that release's own
  `settings.ini`.
- The settings keys that turn cheats and patches on were not confirmed from a permitted source.
  Turn them on in the UI and copy the changed lines.
- `DisallowForAchievements` in a `.cht` code blocks it in hardcore mode (see `duckstation-cht.md`).

## Dolphin, RPCS3, and PPSSPP

- Dolphin: `[Core] EnableCheats` in `Dolphin.ini` gates Gecko and Action Replay codes. The
  per-code `_Enabled` sections live in the game ini (see `dolphin.md`).
- RPCS3: patch enable state is in `patch_config.yml`. Use the Patch Manager to toggle a patch.
- PPSSPP: `[General] EnableCheats` in `ppsspp.ini`, which a per-game config can override (see
  `ppsspp-cwcheat.md`).

## OpenEmu

Checked against OpenEmu `1d205104` and OpenEmu-SDK `c849d831`.

- Settings are user defaults. The domain is probably `org.openemu.OpenEmu` (inferred from the
  project's `org.openemu.` bundle prefix, not confirmed), so check with
  `defaults domains | tr ',' '\n' | grep -i openemu` first. Read them with `defaults read <domain>`
  while OpenEmu is closed. Per-core key names were not confirmed, so copy a key from that output
  rather than guessing one.
- Cheats work only where the core declares `OEGameCoreSupportsCheatCode` for the system.
- The built-in database is `OpenEmu/Other Assets/cheats-database.xml`. Entries look like
  `<cheat code="010F4ED8+01424FD8" type="GameShark" description="…"/>`, are matched by ROM MD5, and
  join multi-line codes with `+`.
- Saving user-added cheats is a TODO in `OEGameDocument.swift`, so a cheat added in the UI may not
  persist. Test it after a restart.
