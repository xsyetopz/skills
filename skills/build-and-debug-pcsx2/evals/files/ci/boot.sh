#!/bin/sh
# CI job: boot our homebrew test ELF in PCSX2 v2.8.2 and check it runs.
# PS2_BIOS_DIR points at our own BIOS dump, stored as a runner secret.
set -e
BIN=/Applications/PCSX2-v2.8.2.app/Contents/MacOS/PCSX2
DATA=/tmp/ci/data
mkdir -p "$DATA/bios" "$DATA/PCSX2/inis"
cp "$PS2_BIOS_DIR"/* "$DATA/bios/"
printf '[UI]\nSetupWizardIncomplete = false\n' > "$DATA/PCSX2/inis/PCSX2.ini"
"$BIN" -batch -nogui -datapath "$DATA" -elf build/hello.elf
echo "BOOT OK"
