# PCSX2 PS2 emulator: verify patches and texture replacements

Implementation baseline: PCSX2 v2.8.2. Verify the target build before using
version-specific interfaces.

## Patch identity and storage

Use **Tools → Edit Cheats** or **Edit Patches** for the current game to
create/open the correctly named file. Modern filenames use the game serial and
executable CRC, such as `SERIAL_CRC.pnach`; substitute the actual identity
reported by the emulator. Custom cheats belong in the configured cheats
directory, patches in the patches directory. Built-in patches can also come from
packaged archives; essential compatibility data belongs to GameDB. These sources
have different purposes and activation controls. [Patch guide][ref-patch-guide].

A title or matching serial alone does not establish compatible code addresses.
Record region, executable revision/CRC and any modified image. Before applying a
patch, inspect the original instruction/data at its intended EE or IOP address.
A wrong write can corrupt state without an immediate crash.

## PNACH writes and timing

The basic form is:

```text
patch=<place>,<cpu>,<address>,<type>,<data>
```

`cpu` is `EE` or `IOP`; address and data are hexadecimal. Direct types `byte`,
`short`, `word` and `double` write 1, 2, 4 and 8 bytes respectively. Big-endian
variants `beshort`, `beword`, `bedouble` and a `bytes` sequence are documented
for cases that need their explicit byte semantics. Do not confuse patch `word`
with the debugger `.sym` format's `.wrd` element size.

| Place | Application time |
| ----- | ---------------------------------------------------------------- |
| `0` | First execution entry/startup application. |
| `1` | Repeated at vertical blank. |
| `2` | Both startup and vertical blank. |
| `3` | Startup and immediately when enabled; documented since v2.5.385. |

Homebrew fixture example. Verify that the fixture owns address `00100000` before
use:

```ini
[Fixture counter]
comment=Set the known fixture counter on startup
patch=0,EE,00100000,word,00000001
```

Do not apply fixture addresses to other executables. Choose startup for one-time
initialization or code changes; a recurring write may suit a deliberately frozen
variable but can fight the game's own logic. Group headings expose selectable
named patches; older ungrouped files remain relevant for pre-v1.7.4546 projects.
Use ungrouped files for versions before group support.

The `extended` type interprets supported RAW cheat codes, not an ordinary direct
write. Multi-line pointer/conditional codes are sequences whose order and count
matter. Preserve a supplied code's complete sequence and determine its code
family before conversion. Pointer behavior has documented corrections around
v2.7.169; older builds can interpret the same sequence differently. Prefer a
verified direct-address patch when the location is truly stable. For runtime
pointers, confirm allocation/module timing and the condition before enabling a
recurring write. Use the local RAW and dynamic-patch procedures below for
advanced code patches. [Formats, timing and RAW compatibility][source-1-1].

[source-1-1]: https://pcsx2.net/docs/advanced/writing-patches/

## RAW conditionals, pointers and dynamic code

For `extended`, the high nibble is an operation code, not part of a normal
direct address. `0`, `1` and `2` select 8-, 16- and 32-bit writes. `3`
increments/decrements, `4` writes a strided sequence of 32-bit values, `5`
copies bytes, `6` follows pointers, and `7` applies bitwise operations. `9` and
`C` are unsupported in the examined guide. Keep addresses within the documented
0x01ffffff range and follow the exact family encoding; malformed operands have
undefined behavior.

For a D conditional, `Daaaaaaa` with data `nntsvvvv` compares memory at `a` with
`v`; `nn` is the number of following patch commands to skip on false (at least
one), `t` selects comparison, and `s=0/1` selects 16/8 bits. Comparisons
`t=0/1/2/3` are equal/not-equal/less/greater; `4/5/6/7` are NAND/AND/NOR/OR
truth tests. Keep conditional bodies entirely `extended` and count command
lines, including continuation lines. For a fixture whose 16-bit mode is at
0x00110000:

```ini
patch=1,EE,D0110000,extended,01000002
patch=1,EE,20110010,extended,00000007
```

This writes 7 to the 32-bit value at 0x00110010 only while mode equals 2. The E
family expresses the same conditional fields as address `Esnnvvvv`, data
`taaaaaaa`.

