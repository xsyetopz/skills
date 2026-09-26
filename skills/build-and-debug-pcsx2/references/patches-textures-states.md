# PNACH patches, texture replacement, and save states

Cards for the PNACH format and where files are found, `patch=` commands,
RAW `extended` codes, `dpatch`, texture dumping and replacement, and
save-state compatibility. Loader rules come from `pcsx2/Patch.cpp` at
`2c804670`; format text comes from [Writing Patches][patches]. Where they
disagree, the card follows the loader and says so.
`scripts/check_pnach.py` reproduces the loader's rejections before boot;
its tests and fixtures run in `assets/examples/verify.sh` (Executed).

## Contents

- PNACH file placement and naming
- patch command
- RAW extended codes
- dpatch dynamic patch
- Texture dump and replacement
- Save-state version caveats

## PNACH file placement and naming

**Definition.** Patches and cheats share the PNACH text format:

- User patches load from `patches/`.
- Cheats load from `cheats/`, and only when **Enable Cheats** is on.
- Bundled patches come from `resources/patches.zip`.
- GameDB patches come from `GameIndex.yaml`.

On disk, the loader globs `SERIAL_CRC*.pnach` and then `CRC*.pnach`
(`GetPnachTemplate`, `FindPatchFilesOnDisk`). The CRC is 8 hex digits,
matched case-insensitively because `StringUtil::WildcardMatch` compares
with `tolower`. A `patch=` line before the first `[group]` is legacy and
always on; such a line in `patches/` also stops the loader reading
`patches.zip` for that game. A `[group]` whose name was already loaded is
skipped. Group names such as `Cheats\Infinite Health` form a tree in the
UI. The matching global settings apply the groups `Widescreen 16:9` and
`No-Interlacing` automatically.

**Use when.**

- Creating or debugging a patch that does not show up or apply.

**Do not use when.**

