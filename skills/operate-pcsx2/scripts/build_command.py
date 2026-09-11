"""Build, but never execute, a validated PCSX2 command line."""

from __future__ import annotations

import argparse
import shlex
from pathlib import Path


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--exe", required=True, help="PCSX2 executable path")

    target = p.add_mutually_exclusive_group()
    target.add_argument("--boot", type=Path, help="Positional boot filename")
    target.add_argument("--bios", action="store_true", help="Boot BIOS/system menu")
    target.add_argument("--elf", type=Path, help="Boot a PS2 ELF")
    p.add_argument(
        "--state-file", type=Path, help="Load a save state with a boot target"
    )
    target.add_argument("--test-config", action="store_true")
    target.add_argument("--setup-wizard", action="store_true")

    p.add_argument(
        "--disc",
        type=Path,
        help="Host DVD drive path with --elf; use --boot for an image",
    )
    p.add_argument("--game-args", help="Single argument string passed to the game")
    p.add_argument("--state", type=int, help="Save-state slot index")
    p.add_argument("--batch", action="store_true")
    p.add_argument("--no-gui", action="store_true")

    data = p.add_mutually_exclusive_group()
    data.add_argument("--portable", action="store_true")
    data.add_argument("--data-path", type=Path)

    p.add_argument("--log-file", type=Path)
    boot = p.add_mutually_exclusive_group()
    boot.add_argument("--fast-boot", action="store_true")
    boot.add_argument("--slow-boot", action="store_true")
    screen = p.add_mutually_exclusive_group()
    screen.add_argument("--fullscreen", action="store_true")
    screen.add_argument("--no-fullscreen", action="store_true")
    speed = p.add_mutually_exclusive_group()
    speed.add_argument("--turbo", action="store_true")
    speed.add_argument("--unlimited", action="store_true")

    p.add_argument("--big-picture", action="store_true")
    p.add_argument("--early-console-log", action="store_true")
    p.add_argument("--debugger", action="store_true")
    p.add_argument("--ra-integration", action="store_true")
    return p


def build(args: argparse.Namespace, p: argparse.ArgumentParser) -> list[str]:
    if args.state is not None and args.state < 0:
        p.error("--state must be non-negative")
    if args.state is not None and args.state_file is not None:
        p.error("--state and --state-file are mutually exclusive")
    if args.game_args and args.elf is None:
        p.error("--game-args requires --elf")
    if args.disc and args.elf is None:
        p.error("--disc requires --elf in this strict command builder")
    has_boot_target = any((args.boot, args.bios, args.elf))
    if (args.state_file is not None or args.state is not None) and not has_boot_target:
        p.error("--state-file and --state require a boot target")
    if (args.no_gui or args.batch) and not (has_boot_target or args.big_picture):
        p.error("--no-gui and --batch require a bootable target or --big-picture")
    if args.test_config and any(
        (
            args.batch,
            args.no_gui,
            args.disc,
            args.game_args,
            args.state is not None,
            args.fast_boot,
            args.slow_boot,
            args.fullscreen,
            args.no_fullscreen,
            args.big_picture,
            args.debugger,
            args.turbo,
            args.unlimited,
        )
    ):
        p.error(
            "--test-config only accepts data-path, portable, log, and console options"
        )
    if args.setup_wizard and any((args.batch, args.no_gui, args.state is not None)):
        p.error("--setup-wizard is interactive")

    out = [args.exe]
    pairs = (
        (args.batch, "-batch"),
        (args.no_gui, "-nogui"),
        (args.portable, "-portable"),
    )
    out.extend(flag for enabled, flag in pairs if enabled)
    if args.data_path:
        out.extend(("-datapath", str(args.data_path)))
    if args.log_file:
        out.extend(("-logfile", str(args.log_file)))
    if args.elf:
        out.extend(("-elf", str(args.elf)))
    if args.game_args:
        out.extend(("-gameargs", args.game_args))
    if args.disc:
        out.extend(("-disc", str(args.disc)))
    if args.bios:
        out.append("-bios")
    if args.fast_boot:
        out.append("-fastboot")
    if args.slow_boot:
        out.append("-slowboot")
    if args.state is not None:
        out.extend(("-state", str(args.state)))
    if args.state_file:
        out.extend(("-statefile", str(args.state_file)))
    if args.fullscreen:
        out.append("-fullscreen")
    if args.no_fullscreen:
        out.append("-nofullscreen")
    if args.big_picture:
        out.append("-bigpicture")
    if args.early_console_log:
        out.append("-earlyconsolelog")
    if args.test_config:
        out.append("-testconfig")
    if args.setup_wizard:
        out.append("-setupwizard")
    if args.debugger:
        out.append("-debugger")
    if args.turbo:
        out.append("-turbo")
    if args.unlimited:
        out.append("-unlimited")
    if args.ra_integration:
        out.append("-raintegration")
    if args.boot:
        out.extend(("--", str(args.boot)))
    return out


def main() -> None:
    p = parser()
    print(shlex.join(build(p.parse_args(), p)))


if __name__ == "__main__":
    main()
