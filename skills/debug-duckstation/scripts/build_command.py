"""Build, but never execute, a DuckStation launch command for a release binary.

Flags are those printed by `DuckStation -help` in official release v0.1-11826.
Pass --help-file with the -help output (stderr) of the binary you will run to
reject any emitted flag that binary does not list.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
from pathlib import Path

EPILOG = """\
Exit status:
  0  the command line was printed (nothing is executed)
  2  usage error: conflicting or incomplete switches, a NUL in an argument,
     an unreadable --help-file, or a flag the --help-file does not list

Output: a JSON array of argv strings (--format argv, the default), or one
POSIX-shell-quoted line (--format posix).

Examples:
  python3 scripts/build_command.py --exe ./DuckStation.AppImage --boot game.cue \\
    --batch
  python3 scripts/build_command.py --exe duckstation-qt --boot game.cue \\
    --help-file duckstation-help.txt --format posix
"""


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=__doc__,
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--format",
        choices=("argv", "posix"),
        default="argv",
        help="argv: JSON array (default); posix: POSIX shell only, not PowerShell/cmd",
    )
    p.add_argument(
        "--native",
        nargs=argparse.REMAINDER,
        help="complete native argv after --exe; cannot combine with convenience switches",
    )
    p.add_argument("--exe", required=True, help="DuckStation executable path")
    p.add_argument(
        "--help-file",
        type=Path,
        help="saved '-help' output of the target binary; emitted flags must appear",
    )

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


def listed_flags(help_text: str) -> set[str]:
    return set(re.findall(r"^\s+(-[a-z]+)\b", help_text, flags=re.MULTILINE))


def unlisted_flags(argv: list[str], help_text: str) -> list[str]:
    listed = listed_flags(help_text)
    options = argv[1 : argv.index("--")] if "--" in argv else argv[1:]
    return [a for a in options if a.startswith("-") and a not in listed]


def main() -> None:
    p = parser()
    args = p.parse_args()
    if not args.exe or "\0" in args.exe:
        p.error("--exe must be a nonempty path without NUL")
    if args.native is not None:
        controls = {
            key: value
            for key, value in vars(args).items()
            if key not in {"exe", "format", "native", "help_file"}
            and value is not None
            and value is not False
        }
        if controls:
            p.error(
                "--native supplies the complete native argument list; do not mix convenience switches"
            )
        out = [args.exe, *args.native]
    else:
        out = build(args, p)
    if any("\0" in item for item in out):
        p.error("arguments cannot contain NUL")
    if args.help_file is not None:
        try:
            listed = args.help_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            p.error(f"cannot read --help-file {args.help_file}: {error}")
        missing = unlisted_flags(out, listed)
        if missing:
            p.error(f"flags not listed in {args.help_file}: {' '.join(missing)}")
    print(
        json.dumps(out, ensure_ascii=False)
        if args.format == "argv"
        else shlex.join(out)
    )


if __name__ == "__main__":
    main()
