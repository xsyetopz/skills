"""Load the service's settings file (INI-like, hand-rolled parser)."""


def load(text: str) -> dict[str, dict[str, str]]:
    sections: dict[str, dict[str, str]] = {}
    current: dict[str, str] | None = None
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            current = sections.setdefault(line[1:-1].strip(), {})
            continue
        if current is None:
            raise ValueError(f"key outside a section: {line!r}")
        key, sep, value = line.partition("=")
        if not sep:
            raise ValueError(f"missing '=': {line!r}")
        current[key.strip()] = value.strip()
    return sections


def load_file(path: str) -> dict[str, dict[str, str]]:
    with open(path, encoding="utf-8") as handle:
        return load(handle.read())
