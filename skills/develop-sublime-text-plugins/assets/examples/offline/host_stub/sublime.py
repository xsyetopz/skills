"""Call-shape stub of Sublime Text's `sublime` module (offline tests only).

Signatures follow https://www.sublimetext.com/docs/api_reference.html for
the subset TodoLens uses. The buffer, selection, settings, and timer
models are the minimum needed to drive plugin code and record its calls.
Passing tests prove the plugin calls these names with these argument
shapes; they do not prove what the real editor does with them (drawing,
undo grouping, threading, command dispatch rules).
"""

from __future__ import annotations

import itertools
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple

Value = Any
CommandArgs = Optional[Dict[str, Value]]

# Backwards-compatible module constants (the API also has enum forms).
HOVER_TEXT = 1
HOVER_GUTTER = 2
HOVER_MARGIN = 3
DRAW_NO_FILL = 32
HIDDEN = 128
HIDE_ON_MOUSE_MOVE_AWAY = 8
LAYOUT_INLINE = 0
LAYOUT_BELOW = 1
LAYOUT_BLOCK = 2
OP_EQUAL = 0
OP_NOT_EQUAL = 1
OP_REGEX_MATCH = 2
OP_NOT_REGEX_MATCH = 3
OP_REGEX_CONTAINS = 4
OP_NOT_REGEX_CONTAINS = 5

calls: List[Tuple[str, tuple]] = []
_main_queue: List[Tuple[int, Callable[[], None]]] = []
_async_queue: List[Tuple[int, Callable[[], None]]] = []
_settings: Dict[str, Settings] = {}
_windows: List[Window] = []
_ids = itertools.count(1)


def reset() -> None:
    """Test helper: forget every call, timer, setting, and window."""
    calls.clear()
    _main_queue.clear()
    _async_queue.clear()
    _settings.clear()
    _windows.clear()


def _record(name: str, *args: object) -> None:
    calls.append((name, args))


def version() -> str:
    return "4200"


def set_timeout(callback: Callable[[], None], delay: int = 0) -> None:
    _record("set_timeout", callback, delay)
    _main_queue.append((delay, callback))


def set_timeout_async(callback: Callable[[], None], delay: int = 0) -> None:
    _record("set_timeout_async", callback, delay)
    _async_queue.append((delay, callback))


def run_async() -> int:
    """Test helper: run queued async callbacks in order; return the count."""
    ran = 0
    while _async_queue:
        _async_queue.pop(0)[1]()
        ran += 1
    return ran


def run_main() -> int:
    ran = 0
    while _main_queue:
        _main_queue.pop(0)[1]()
        ran += 1
    return ran


def status_message(msg: str) -> None:
    _record("status_message", msg)


def load_settings(base_name: str) -> Settings:
    # The API returns the same object for repeated calls with one name.
    _record("load_settings", base_name)
    if base_name not in _settings:
        _settings[base_name] = Settings()
    return _settings[base_name]


def save_settings(base_name: str) -> None:
    _record("save_settings", base_name)


def windows() -> List[Window]:
    return list(_windows)


def active_window() -> Window:
    if not _windows:
        _windows.append(Window())
    return _windows[0]


class Region:
    def __init__(self, a: int, b: Optional[int] = None) -> None:
        self.a = a
        self.b = a if b is None else b

    def __repr__(self) -> str:
        return "Region(%d, %d)" % (self.a, self.b)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Region) and (self.a, self.b) == (
            other.a,
            other.b,
        )

    def __hash__(self) -> int:
        return hash((self.a, self.b))

    def begin(self) -> int:
        return min(self.a, self.b)

    def end(self) -> int:
        return max(self.a, self.b)

    def empty(self) -> bool:
        return self.a == self.b

    def size(self) -> int:
        return self.end() - self.begin()

    def to_tuple(self) -> Tuple[int, int]:
        return (self.a, self.b)


class Edit:
    """Valid only while the TextCommand.run call that received it runs."""

    def __init__(self, view: View) -> None:
        self.view = view
        self.live = True


class Selection:
    def __init__(self) -> None:
        self._regions: List[Region] = []

    def __iter__(self) -> Iterator[Region]:
        return iter(list(self._regions))

    def __len__(self) -> int:
        return len(self._regions)

    def __getitem__(self, index: int) -> Region:
        return self._regions[index]

    def clear(self) -> None:
        self._regions = []

    def add(self, x: Region | int) -> None:
        region = x if isinstance(x, Region) else Region(x)
        # The real Selection merges overlaps; the stub only keeps order.
        self._regions.append(region)
        self._regions.sort(key=lambda r: (r.begin(), r.end()))


class Settings:
    def __init__(self, values: Optional[Dict[str, Value]] = None) -> None:
        self._values: Dict[str, Value] = dict(values or {})
        self._callbacks: List[Tuple[str, Callable[[], None]]] = []

    def get(self, key: str, default: Value = None) -> Value:
        return self._values.get(key, default)

    def has(self, key: str) -> bool:
        return key in self._values

    def set(self, key: str, value: Value) -> None:
        self._values[key] = value
        for _tag, callback in list(self._callbacks):
            callback()

    def erase(self, key: str) -> None:
        self._values.pop(key, None)

    def add_on_change(self, tag: str, callback: Callable[[], None]) -> None:
        _record("add_on_change", tag)
        self._callbacks.append((tag, callback))

    def clear_on_change(self, tag: str) -> None:
        _record("clear_on_change", tag)
        self._callbacks = [c for c in self._callbacks if c[0] != tag]

    def callback_count(self) -> int:
        """Test helper, not API."""
        return len(self._callbacks)


