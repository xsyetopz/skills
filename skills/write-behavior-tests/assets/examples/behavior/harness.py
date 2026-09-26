"""Load subjects with the variant named by $VARIANT applied.

VARIANT unset or empty runs the reference implementation. Tests import
`impl` from here, never from subjects directly, so one test file can be
run against every variant without edits.
"""

from __future__ import annotations

import os
import types

import subjects
from variants import VARIANTS


def load() -> types.SimpleNamespace:
    name = os.environ.get("VARIANT", "")
    namespace = types.SimpleNamespace(**vars(subjects))
    if name:
        if name not in VARIANTS:
            raise SystemExit(f"unknown VARIANT {name!r}")
        for attribute, replacement in VARIANTS[name].items():
            setattr(namespace, attribute, replacement)
            if attribute == "DELIVERY_FEES":
                subjects.DELIVERY_FEES = replacement  # read by delivery_fee
    return namespace


impl = load()
