# ruff: noqa: F403, F405, BLE001, SIM105 -- deliberate findings
"""Scanner fixture: one finding of each kind zen_scan.py reports.

Not imported by the examples; verify.sh expects exactly 5 findings here
and 0 in the other modules.
"""

import json
from contextlib import suppress
from os.path import *  # star-import


def timeout_seconds(value, default=30.0):
    return value or default  # or-default: 0 becomes 30.0


def load(path):
    try:
        with open(path) as handle:
            return json.load(handle)
    except Exception:  # broad-except
        return {}


def cleanup(path):
    try:
        remove_file(path)
    except OSError:  # silenced-except
        pass


def remove_file(path):
    with suppress(OSError):  # wide-suppress: two statements
        print("removing", basename(path))
        __import__("os").remove(path)
