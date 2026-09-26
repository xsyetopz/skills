"""Config loader with accumulated compatibility code (the "before" state)."""

import sys
import warnings

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11 only
    import tomli as tomllib  # type: ignore[no-redef]

# Settings written before 1.3 used "timeout"; saved files still contain it.
_LEGACY_KEYS = {"timeout": "timeout_s"}

if sys.version_info < (3, 11):

    def _read(path: str) -> dict:
        with open(path, "rb") as handle:
            return tomllib.load(handle)

else:

    def _read(path: str) -> dict:
        with open(path, "rb") as handle:
            return tomllib.load(handle)


def load(path: str) -> dict:
    raw = _read(path)
    return {_LEGACY_KEYS.get(key, key): value for key, value in raw.items()}


def load_config(path: str) -> dict:
    """Deprecated in 1.2 (CHANGELOG): use load(); removal planned for 2.0."""
    warnings.warn(
        "load_config is deprecated; use load", DeprecationWarning, stacklevel=2
    )
    return load(path)
