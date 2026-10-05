"""Reads a JSON list of flat objects on stdin and writes it in another format."""

import argparse
import json
import sys

from exporters import export_json

FORMATS = {"json": export_json}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--format", choices=sorted(FORMATS), default="json")
    args = parser.parse_args()
    sys.stdout.write(FORMATS[args.format](json.load(sys.stdin)))


if __name__ == "__main__":
    main()
