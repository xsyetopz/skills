# PPSSPP CWCheat Files

Checked against PPSSPP master `647819fb` ([`Core/CwCheat.cpp`][cwcheat]); the parser is the same at
`v1.20.4` (`fa50bb19`).

## Contents

- [Location and Names](#location-and-names)
- [Line Grammar](#line-grammar)
- [Opcodes](#opcodes)
- [Enabling and Errors](#enabling-and-errors)

## Location and Names

- One file per game: `memstick/PSP/Cheats/<GAMEID>.ini`, UTF-8 (PPSSPP writes a BOM).
- A block whose `_S` disc ID does not match the running game is disabled. A file with a single
  legacy `_S` line is tolerated. Region releases have different IDs and addresses, so keep one
  block per ID.

## Line Grammar

```text
_S ULUS-99999
_G My Homebrew
_C1 Infinite Lives
_L 0x20123456 0x00000009
_C0 Debug Menu
_L 0x00123460 0x00000001
```

- `_S` disc ID, `_G` title, `_C0 name` a disabled cheat, `_C1 name` an enabled one, `_L` a code line
  of two hex words. `//` and `#` start comments.
- `_M` (TempAR) codes are rejected: "TempAR codes not supported".
- Addresses are offsets from user RAM: after the opcode nibble is masked off, the target is
  `(value + 0x08800000) & 0x3FFFFFFF` (`GetAddress` in `Core/CwCheat.h`). An address read from the
  PPSSPP memory viewer (`0x088xxxxx`) needs `0x08800000` subtracted.

## Opcodes

The high nibble of the first word selects the operation: `0` 8-bit write, `1` 16-bit write, `2`
32-bit write, `3` increment or decrement, `4` multi-write, `5` copy, `6` pointer, `7` boolean, `8`
multi, `A` PPSSPP-specific, `B` delay, `C` code stopper, `D` conditionals and joker (button) codes.

## Enabling and Errors

- Cheats need Enable Cheats: `[General] EnableCheats = True` in `ppsspp.ini`
  ([`Core/Config.cpp`][config]). It is a per-game setting, so a game's own config can override it.
- `_C0` disables a cheat; `_C1` through `_C9` all enable it.
- RetroAchievements hardcore mode disables cheats even with `EnableCheats` on.
- Errors appear only in the log as `CwCheat error: %s`: "Unrecognized content on line %d: expecting
  _", "expecting two values", "junk after line data", "unknown line type", and "could not parse
  cheat name line". Nothing shows in the UI, so run with `--log=FILE` and read it.

[cwcheat]: https://github.com/hrydgard/ppsspp/blob/647819fb/Core/CwCheat.cpp
[config]: https://github.com/hrydgard/ppsspp/blob/fa50bb19/Core/Config.cpp