- The change should reach every user as a compatibility fix: it belongs
  in upstream GameDB or `pcsx2_patches`. Read the policy card in
  [build from source](build-from-source.md#licence-and-ai-assistant-policy)
  before contributing.

**Example.** Create the file with **Tools > Edit Patches…** so the serial
and CRC come from the running game, then check it:

```sh
python3 scripts/check_pnach.py "$DATA/PCSX2/patches/SLUS-20062_ABCDEF01.pnach"
```

`check_pnach.py` warns when the loader would not find the file name.
Executed: it warned on `warn/SLUS-20062_notes.pnach`, which has no CRC.

**Cost removed.** Patches that silently never load. Count: checker
warnings for the file name, ungrouped lines, and duplicate groups.

**Verify.**

1. `python3 scripts/check_pnach.py FILE` prints `0 errors`, and every
   warning is intended or fixed.
1. After boot, the group appears on the game's **Patches** page and the
   emulog has no `(Patch) Error Parsing` line.

## patch command

**Definition.** `patch=<place>,<cpu>,<address>,<type>,<data>`. The loader
splits the five fields on commas and strips whitespace around each.

- `place` is `0` (once, at startup), `1` (every vsync), `2` (both; since
  v1.7.618), or `3` (startup and when enabled; since v2.5.385).
- `cpu` is `EE` or `IOP`, matched case-sensitively.
- `address` is up to 8 hex digits with no `0x`.
- `type` is `byte`, `short`, `word`, `double`, `extended`, `beshort`,
  `beword`, `bedouble` or `bytes`, lowercase only.
- `data` is hex with no prefix. For `bytes` it is an even-length hex
  string.

The loader logs `(Patch) Error Parsing: …` and drops a bad line; the game
still runs. A value wider than the type is truncated
(`static_cast<u8>` for `byte`).

**Use when.**

- The target address is fixed for this serial and CRC, and the debugger
  confirmed it.

**Do not use when.**

- The data moves on the heap: use the pointer code below.
- The code loads at a different address each time: use `dpatch`.
- The target is a different CRC or region: addresses do not carry over.

**Example.** From the good fixture
`assets/examples/pnach/good/SLPM-99999_1A2B3C4D.pnach` (synthetic serial,
CRC and addresses):

```ini
[Fixture\Every frame]
description=Freeze two bytes each vsync; spaces after commas are allowed.
patch=1, EE, 00100010, short, 0203
patch=1,EE,00100014,beword,78563412
patch=1,EE,00100020,bytes,48656C6C6F00
```

The checker rejects each of the 11 bad fixtures with the loader's
message, for example `Unrecognized CPU Target: 'ee'` and `Malformed
address '0x00100000'`. It warns on `data 1FF is wider than byte`.

**Cost removed.** Boot-and-look cycles for typos. Count: checker errors
before boot (target 0). Measured: the checker catches all 11 loader
rejection classes in the fixtures.

**Verify.**

1. `sh assets/examples/verify.sh` prints `PASS bad PNACH fixtures: 11
   loader errors, exit 1`.
1. In the debugger, the Memory view at the address shows the original
   value before enabling the group and the patched value after.

## RAW extended codes

**Definition.** With `type` set to `extended`, the high nibble of
`address` selects a RAW code:

- `0`, `1`, `2`: 8-, 16- and 32-bit writes.
- `3`: increment or decrement.
- `4`: strided 32-bit writes.
- `5`: copy bytes.
- `6`: follow pointers.
- `7`: bitwise OR, AND or XOR.
- `D` and `E`: conditionals.
- `9` and `C`: not supported.

Multi-line codes continue on consecutive `patch=` lines. Addresses are at
most `1ffffff`. A `D` code `Daaaaaaa`,`nntsvvvv` compares memory with `v`
and skips the next `max(n,1)` commands when false:

- `t` 0 to 3 is `==`, `!=`, `<`, `>`.
- `t` 4 to 7 is NAND, AND, NOR, OR.
- `s` is `0` for 16-bit, `1` for 8-bit.

Do not mix conditionals with non-`extended` lines. Errata:

- Pointer codes of three or more lines were misread up to v2.7.168.
- `bytes` patches were not applied from v2.7.169 to v2.7.185.

**Use when.**

- A write depends on game state (level, mode), or the data sits behind a
  pointer.

**Do not use when.**

- Targeting PCSX2 v2.7.168 or older with a pointer chain of three or more
  lines: the same text behaves differently there.

**Example.** From the good fixture:

```ini
[Fixture\Conditional]
patch=1,EE,D0100000,extended,0200ABCD
patch=1,EE,10100010,extended,00001234
patch=1,EE,10100020,extended,00001234

[Fixture\Pointer]
patch=1,EE,60110000,extended,00000007
patch=1,EE,00020001,extended,00000010
```

The first group writes 16-bit `1234` to two addresses while the 16-bit
value at `0x100000` is `ABCD`. The second reads a pointer at `0x110000`
and, if it is non-zero, writes 32-bit `7` at pointer + `0x10`.

**Cost removed.** Recurring writes that fight game logic in the wrong
state. 60 `Patch.*` GoogleTests cover the upstream semantics, executed
here: `core_test --gtest_filter='Patch.*'` printed `[  PASSED  ]
60 tests.` See
[unit tests target](build-from-source.md#unit-tests-target).

**Verify.**

1. `check_pnach.py` reports 0 errors. It checks the fields, not the
   nibble semantics.
1. A debugger Memory Write breakpoint on the target fires only when the
   condition holds, or only through the resolved pointer.

## dpatch dynamic patch

**Definition.** `dpatch=0,<P>,<R>,<off>,<val>,…` has `P` pattern pairs,
then `R` replacement pairs. Counts, offsets and values are hex; offsets
should be multiples of 4. When the EE recompiler compiles an instruction
whose surroundings match every pattern, it writes the replacements
relative to that instruction. With the recompiler off, `dpatch` does
nothing. Only type `0` is accepted.

**Use when.**

- You are patching code, not data, and it appears at varying addresses
  (overlays, relocated modules).

**Do not use when.**

- The EE interpreter is in use: the patch never runs.
- The pattern contains an absolute address immediate: it stops matching
  after relocation.

**Example.** From the good fixture: replace `addiu v0,zero,1` with
`addiu v0,zero,2` when `jr ra` follows it.

```ini
dpatch=0,2,1,0,24020001,4,03E00008,0,24020002
```

A mismatched pair count gives `Expected 2 fields for each 2
patterns and 1 replacements; found 3` (bad fixture `10000008_dpatch`).

**Cost removed.** One `patch=` line per load address. Count: load
addresses covered by one `dpatch` line.

**Verify.**

1. `check_pnach.py` reports 0 errors, with no `offset … is not a multiple
   of 4` warning.
1. After the code runs once under the recompiler, the Disassembly view at
   the matched address shows the replacement.

## Texture dump and replacement

**Definition.** These `[EmuCore/GS]` keys control texture replacement:

- `DumpReplaceableTextures` and `DumpReplaceableMipmaps` write PNGs to
  `textures/<SERIAL>/dumps/`.
- `LoadTextureReplacements` loads `.png` or `.dds` files from
  `textures/<SERIAL>/replacements/`.
- `LoadTextureReplacementsAsync` (default true) loads them in the
  background.
- `PrecacheTextureReplacements` loads them all at startup.

This works only with hardware renderers (`GS/Renderers/HW`) and only with
a game serial. File names encode hashes:
`<TEX0hash>[-<CLUThash>][-r<W>x<H>]-<bits>[-mip<N>].png`.
`GSTextureReplacements.cpp` parses the name, so a renamed file never
matches.

**Use when.**

- Replacing or inspecting individual textures of a game the user owns.

**Do not use when.**

- The software renderer is selected: it ignores replacements.
- Comparing performance while dumping is on: dumping writes files in every
  frame where a new texture appears.

**Example.** Not runnable here (needs a booted game).

```ini
[EmuCore/GS]
DumpReplaceableTextures = true
LoadTextureReplacements = false
```

Visit the scene, stop the VM, copy the chosen dump from `dumps/` to
`replacements/` under the same name, and edit it. Then set
`DumpReplaceableTextures = false` and `LoadTextureReplacements = true`.
With GPU palette conversion on and full preloading off, the log says
`Palette textures will be disabled`.

**Cost removed.** Guessing file names. Observable: the replacement is
visible in the scene, with no `Failed to load replacement texture` log
line.

**Verify.**

1. `ls textures/<SERIAL>/replacements/` names match files in `dumps/`
   exactly, including case.
1. Screenshots with loading on and off differ only in the replaced
   texture.

## Save-state version caveats

**Definition.** A save state (`.p2s`, a zip) records `g_SaveVersion`.
Loading is refused when the state is newer than the emulator or the upper
16 bits differ (`SaveState.cpp`). Both `v2.8.2` and `2c804670` use
`0x9A590000`. The emulator logs `Savestate version: 0x9a590000` at VM
start (executed here in the `v2.8.2` no-BIOS run). Commits that bump it
carry `[SAVEVERSION+]` in their message, and the auto-updater looks for
that tag. Slot files are named `SERIAL (CRC).NN.p2s` in
`sstates/`.

**Use when.**

- Reusing a state across builds, for example while bisecting, or sharing
  a state in a report.

**Do not use when.**

- The state is the only evidence of a bug. States capture emulator
  internals and settings; a cold boot or an in-game memory-card save
  reproduces across versions, a state may not.
- The builds differ in save version: loading fails with "This save state
  was created with PCSX2 version …".

**Example.** Compare versions before loading a state from another build:

```sh
grep -m1 'Savestate version' old/emu.log new/emu.log
git log --oneline --grep='\[SAVEVERSION+\]' v2.8.2..2c804670
```

The `git log` needs full history, which the shallow clone used here
lacks. A GitHub commit search found 43 such commits, the most recent on
2026-03-15.

**Cost removed.** Bisect steps lost to refused or subtly corrupt states.
Count: `[SAVEVERSION+]` commits in the bisect range (0 means states are
accepted).

**Verify.**

1. Both logs print the same `Savestate version`.
1. After loading, the log has no "no longer compatible" error, and the
   scene matches the state's screenshot.

[patches]: https://pcsx2.net/docs/advanced/writing-patches/
