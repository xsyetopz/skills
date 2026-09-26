"""User preferences stored as JSON, one file per user."""
import json

DEFAULTS = {"theme": "light", "compact": False, "page_size": 50}


def load(path):
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    prefs = {**DEFAULTS, **{k: v for k, v in raw.items() if k in DEFAULTS}}
    # legacy_mode was the pre-2023 name for compact; nothing writes it anymore.
    if "legacy_mode" in raw and "compact" not in raw:
        prefs["compact"] = bool(raw["legacy_mode"])
    return prefs


def save(path, prefs):
    with open(path, "w", encoding="utf-8") as f:
        json.dump({k: prefs[k] for k in DEFAULTS}, f, indent=2, sort_keys=True)
