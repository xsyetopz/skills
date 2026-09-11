"""Build, but never execute, a validated DuckStation command line."""

from __future__ import annotations

import argparse
import shlex
from pathlib import Path


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--exe", required=True, help="DuckStation executable path")

    target = p.add_mutually_exclusive_group()
    target.add_argument("--boot", type=Path, help="Positional boot filename")
    target.add_argument("--bios", action="store_true", help="Boot BIOS/system menu")
    target.add_argument("--state-file", type=Path, help="Load a save-state file")
    target.add_argument("--psx-exe", type=Path, help="Boot a PS-X executable")

    p.add_argument("--resume", action="store_true")
    p.add_argument("--state", type=int, help="Save-state slot index")
    p.add_argument("--batch", action="store_true")
    p.add_argument("--no-gui", action="store_true")

    boot = p.add_mutually_exclusive_group()
    boot.add_argument("--fast-boot", action="store_true")
    boot.add_argument("--slow-boot", action="store_true")
    screen = p.add_mutually_exclusive_group()
    screen.add_argument("--fullscreen", action="store_true")
    screen.add_argument("--no-fullscreen", action="store_true")

    p.add_argument("--big-picture", action="store_true")
    p.add_argument("--early-console", action="store_true")
    return p


def build(args: argparse.Namespace, p: argparse.ArgumentParser) -> list[str]:
    if args.state is not None and args.state < 0:
        p.error("--state must be non-negative")
    if args.state is not None and args.state_file is not None:
        p.error("--state and --state-file are mutually exclusive")
    if args.resume and any(
        (args.bios, args.state_file, args.psx_exe, args.state is not None)
    ):
        p.error("--resume cannot be combined with BIOS, EXE, or another state mode")
    if args.state is not None and any((args.bios, args.psx_exe)):
        p.error("--state cannot be combined with BIOS or EXE boot")
    if args.no_gui and not any(
        (
            args.boot,
            args.bios,
            args.state_file,
            args.psx_exe,
            args.resume,
            args.state is not None,
        )
    ):
        p.error("--no-gui requires a bootable target, resume, or state")
    if args.batch and not any(
        (
            args.boot,
            args.bios,
            args.state_file,
            args.psx_exe,
            args.resume,
            args.state is not None,
        )
    ):
        p.error("--batch requires a bootable target, resume, or state")

    out = [args.exe]
    for enabled, flag in (
        (args.batch, "-batch"),
        (args.fast_boot, "-fastboot"),
        (args.slow_boot, "-slowboot"),
        (args.bios, "-bios"),
        (args.resume, "-resume"),
    ):
        if enabled:
            out.append(flag)
    if args.state is not None:
        out.extend(("-state", str(args.state)))
    if args.state_file:
        out.extend(("-statefile", str(args.state_file)))
    if args.fullscreen:
        out.append("-fullscreen")
    if args.no_fullscreen:
        out.append("-nofullscreen")
    if args.no_gui:
        out.append("-nogui")
    if args.big_picture:
        out.append("-bigpicture")
    if args.early_console:
        out.append("-earlyconsole")
    boot_path = args.boot or args.psx_exe
    if boot_path:
        out.extend(("--", str(boot_path)))
    return out


def main() -> None:
    p = parser()
    print(shlex.join(build(p.parse_args(), p)))


if __name__ == "__main__":
    main()