class Phantom:
    # Constructor order inferred from Phantom.to_tuple() and its attributes;
    # the fetched reference does not print the __init__ signature.
    def __init__(
        self,
        region: Region,
        content: str,
        layout: int,
        on_navigate: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.region = region
        self.content = content
        self.layout = layout
        self.on_navigate = on_navigate


class PhantomSet:
    def __init__(self, view: View, key: str = "") -> None:
        self.view = view
        self.key = key
        self.phantoms: List[Phantom] = []

    def update(self, phantoms: List[Phantom]) -> None:
        _record("PhantomSet.update", self.key, len(phantoms))
        self.phantoms = list(phantoms)


class View:
    def __init__(self, text: str = "", window: Optional[Window] = None):
        self._id = next(_ids)
        self._text = text
        self._change_count = 0
        self._valid = True
        self._read_only = False
        self._sel = Selection()
        self._settings = Settings()
        self._regions: Dict[str, List[Region]] = {}
        self._status: Dict[str, str] = {}
        self._window = window
        self.popups: List[str] = []
        self.annotations: List[str] = []

    def id(self) -> int:
        return self._id

    def is_valid(self) -> bool:
        return self._valid

    def close(self) -> bool:
        self._valid = False
        return True

    def window(self) -> Optional[Window]:
        return self._window

    def size(self) -> int:
        return len(self._text)

    def substr(self, x: Region | int) -> str:
        if isinstance(x, Region):
            return self._text[x.begin() : x.end()]
        return self._text[x : x + 1]

    def change_count(self) -> int:
        return self._change_count

    def settings(self) -> Settings:
        return self._settings

    def sel(self) -> Selection:
        return self._sel

    def is_read_only(self) -> bool:
        return self._read_only

    def set_read_only(self, read_only: bool) -> None:
        self._read_only = read_only

    def _edit(self, edit: Edit, begin: int, end: int, text: str) -> None:
        if not edit.live or edit.view is not self:
            raise ValueError("invalid Edit object")
        self._text = self._text[:begin] + text + self._text[end:]
        self._change_count += 1
        _record("View.edit", begin, end, text)

    def insert(self, edit: Edit, pt: int, text: str) -> int:
        self._edit(edit, pt, pt, text)
        return len(text)

    def erase(self, edit: Edit, region: Region) -> None:
        self._edit(edit, region.begin(), region.end(), "")

    def replace(self, edit: Edit, region: Region, text: str) -> None:
        self._edit(edit, region.begin(), region.end(), text)

    def user_types(self, text: str) -> None:
        """Test helper: simulate a user edit outside any command."""
        self._text += text
        self._change_count += 1

    def run_command(self, cmd: str, args: CommandArgs = None) -> None:
        from . import sublime_plugin

        _record("View.run_command", cmd, args)
        command = sublime_plugin.find_text_command(cmd)(self)
        edit = Edit(self)
        try:
            command.run(edit, **(args or {}))
        finally:
            edit.live = False

    def add_regions(
        self,
        key: str,
        regions: List[Region],
        scope: str = "",
        icon: str = "",
        flags: int = 0,
        annotations: Optional[List[str]] = None,
        annotation_color: str = "",
        on_navigate: Optional[Callable[[str], None]] = None,
        on_close: Optional[Callable[[], None]] = None,
    ) -> None:
        _record("View.add_regions", key, len(regions), scope, flags)
        self._regions[key] = list(regions)
        self.annotations = list(annotations or [])

    def get_regions(self, key: str) -> List[Region]:
        return list(self._regions.get(key, []))

    def erase_regions(self, key: str) -> None:
        _record("View.erase_regions", key)
        self._regions.pop(key, None)

    def set_status(self, key: str, value: str) -> None:
        self._status[key] = value

    def get_status(self, key: str) -> str:
        return self._status.get(key, "")

    def erase_status(self, key: str) -> None:
        self._status.pop(key, None)

    def show_popup(
        self,
        content: str,
        flags: int = 0,
        location: int = -1,
        max_width: float = 320,
        max_height: float = 240,
        on_navigate: Optional[Callable[[str], None]] = None,
        on_hide: Optional[Callable[[], None]] = None,
    ) -> None:
        _record("View.show_popup", flags, location, max_width)
        self.popups.append(content)

    def show_at_center(self, location: Region | int, animate: bool = True):
        _record("View.show_at_center", location)


class Window:
    def __init__(self) -> None:
        self._id = next(_ids)
        self._views: List[View] = []
        self.quick_panels: List[Tuple[List[str], Callable[[int], None]]] = []

    def id(self) -> int:
        return self._id

    def new_file(self, flags: int = 0, syntax: str = "") -> View:
        view = View(window=self)
        self._views.append(view)
        return view

    def views(self, *, include_transient: bool = False) -> List[View]:
        return [v for v in self._views if v.is_valid()]

    def active_view(self) -> Optional[View]:
        views = self.views()
        return views[-1] if views else None

    def show_quick_panel(
        self,
        items: List[str],
        on_select: Callable[[int], None],
        flags: int = 0,
        selected_index: int = -1,
        on_highlight: Optional[Callable[[int], None]] = None,
        placeholder: Optional[str] = None,
    ) -> None:
        _record("Window.show_quick_panel", list(items), flags)
        self.quick_panels.append((list(items), on_select))
