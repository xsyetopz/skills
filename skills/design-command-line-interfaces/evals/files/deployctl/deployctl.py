#!/usr/bin/env python3
"""deployctl: manage deployed apps (records live in apps.json)."""

import argparse
import json
import sys
from pathlib import Path

STORE = Path(__file__).with_name("apps.json")


def load():
    return json.loads(STORE.read_text())


def cmd_ls(args):
    print("\x1b[36mFetching apps...\x1b[0m")
    for app in load():
        print(f"{app['name']}\t{app['region']}")


def cmd_rm(args):
    apps = load()
    names = [a["name"] for a in apps]
    if args.app not in names:
        print(f"ERROR: {args.app} not found")
        return
    answer = input(f"Really delete {args.app}? ")
    if answer == "y":
        STORE.write_text(json.dumps([a for a in apps if a["name"] != args.app], indent=2))
        print("done")


def main():
    parser = argparse.ArgumentParser(prog="deployctl")
    parser.add_argument("--token", help="API token")
    parser.add_argument("--verbose", action="store_true")
    subs = parser.add_subparsers(dest="cmd")
    ls = subs.add_parser("ls", help="list apps")
    ls.set_defaults(run=cmd_ls)
    rm = subs.add_parser("rm", help="delete an app")
    rm.add_argument("app")
    rm.set_defaults(run=cmd_rm)
    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        return
    args.run(args)


if __name__ == "__main__":
    main()
