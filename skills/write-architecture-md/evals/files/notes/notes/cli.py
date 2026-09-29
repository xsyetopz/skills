"""Command-line entry point: parses arguments and calls storage and render."""

import argparse
from pathlib import Path

from notes import render, storage


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="notes")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("add").add_argument("text")
    sub.add_parser("list")
    sub.add_parser("export").add_argument("out", type=Path)
    args = parser.parse_args(argv)
    path = storage.default_path()
    notes = storage.load(path)
    if args.command == "add":
        notes.append({"text": args.text})
        storage.save(path, notes)
    elif args.command == "list":
        for number, note in enumerate(notes, 1):
            print(number, note["text"])
    else:
        args.out.write_text(render.to_html(notes), encoding="utf-8")
    return 0
