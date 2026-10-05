# Dolphin Game Patches and Cheats

Checked against Dolphin master `0961ec1d` ([`PatchEngine.cpp`][patch-engine],
`GameConfigLoader.cpp`, `GeckoCode*.cpp`, `ActionReplay.cpp`). Dolphin has no tagged GitHub
releases, so record the build string from Help > About.

Dolphin's [`Contributing.md`][contributing] accepts contributions "from humans, not from AI agents"
and forbids using LLMs "to make changes related to the behavior of the emulated console or to use
LLMs to obtain information related to the console". Write codes for the user's own game ini only,
and never draft an upstream change or a GameSettings PR.

## Contents

- [Location and Names](#location-and-names)
- [OnFrame Patches](#onframe-patches)
- [Gecko Codes](#gecko-codes)
- [Action Replay Codes](#action-replay-codes)
- [Enabling and Errors](#enabling-and-errors)

## Location and Names

- Defaults live in `Data/Sys/GameSettings`, user files in `<User>/GameSettings`. The user file is
  read after the default one. Put codes in the user file, never in the defaults.
- Files load in ascending priority: `X.ini` (the system code, the first letter of the game ID),
  `XXX.ini` (first three), `<ID>.ini` (six characters), then `<ID>r<rev>.ini`, also for revision 0.
  The one- and three-letter files load only for six-character IDs. Use the `r<rev>` file for
  addresses that differ between disc revisions, because `<ID>.ini` applies to all of them.

## OnFrame Patches

- Section `[OnFrame]`. Each patch is a `$Name` line, then lines of
  `0xADDR:byte|word|dword:0xVALUE[:0xCOMPARAND]`. With a comparand, the write happens only while
  memory equals it. `word` is 16 bits and `dword` is 32; type names are lowercase and exact.
- Numbers are parsed with base auto-detection: `0x` is hex, a leading `0` is octal, and anything
  else is decimal. Always write the `0x` prefix. Without it, `80123456` is a wrong decimal address
  and `803A1F20` does not parse at all.
- OnFrame patches are not gated by Enable Cheats.
- A bad line is dropped with no message, so read the line back against this grammar.

```ini
[OnFrame]
$Skip intro
0x80123456:dword:0x60000000
[OnFrame_Enabled]
$Skip intro
```

## Gecko Codes

- Section `[Gecko]`. Each code is `$Name [Creator]`, optional `*` note lines, then code lines of
  `XXXXXXXX XXXXXXXX`. Both words are parsed as hex with no length check, so a short word such as
  `3E7` loads as `000003E7`. Pad to eight digits anyway, for readability.
- The enable list names the code without its creator: `$Name`, not `$Name [Creator]`.
- The code handler lives in game RAM at `0x80001800`-`0x80003000`. Too many codes log
  "Too many GeckoCodes! Ran out of storage space in Game RAM."

## Action Replay Codes

- Section `[ActionReplay]`. Each code is `$Name`, then decrypted `XXXXXXXX XXXXXXXX` lines or
  encrypted `XXXX-XXXX-XXXXX` lines.
- A bad line shows a popup: "Action Replay Error: invalid AR code line: {0}".

## Enabling and Errors

- List each enabled code by `$Name` under `[OnFrame_Enabled]`, `[Gecko_Enabled]`, or
  `[ActionReplay_Enabled]`. The `_Disabled` sections turn off a default code.
- Gecko and Action Replay codes also need `[Core] EnableCheats = True` in `Dolphin.ini`.
- RetroAchievements hardcore mode runs only approved codes. Others show
  "Failed to verify code {} for game ID {}." and "Disable hardcore mode to enable this code."

[patch-engine]:
https://github.com/dolphin-emu/dolphin/blob/0961ec1d/Source/Core/Core/PatchEngine.cpp
[contributing]: https://github.com/dolphin-emu/dolphin/blob/0961ec1d/Contributing.md
