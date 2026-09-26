# Textures, patches, and cheats

Cards for the content DuckStation applies on top of a game: dumped and
replacement textures, and chtdb-format patches and cheats. Sources: the
[Texture Replacement wiki page][wiki-tex] (wiki commit `f79454bf`), the
[duckstation/chtdb README][chtdb] (commit `99853a6`), and the settings
written by release `v0.1-11826`.

## Contents

- Texture dumping
- Texture replacement and aliases
- Per-game texture options
- Patches and cheats file

## Texture dumping

**Definition.** With the texture cache on (`[GPU] EnableTextureCache`)
and dumping on (`[TextureReplacements] DumpTextures`), a hardware
renderer writes each tracked texture as an image under
`textures/<SERIAL>/dumps` in the user directory. Names follow
`texupload-P4-<16 hex data hash>-<16 hex palette hash>-<upload WxH>-
<x>-<y>-<sub-texture WxH>-P<first>-<last>` (one name, wrapped here);
direct (C16) textures have no palette fields ([wiki][wiki-tex]).

**Use when.**

- Preparing replacements, or checking whether a game's textures are
  tracked at all.

**Do not use when.**

- The renderer is Software: texture replacement is a hardware-renderer
  feature ([README][readme]).
- Measuring performance: dumping writes files while the game runs.

**Example.** Settings for a dump run (defaults are `false`):

```ini
[GPU]
EnableTextureCache = true

[TextureReplacements]
DumpTextures = true
EnableTextureReplacements = false
```

```sh
python3 scripts/check_formats.py settings "$M/settings.ini"
ls "$M/textures"/*/dumps | head
python3 scripts/check_formats.py texture-name \
  $(ls "$M/textures/$SERIAL/dumps")
```

The checker's C16 name pattern is inferred from the wiki sentence, not an
observed dump, and it accepts P8 by analogy with P4.

**Cost removed.** Replacement work on textures the game never re-uploads
the same way. Observable: files appear in `dumps/`, and their names pass
`check_formats.py texture-name`.

**Verify.**

1. Stop the virtual machine (wiki step 4), then count files in `dumps/`.
1. Tier: settings and name checks Executed on fixtures; dumping Not
   runnable here (needs a booted game).

## Texture replacement and aliases

**Definition.** Copy dumped files to the game's replacements directory,
edit them (PNG, JPG, or WebP), and enable
`[TextureReplacements] EnableTextureReplacements`. `config.yaml` in the
game's texture directory maps several dumped names to one file under
`Aliases:` ([wiki][wiki-tex]).

**Use when.**

- The dumped name is stable across runs of the same scene.

**Do not use when.**

- You would give files readable names without an alias: the loader
  matches the generated name.
- Several dumps differ only by palette range and the game needs
  `ReducePaletteRange` (below): fix the option first, then redump.

**Example.** `textures/<SERIAL>/config.yaml` (wiki format):

```yaml
Aliases:
  texupload-P4-AAAAAAAAAAAAAAAA-BBBBBBBBBBBBBBBB-64x256-0-192-64x64-P0-14: |
    texupload-P4-BBBBBBBBBBBBBBBB-BBBBBBBBBBBBBBBB-64x256-0-64-64x64-P0-13.png
  texupload-P4-CCCCCCCCCCCCCCCC-BBBBBBBBBBBBBBBB-64x256-0-0-64x64-P0-14: a.png
```

The wiki calls the target folder "the replacements directory" without a
literal path; before copying, confirm its name through
**Tools > Open Data Directory** in the release under test.

**Cost removed.** Duplicate image edits. Observable: one edited file
serves every aliased name.

**Verify.**

1. `python3 -c "import yaml,sys; yaml.safe_load(open(sys.argv[1]))"
   config.yaml` parses (needs PyYAML).
1. At the same checkpoint with replacements off and on, only the intended
   texture changes (Not runnable here).

## Per-game texture options

