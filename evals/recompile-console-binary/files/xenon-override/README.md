# Xenon Override Fixture

`generated/ppc_recomp.0.cpp` is XenonRecomp output for a homebrew XEX. The game's HUD function
`sub_82010C00` draws one frame too late. Replace it with a hand-written `override.cpp` that
calls through to the original after setting r3 to 1. Build files list `override.cpp` next to the
generated sources.
