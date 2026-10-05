"""Unit conversion helpers."""

import warnings

# Config files saved by 1.x still use "timeout".
_LEGACY_KEYS = {"timeout": "timeout_s"}


def to_seconds(ms: float) -> float:
    return ms / 1000


def ms_to_s(ms: float) -> float:
    """Deprecated in 1.5.0; use to_seconds."""
    warnings.warn("ms_to_s is deprecated; use to_seconds", DeprecationWarning, stacklevel=2)
    return to_seconds(ms)


def secs(ms: float) -> float:
    """Deprecated in 1.6.0; use to_seconds."""
    warnings.warn("secs is deprecated; use to_seconds", DeprecationWarning, stacklevel=2)
    return to_seconds(ms)


def load_config(raw: dict) -> dict:
    return {_LEGACY_KEYS.get(key, key): value for key, value in raw.items()}