**Definition.** The first dump for a game creates `config.yaml`. Its
options (wiki) tune tracking: `DumpTexturePages`,
`DumpFullTexturePages`, `DumpC16Textures`, `ReducePaletteRange`,
`ConvertCopiesToWrites`, `MaxVRAMWriteSplits`,
`MaxVRAMWriteCoalesceWidth`/`Height`, dump width/height thresholds,
`MaxHashCacheEntries`, `MaxHashCacheVRAMUsageMB`,
`MaxReplacementCacheVRAMUsage`, `ReplacementScaleLinearFilter`. The
global `settings.ini` defaults in 0.1-11826 include
`ReducePaletteRange = true`, `MaxHashCacheEntries = 1200`,
`MaxHashCacheVRAMUsageMB = 2048`, `DumpTextureWidthThreshold = 16`.

**Use when.**

| Symptom (wiki) | Option |
| --- | --- |
| Game incompatible with write tracking | `DumpTexturePages` (more duplicates) |
| 8-bit textures dump many duplicates | `ReducePaletteRange` |
| Animated textures built by VRAM copies | `ConvertCopiesToWrites` |
| Partially overwritten uploads vanish | `MaxVRAMWriteSplits` |
| Log repeats "tracking VRAM write of Nx1" | `MaxVRAMWriteCoalesceWidth` or `Height` = 1 |
| Direct-colour textures missing | `DumpC16Textures` |

**Do not use when.**

- Raising cache limits "just in case": the wiki warns that too many
  texture objects break mobile drivers and too much VRAM use causes
  swapping.

**Example.**

```yaml
ReducePaletteRange: true
ConvertCopiesToWrites: true
MaxVRAMWriteCoalesceWidth: 1
```

The `Key: value` layout follows the YAML `Aliases:` example; the wiki
prints no full file, so compare with the generated `config.yaml`.

**Cost removed.** Redump cycles that change several options at once.
Observable: one option changed per redump, and the dump count moves.

**Verify.**

1. `diff` of `config.yaml` before and after shows one option.
1. Count files in `dumps/` after a redump of the same scene.

## Patches and cheats file

**Definition.** DuckStation ships a community cheat and patch database
([README][readme]); its source is [duckstation/chtdb][chtdb]. Files are
`SERIAL.cht` or `SERIAL-HASH.cht`, INI-like: `[Code Name]`, metadata
(`Type = Gameshark`, `Activation = EndFrame` or `Manual`, `Description`,
`Author`, `Option`, `OptionRange = min:max`, and setting overrides such
as `OverrideCPUOverclock`), then code lines. Patches give the player no
advantage (frame-rate, bug fixes, widescreen); cheats do. The
user directory has `cheats/` and `patches/` folders
(`[Folders] Cheats`, `Patches`).

**Use when.**

- A symptom may come from an enabled code: disable all codes and re-run
  before blaming the emulator.
- Writing a code for a self-built test program.

**Do not use when.**

- The code targets another disc revision: per the README, the
  `SERIAL-HASH` form exists because offsets differ between revisions.
- Claiming a patch fixes the emulator: it changes guest memory.

**Example.** Runnable: `assets/examples/cheats/HASH-EXAMPLE.cht`.

```ini
[Example Chosen Value]
Type = Gameshark
Activation = Manual
Description = Writes the value picked in the UI spinbox.
OptionRange = 1:100
80010002 00??
```

```sh
python3 scripts/check_formats.py cht assets/examples/cheats/*.cht
```

The chtdb repository also has an MIT `validate_file.py` that checks
opcodes; it passed `HASH-EXAMPLE.cht` in this session.

**Cost removed.** Codes outside the documented format reaching the
emulator unreviewed; how DuckStation treats such lines was not observed.
Measured: over all 4,634 files in chtdb `99853a6`,
`check_formats.py cht` printed 209 findings outside the README format
(for example `8008DA9A OCOO` with letter O, `800C6E79-0001` with a
hyphen, `?` without `Option`), while chtdb's own validator reported every
file OK. The rule that `?` needs `Option` or `OptionRange` is this
checker's reading of the README, not a documented error. On
`bad-example.cht` it reports 3 codes; the chtdb validator reports 1.

**Verify.**

1. `check_formats.py cht FILE` prints `OK`.
1. In the release, the code appears in the game's cheat or patch list and
   changes the targeted memory (Not runnable here).

[wiki-tex]: https://github.com/stenzek/duckstation/wiki/Texture-Replacement
[chtdb]: https://github.com/duckstation/chtdb
[readme]: https://github.com/stenzek/duckstation/blob/master/README.md
