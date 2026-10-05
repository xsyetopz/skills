# DuckStation Cheats and Patches

Sources: the [chtdb README][chtdb] and its `validate_file.py` (commit `f6613303`), and the
DuckStation [README][readme]. DuckStation's own source was not read: its repository `CLAUDE.md` asks
AI assistants not to read or run anything in it. Write `.cht` files only, and never clone, build, or
modify DuckStation.

## Contents

- [Location and Names](#location-and-names)
- [File Format](#file-format)
- [User Choices](#user-choices)
- [Setting Overrides](#setting-overrides)
- [Opcodes](#opcodes)
- [Checking a File](#checking-a-file)

## Location and Names

- Game patches go in `patches/`, cheats in `cheats/`, both in the user directory (Tools > Open Data
  Directory). chtdb files patches as changes that give no advantage: performance, game-breaking bug
  fixes, frame-rate unlocks, and widescreen where the built-in hack is not enough. Anything that
  makes the game easier is a cheat.
- Files are `SERIAL.cht` or `SERIAL-HASH.cht`, where `HASH` is the XXHash DuckStation shows. Use the
  hash form only when revisions have different executable offsets, so a code for one revision does
  not work on the other.

## File Format

- Lines starting with `;` or `#` are comments.
- Each code is a `[Code Name]` header, then metadata, then the code body with no escaping:

  ```ini
  [Infinite Lives]
  Type = Gameshark
  Activation = EndFrame
  Description = Keeps lives at 9.
  Author = Optional name.
  80012345 0009
  ```

- `Type` is `Gameshark`, the only type the validator accepts. `Activation` is `EndFrame`, applied
  automatically at the end of each frame, or `Manual`, a one-shot the user triggers.
- Body lines are `XXXXXXXX YYYY` or `XXXXXXXX YYYYYYYY` hex. The chtdb validator accepted letter-O
  digits and hyphenated addresses that this format does not allow, so read the format as well.

## User Choices

- `OptionRange = min:max` shows a spinbox. `Option = Name:Value` (repeat for each entry) shows a
  dropdown. Values are decimal unless prefixed `0x` or `0b`.
- Replace the value nibbles the choice fills with `?`. DuckStation shifts the chosen value into the
  `?` position. `80001234 00??` with `OptionRange = 1:100` writes the chosen value to `0x1234`.

## Setting Overrides

Put these before the code body:

- `OverrideAspectRatio`, `OverrideCPUOverclock` (a percentage), `DisableWidescreenRendering`,
  `Enable8MBRAM`, and `DisallowForAchievements` (blocks the code in RetroAchievements hardcore
  mode).

## Opcodes

The first byte of the address word selects the operation (from `validate_file.py`):

| Byte | Operation |
| - | - |
| `30`, `80`, `90` | Write 8, 16, 32 bits |
| `31`/`32`, `81`/`82`, `91`/`92` | Set or clear bits, 8, 16, 32 |
| `10`/`11`, `20`/`21`, `60`/`61` | Increment or decrement 16, 8, 32 |
| `D0`-`D3`, `E0`-`E3`, `A0`-`A3` | If equal, not equal, less, greater (16, 8, 32), next line |
| `D4`-`D7` | Button compares |
| `C0` | Skip if not equal (16) |
| `C1` | Delay activation |
| `C2` | Memory copy (2 lines) |
| `50`, `53` | Slide (2 lines); line 2 is a write (`50`) or a write or bit opcode (`53`) |
| `F4` | Find and replace (5 lines) |

`00` is a no-op. Other opcodes (`1F`, `51`, `52`, `A4`-`A8`, `C3`-`C6`, `E4`, `E5`, `F0`-`F3`,
`F5`, `F6`) exist; read the validator's table before using one.

## Checking a File

- Run chtdb's `validate_file.py` from a clone of [duckstation/chtdb][chtdb] (not the DuckStation
  repository). It reports `Unknown opcode`, `Empty body for cheat`, `Duplicate code name`,
  `Malformed section header`, and `Code data outside any section`.
- Test each code alone from a cold boot with every other code off. A code never proves an emulator
  fix.

[chtdb]: https://github.com/duckstation/chtdb
[readme]: https://github.com/stenzek/duckstation/blob/master/README.md
