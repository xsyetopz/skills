"""Tiny notes store."""

NOTES: dict[str, list[str]] = {}


def add_note(usr: str, text: str) -> int:
    NOTES.setdefault(usr, []).append(text)
    return len(NOTES[usr])


def list_notes(usr: str) -> list[str]:
    return list(NOTES.get(usr, []))
