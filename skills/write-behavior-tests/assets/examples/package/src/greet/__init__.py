"""Greets in a language listed in greetings.json (shipped with the package)."""

import json
from importlib import resources


def greet(name: str, language: str = "en") -> str:
    table = json.loads(
        resources.files("greet").joinpath("greetings.json").read_text("utf-8")
    )
    return f"{table[language]}, {name}!"
