# RPCS3 patch.yml

Checked against RPCS3 master `3e747710` ([`Utilities/bin_patch.cpp`][bin-patch] and `bin_patch.h`).
The file path, engine version, serial and app-version rules, file names, and hash log line were
also checked against release `v0.0.43` (`53d44aa4`). The
[Game Patches wiki page][wiki] was not readable (Cloudflare), so the format below comes from the
source only.

## Contents

- [Location and Names](#location-and-names)
- [Structure](#structure)
- [Patch Types](#patch-types)
- [Errors](#errors)

## Location and Names

- Patch files live in `<config>/patches/`: `patch.yml` (the downloaded database),
  `imported_patch.yml`, and `<TITLEID>_patch.yml`, loaded in that order. "Download latest patches"
  renames `patch.yml` to `patch.yml.old` and writes a new `patch.yml`; it does not touch the other
  files. Put the user's own patches in `<TITLEID>_patch.yml`.
- The Patch Manager stores enable state and configurable values in `<config>/patch_config.yml`.
  Toggle patches there rather than editing that file.

## Structure

- The file starts with `Version: 1.2`, the engine version. A mismatch is a load error.
- Top-level keys are executable hashes: `PPU-<40 hex SHA-1>`, `SPU-…`, `PRX-…`, `OVL-…`, or `ALL`.
  The hash is per executable build, so a disc revision or update needs its own entry. Copy the
  hash (lowercase hex) from the `ppu_loader` log line `PPU executable hash: PPU-…` rather than
  computing it. When patches applied, the line ends with `(<- N)`, the number of patches.
- Under the hash, each patch is keyed by its description:

```yaml
Version: 1.2

PPU-0123456789abcdef0123456789abcdef01234567:
  "Skip intro":
    Games:
      "My Homebrew":
        NPUB99999: [ 01.00 ]
    Author: "me"
    Patch Version: 1.0
    Notes: "Tested from a cold boot."
    Patch:
      - [ be32, 0x00123456, 0x60000000 ]
```

- The serial is 9 alphanumeric characters. The app version is `NN.NN` or `All`.
- `Group`, `Notes`, `Configurable Values`, and a top-level `Anchors` section are optional.
- When two files define the same description, the higher `Patch Version` wins, with a warning.
- Patches apply in this order: all serials and all versions, all serials and this version, this
  serial and all versions, this serial and this version.

## Patch Types

- Types: `alloc`, `calloc`, `jump`, `jumpl`, `jumpf`, `load`, `byte`, `le16`, `le32`, `le64`,
  `lef32`, `lef64`, `be16`, `be32`, `bd32`, `be64`, `bd64`, `bef32`, `bef64`, `bpex`, `utf8`,
  `cutf8`, `move_file`, `hide_file`.
- PS3 code and data are big-endian, so instruction patches use `be32`.
- Addresses for `alloc` through `cutf8` need the `0x` prefix.

## Errors

The `PAT` log channel in `RPCS3.log` reports:

- "Error: File version %s does not match patch engine target version %s" and
  "Error: No 'Version' entry found."
- "Skipping patch node %s: type '%s' is invalid." and
  "Skipping patch node %s. Address element has wrong format %s."
- "Error: Serial '%s' invalid" and "Error: Skipping invalid app version '%s'".
- A patch that loaded logs "Applied patch (hash=…)". No such line means it did not apply.

[bin-patch]: https://github.com/RPCS3/rpcs3/blob/3e747710/Utilities/bin_patch.cpp
[wiki]: https://wiki.rpcs3.net/index.php?title=Help:Game_Patches
