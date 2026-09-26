"""defusedxml refuses entity declarations (CWE-611, CWE-776).

Run: uv run --no-project --with defusedxml python defused_xml.py
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from importlib.metadata import version

import defusedxml  # pyright: ignore[reportMissingModuleSource]
import defusedxml.ElementTree as DET  # pyright: ignore[reportMissingModuleSource]

DOC = "<?xml version='1.0'?><!DOCTYPE r [<!ENTITY e 'expanded'>]><r>&e;</r>"


def main() -> int:
    print("stdlib ElementTree text:", ET.fromstring(DOC).text)
    try:
        DET.fromstring(DOC)
    except defusedxml.EntitiesForbidden as error:
        print("defusedxml refused:", type(error).__name__)
    else:
        print("FAIL defusedxml accepted an entity declaration")
        return 1
    try:
        DET.fromstring(DOC, forbid_dtd=True)
    except defusedxml.DTDForbidden as error:
        print("forbid_dtd=True refused:", type(error).__name__)
    else:
        print("FAIL forbid_dtd accepted a DTD")
        return 1
    print("plain document:", DET.fromstring("<r>ok</r>").text)
    print("defusedxml", version("defusedxml"), "PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
