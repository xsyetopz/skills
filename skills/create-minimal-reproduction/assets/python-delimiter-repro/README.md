# Delimiter parsing reproduction

This artifact reproduces a parser failure when a text field contains the
protocol delimiter.

## Prerequisites

- Python 3.10 or newer

Verified with Python 3.14.7 on macOS 26.6.2 arm64.

## Run

Run `python3 repro.py` from this directory.

Input: `42|start|stop`

Expected: parse message ID `42` and text `start|stop`.

Actual on the tested environment: the process exits nonzero with
`ValueError: too many values to unpack (expected 2, got 3)`.

## Verify

Run `python3 verify.py`. The verifier exits zero only when `repro.py` produces
the documented `ValueError` failure.
