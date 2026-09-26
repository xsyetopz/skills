"""Print one setting: python3 -m app.cli FILE SECTION KEY."""

import sys

from app.settings import load_file


def main(argv: list[str]) -> int:
    path, section, key = argv
    print(load_file(path)[section][key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