For a one-level pointer fixture, the first line supplies `6aaaaaaa` and the
value; the second supplies `000snnnn` and final offset. Example:

```ini
patch=1,EE,60110000,extended,00000007
patch=1,EE,00020001,extended,00000010
```

It reads a 32-bit pointer at 0x00110000 and, if nonzero, writes a 32-bit 7 at
pointer + 0x10. Longer chains read another pointer at each intermediate offset,
then apply the final offset; pack continuation operands consecutively in their
specified order. Null checking does not prove that a non-null pointer is valid.
Verify allocation lifetime and each hop. Builds before v2.7.169 have
pointer-code errata and must not inherit this interpretation unchecked.

For relocated **code**, `dpatch` matches instruction patterns as the EE
recompiler compiles the offset-zero instruction. The format is
`dpatch=0,P,R,offset,value,...,offset,value,...`, with hexadecimal
pattern/replacement counts and four-byte-aligned offsets. It does not run with
the recompiler disabled and is not a dynamic-data pointer substitute. A fixture
pattern can replace one known instruction only when its neighbor also matches:

```ini
dpatch=0,2,1,0,24020001,4,03E00008,0,24020002
```

This pattern changes `addiu v0,zero,1` to `addiu v0,zero,2` when followed by `jr
ra`. Verify the surrounding routine and delay slot in the actual fixture; two
instructions may not uniquely identify a real game's function. Choose a pattern
whose offset-zero instruction executes before affected instructions, and avoid
absolute-address immediates that change on relocation. [RAW encoding, errata and
dynamic patches][source-2-1].

[source-2-1]: https://pcsx2.net/docs/advanced/writing-patches/

## Patch verification and retirement

Boot with the patch disabled and capture the original value/behavior. Enable one
group, reach the exact trigger and inspect the changed value/instruction plus
surrounding guest behavior. Repeat after reload or an overlay transition if
relevant. Disable the patch and restart to ensure a previous write is not
contaminating the comparison. For regressions, record built-in fixes, user
cheats, and rendering options separately. Change one mechanism per comparison.

## PCSX2 texture workflow

The examined implementation and UI expose **Load Textures**, **Dump Textures**,
**Dump Mipmaps**, **Asynchronous Texture Loading** and **Precache Textures**.
Use the game's graphics texture-replacement settings and the configured textures
directory in the isolated root. The implementation organizes content as
`textures/SERIAL/dumps` and `textures/SERIAL/replacements`; it does not replace
BIOS textures when there is no game serial. Sources: [UI
definitions][source-4-1], [replacement implementation][source-4-2].

1. Use a hardware renderer and enable dumping for the intended game. Visit the
   relevant scenes and stop the VM before editing.
1. Inspect generated PNGs and keep original names, including
   palette/region/mipmap identity. A dumped texture is a rendering asset, not
   necessarily one complete object from the game's source art.
1. Copy selected dumps into `replacements`, edit those copies, enable loading
   and repeat the scene. Keep the directory name/case correct rather than
   relying on recovery behavior.
1. Disable dumping during timing comparisons. Compare with loading disabled to
   establish the original rendering.

Texture names include data/palette hashes and format information, with region
and mip suffixes where needed. A renamed file may not be discovered, and a
palette change can create a different identity. Missing replacements can mean
wrong serial/directory, unsupported match, wrong filename, disabled loading or
an asset not yet encountered; distinguish these before changing renderer hacks.

Asynchronous loading can avoid blocking the emulation thread but allows a
replacement to appear later. Precaching shifts cost toward startup and memory.
Large uncompressed replacements and mip chains increase memory/VRAM use; judge
on the target GPU and disclose loading mode. Duplicates, FMV textures and alpha
interpretation need visual inspection at the actual scene. Keep texture packs
separate from PNACH changes so either can be removed independently.

[source-4-1]:
https://github.com/PCSX2/pcsx2/blob/v2.8.2/pcsx2-qt/Settings/GraphicsTextureReplacementSettingsTab.ui
[source-4-2]:
https://github.com/PCSX2/pcsx2/blob/v2.8.2/pcsx2/GS/Renderers/HW/GSTextureReplacements.cpp

[ref-patch-guide]: https://pcsx2.net/docs/advanced/writing-patches/
