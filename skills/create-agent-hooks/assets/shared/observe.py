#!/usr/bin/env python3
"""Session-start transport fixture only: no policy, logging, network, or file writes.

Accept one UTF-8 JSON object on stdin (at most 1 MiB). Emit one neutral JSON object.
Unknown event fields are preserved by not interpreting them. This checks transport,
not the provider's full schema or whether a host has loaded the hook.
"""

import json
import sys

LIMIT = 1024 * 1024


def main() -> int:
    try:
        raw = sys.stdin.buffer.read(LIMIT + 1)
        if len(raw) > LIMIT:
            raise ValueError("input exceeds 1 MiB")
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("expected a JSON object")
    except (ValueError, UnicodeError) as exc:
        print(f"invalid hook input: {exc}", file=sys.stderr)
        return 1
    print("{}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
