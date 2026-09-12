#!/usr/bin/env python3
"""Harmless hook handler: validate one stdin JSON object and return JSON."""

import json
import sys


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        print(f"invalid hook input: {error}", file=sys.stderr)
        return 1
    if not isinstance(payload, dict):
        print("invalid hook input: expected a JSON object", file=sys.stderr)
        return 1
    json.dump({}, sys.stdout, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
