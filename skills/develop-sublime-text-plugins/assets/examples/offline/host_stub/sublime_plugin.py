"""Call-shape stub of Sublime Text's `sublime_plugin` module.

Class and method names follow the API reference. Command.name() applies
the naming rule documented for plugins (drop the Command suffix, split
CamelCase words with underscores, lower-case). Build 4213 changed the
host's snake-casing of some class names, so this stub cannot stand in
for the host for names with consecutive capitals.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Type

from . import sublime


def snake_name(class_name: str, suffix: str) -> str:
    if class_name.endswith(suffix):
        class_name = class_name[: -len(suffix)]
    return re.sub(r"(?<!^)(?=[A-Z])", "_", class_name).lower()


class Command:
    def name(self) -> str:
        return snake_name(type(self).__name__, "Command")

    def is_enabled(self, **kwargs: Any) -> bool:
        return True

    def is_visible(self, **kwargs: Any) -> bool:
        return True

    def is_checked(self, **kwargs: Any) -> bool:
        return False

    def input(self, args: Dict[str, Any]) -> Optional[CommandInputHandler]:
        return None


class ApplicationCommand(Command):
    def run(self, **kwargs: Any) -> None:
        pass


class WindowCommand(Command):
    def __init__(self, window: sublime.Window) -> None:
        self.window = window

    def run(self, **kwargs: Any) -> None:
        pass


class TextCommand(Command):
    def __init__(self, view: sublime.View) -> None:
        self.view = view

    def run(self, edit: sublime.Edit, **kwargs: Any) -> None:
        pass


class EventListener:
    pass


class ViewEventListener:
    def __init__(self, view: sublime.View) -> None:
        self.view = view

    @classmethod
    def is_applicable(cls, settings: sublime.Settings) -> bool:
        return True


class CommandInputHandler:
    def name(self) -> str:
        return snake_name(type(self).__name__, "InputHandler")

    def placeholder(self) -> str:
        return ""

    def validate(self, text: str) -> bool:
        return True

    def next_input(self, args: Dict[str, Any]) -> Optional[CommandInputHandler]:
        return None


class TextInputHandler(CommandInputHandler):
    pass


class ListInputHandler(CommandInputHandler):
    def list_items(self) -> List[Any]:
        return []


def _subclasses(base: type) -> List[type]:
    found = []
    for sub in base.__subclasses__():
        found.append(sub)
        found.extend(_subclasses(sub))
    return found


def find_text_command(name: str) -> Type[TextCommand]:
    """Test helper: the newest TextCommand subclass whose name() matches."""
    for cls in reversed(_subclasses(TextCommand)):
        if snake_name(cls.__name__, "Command") == name:
            return cls
    raise KeyError(name)
