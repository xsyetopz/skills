"""Entry point: python3 -m shortlinks --db links.db --port 8080."""

import argparse

from shortlinks.http import make_server
from shortlinks.store import LinkStore


def main() -> None:
    parser = argparse.ArgumentParser(prog="shortlinks")
    parser.add_argument("--db", default="links.db")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    make_server(LinkStore(args.db), args.port).serve_forever()


if __name__ == "__main__":
    main()
