# Xenon Switch Fixture

`recomp.toml` drives XenonRecomp for a homebrew XEX. The last run printed this line, and the native
build aborts in `sub_82003A40` at the matching `bctr`:

```text
Found a switch jump table at 82003A7C with no switch table entry present
```

Disassembly facts for that jump table (the `bctr` is at 0x82003A7C, the table register is r11,
the default case is 0x82003AF0, and the five case labels are listed in order):

```text
labels: 0x82003A9C 0x82003AA8 0x82003AB4 0x82003AC0 0x82003AD4
```

`generated/` is recompiler output and is regenerated on every run.
