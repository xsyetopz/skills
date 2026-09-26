"""YAML loading pair (needs PyYAML; the test skips without it).

``vulnerable_load`` is INTENTIONALLY VULNERABLE (CWE-502): UnsafeLoader
constructs arbitrary Python objects from ``!!python/...`` tags.
"""

from __future__ import annotations

import yaml


def vulnerable_load(text: str) -> object:
    # INTENTIONALLY VULNERABLE (CWE-502).
    return yaml.load(text, Loader=yaml.UnsafeLoader)


def fixed_load(text: str) -> object:
    return yaml.safe_load(text)
