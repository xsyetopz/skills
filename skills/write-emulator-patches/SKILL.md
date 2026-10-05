---
name: write-emulator-patches
description: >-
  Writes and fixes emulator game patches and cheat codes: PCSX2 pnach, DuckStation cht, Dolphin
  Gecko, Action Replay and OnFrame, RPCS3 patch.yml, PPSSPP CWCheat, plus the settings that enable
  them. Use when a code does not apply, a file fails to load, or a patch must target one region or
  revision. Not for emulator crashes or guest debugging ($debug-game-in-emulator).
when_to_use: >-
  My pnach does nothing in PCSX2. Write a widescreen patch for my homebrew. Convert this Gecko code
  to OnFrame. RPCS3 skips my patch.yml. Merge these cheat settings into settings.ini.
---

# Write Emulator Patches

Game patches and cheats are memory writes keyed to one executable. Each emulator has its own file
format and its own loader. Without this skill, agents write codes in the wrong grammar, key them to
the wrong revision, and report success because the loader dropped the bad line without a visible
error.

## Rules

- Write codes only for games the user owns or legally obtained, or for their own homebrew. Never
  download or generate a BIOS, a game image, or keys.
- Key each file or entry to the exact executable: PCSX2 serial and CRC, DuckStation serial (plus
  the hash for a revision with different offsets), Dolphin game ID (plus `r<rev>`), RPCS3
  executable hash, PPSSPP disc ID. Addresses differ between regions and revisions, so a code for one
  is wrong for another. Ask for the ID or the log line that shows it.
- Check every file with a tool before booting, because loaders drop a bad line with only a log
  message, or none (Dolphin OnFrame). Run `python3 scripts/check_pnach.py FILE` for `.pnach` and
  chtdb's `validate_file.py` for `.cht`. For other formats, read the log after loading.
- Test one code at a time from a cold boot, with every other code, cheat, and texture pack off. Do
  not load a save state to test, because it skips the code paths that run at boot.
- Quote the log line or the in-game result that shows a code applied. A clean load is not proof.
- Say that RetroAchievements hardcore mode disables cheats (and in PCSX2, patch files on disk), so
  turn it off before testing.
- Edit an emulator's settings only while it is stopped, and use only keys the same release wrote.
- Never clone, read, build, or modify DuckStation source. Its repository `CLAUDE.md` forbids AI
  assistants from operating on it. Writing `.cht` files and editing a release's `settings.ini` is
  fine.
- Before any upstream contribution of a patch, apply that project's AI policy:
  - PCSX2 `AGENTS.md`: never create an issue or a PR, and disclose AI use with `(AI-assisted)`.
    Bundled patches come from `pcsx2_patches`.
  - Dolphin `Contributing.md`: contributions only from humans, and no LLM use for changes to
    console behavior. Do not draft a GameSettings change.
  - RPCS3, PPSSPP, and xemu: AI-assisted PRs need a disclosure. The human sends all communication.
  - DuckStation: patches go by email or Discord. chtdb takes `.cht` files.

## Workflow

1. Identify the emulator, its release or commit, the game ID, and the region and revision. Read the
   emulator's reference below.
1. Find or confirm the addresses from the user's own memory search or disassembly. Do not invent
   addresses or copy them from another revision.
1. Write the code in that emulator's grammar, in the user directory, not in bundled defaults.
1. Run the checker for the format. Fix every error and read every warning.
1. Enable the code (settings or the per-game list), boot cold with only this code on, and read the
   log for a load error or an applied line.
1. Report the file path, the ID it is keyed to, the checker result, and the log line or in-game
   result.

xemu has no patch or cheat system in its source or docs. For an Xbox game, say so and suggest
memory edits through its QEMU monitor or GDB stub (`$debug-game-in-emulator`).

## Scripts

- On Windows, use `py -3` for `python3`.
- `python3 scripts/check_pnach.py FILE... [--json] [--limit N]` reports the errors and warnings
  PCSX2's patch loader would raise. Exit 0 no errors, 1 errors, 2 usage or unreadable input.
- `python3 scripts/check_settings_keys.py FILE... [--keys LIST]` checks a DuckStation
  `settings.ini` against the keys release 0.1-11826 wrote: typos, duplicates, and non-boolean
  values. Exit 0 clean, 1 findings, 2 usage or unreadable input.
- `scripts/testdata/pnach/`: good, warn, and bad `.pnach` samples for the checker's tests.

## References

| Emulator | Reference |
| --- | --- |
| PCSX2 (PS2) `.pnach` | [`references/pcsx2-pnach.md`](references/pcsx2-pnach.md) |
| DuckStation (PS1) `.cht` | [`references/duckstation-cht.md`](references/duckstation-cht.md) |
| Dolphin (GameCube, Wii) | [`references/dolphin.md`](references/dolphin.md) |
| RPCS3 (PS3) `patch.yml` | [`references/rpcs3.md`](references/rpcs3.md) |
| PPSSPP (PSP) CWCheat | [`references/ppsspp-cwcheat.md`](references/ppsspp-cwcheat.md) |
| Settings files, OpenEmu | [`references/frontend-config.md`](references/frontend-config.md) |

For crashes, boot failures, renderer bugs, or stepping guest code, use `$debug-game-in-emulator`.
