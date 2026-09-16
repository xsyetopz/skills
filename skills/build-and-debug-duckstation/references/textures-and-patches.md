# DuckStation PS1 emulator: verify textures and guest patches

Implementation baseline: DuckStation commit
`cbe7951be624a3fd69c81858647a8f84e4a1d06b`. Verify the target build before using
version-specific interfaces.

## Texture replacement

1. In the isolated profile, enable the texture cache under **Graphics Settings →
   Texture Replacements**, then enable texture dumping.
1. Run the target scene and move through the relevant content. Stop the VM
   before reviewing the dump.
1. Open the data directory and inspect `textures/SERIAL/dumps`. Keep the game's
   exact serial/revision with the fixture.
1. Copy selected files into `textures/SERIAL/replacements`, preserving generated
   identities, then edit/resize those copies. PNG, JPG and WebP are documented
   replacement formats.
1. Disable dumping for comparison, enable replacements and repeat the scene.
   Confirm both correct substitution and absence of unintended replacements.

The PS1's VRAM uploads do not map cleanly to modern immutable texture assets.
Filenames encode texture-data hash, palette hash where applicable, upload size,
subrectangle and palette range. Do not rename them to descriptive filenames
without an alias mapping. Wrong palette/subrectangle matching can replace
unrelated content or create many duplicates. Source: [texture
replacement][source-0-1].

A game-local `textures/SERIAL/config.yaml` is created when dumping starts.
Adjust one relevant option and redump when it changes identity:

- **Upload tracking cannot identify useful textures** Relevant option and
  tradeoff: `DumpTexturePages` uses drawn page subrectangles; often creates
  duplicates and less reliable matching. `DumpFullTexturePages` captures whole
  pages and is usually less useful.

- **Direct-color content is missing** Relevant option and tradeoff:
  `DumpC16Textures` includes it, but may also dump FMV/postprocessing noise.

- **Unused palette entries cause duplicate identities** Relevant option and
  tradeoff: `ReducePaletteRange` hashes used entries; can improve reliability
  with some CPU overhead.

- **Animated content is assembled through VRAM copies** Relevant option and
  tradeoff: `ConvertCopiesToWrites` tracks those copies, at the cost of
  additional duplicates.

- **Partially overwritten uploads disappear** Relevant option and tradeoff:
  `MaxVRAMWriteSplits` controls tracking splits.

- **Logs repeatedly show one-line uploads** Relevant option and tradeoff:
  `MaxVRAMWriteCoalesceWidth` / `MaxVRAMWriteCoalesceHeight` allow appropriate
  neighboring uploads to combine.

- **Tiny irrelevant dumps dominate** Relevant option and tradeoff:
  Texture/upload width and height thresholds filter them; too high omits useful
  content.

- **Texture packs exhaust memory or stall** Relevant option and tradeoff: Keep
  hash/replacement cache budgets within target RAM/VRAM; increasing them is not
  a universal fix.

Map a dumped identity to a replacement filename in `Aliases`. Replace the key
below with that exact identity:

```yaml
Aliases:
  GENERATED-TEXTURE-IDENTITY: shared-wall.png
```

Keep native-scale, no-replacement and replacement captures at the same
checkpoint. Preloading/cache behavior and replacement resolution affect memory
and timing; disclose them in performance comparisons. Check replacement behavior
in each affected scene.

[source-0-1]: https://github.com/stenzek/duckstation/wiki/Texture-Replacement

## Patches and cheats

The examined README distinguishes built-in compatibility/enhancement data, cheat
databases and automatic PPF disc patches. Use the game's properties/cheat
interface to inspect active entries and keep experimental changes in the
isolated data tree. Record the active mechanism: cheats write guest state, PPF
patches alter disc reads, and renderer enhancements change presentation. For an
existing PPF, preserve the original image and match its exact intended disc
revision before enabling it. Do not infer compatibility from title alone.
[Feature and patch documentation][source-1-1].

[source-1-1]:
https://github.com/stenzek/duckstation/blob/cbe7951be624a3fd69c81858647a8f84e4a1d06b/README.md
