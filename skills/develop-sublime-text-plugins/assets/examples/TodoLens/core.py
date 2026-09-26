"""Pure TodoLens logic: no sublime imports, runs under any Python 3.8+.

Sublime Text loads every root-level .py file of a package as a plugin, so
this module is also imported by the plugin host; it defines no commands or
listeners and therefore registers nothing.
"""

import html
import re
from typing import (
    Callable,
    Dict,
    Iterable,
    List,
    NamedTuple,
    Optional,
    Sequence,
    Tuple,
)

DEFAULT_WORDS = ("TODO", "FIXME")
DISPLAYS = ("annotations", "phantoms", "none")
DEFAULT_DEBOUNCE_MS = 300
MAX_DEBOUNCE_MS = 5000
DONE_WORD = "DONE"
MAX_NOTE = 200

# sublime.QueryOperator values from the API reference (also OP_* names).
EQUAL = 0
NOT_EQUAL = 1
REGEX_MATCH = 2
NOT_REGEX_MATCH = 3
REGEX_CONTAINS = 4
NOT_REGEX_CONTAINS = 5

_WORD = re.compile(r"[A-Za-z]+\Z")


class Marker(NamedTuple):
    begin: int
    end: int
    word: str
    note: str


class Options(NamedTuple):
    enabled: bool
    words: Tuple[str, ...]
    display: str
    debounce_ms: int


class Snapshot(NamedTuple):
    view_id: int
    change_count: int
    generation: int


def read_options(get: Callable[[str, object], object]) -> Tuple[Options, List[str]]:
    """Validate raw setting values; return options plus one line per problem."""
    problems: List[str] = []
    enabled = get("enabled", True)
    if not isinstance(enabled, bool):
        problems.append("enabled must be true or false")
        enabled = True
    words = get("words", list(DEFAULT_WORDS))
    if not (
        isinstance(words, list)
        and words
        and all(isinstance(w, str) and _WORD.match(w) for w in words)
    ):
        problems.append("words must be a non-empty list of ASCII letters")
        words = list(DEFAULT_WORDS)
    display = get("display", "annotations")
    if display not in DISPLAYS:
        problems.append("display must be one of " + ", ".join(DISPLAYS))
        display = "annotations"
    debounce = get("debounce_ms", DEFAULT_DEBOUNCE_MS)
    if (
        isinstance(debounce, bool)
        or not isinstance(debounce, int)
        or not 0 <= debounce <= MAX_DEBOUNCE_MS
    ):
        problems.append("debounce_ms must be an integer 0..%d" % MAX_DEBOUNCE_MS)
        debounce = DEFAULT_DEBOUNCE_MS
    options = Options(enabled, tuple(words), str(display), debounce)
    return options, problems


def _pattern(words: Sequence[str]) -> "re.Pattern[str]":
    alternatives = "|".join(
        re.escape(w) for w in sorted(set(words), key=len, reverse=True)
    )
    return re.compile(r"\b(%s)\b" % alternatives)


def find_markers(text: str, words: Sequence[str]) -> List[Marker]:
    """Each marker word, with the text up to the next marker or line end."""
    if not words:
        return []
    hits = list(_pattern(words).finditer(text))
    markers: List[Marker] = []
    for index, hit in enumerate(hits):
        stop = len(text)
        for newline in ("\n", "\r"):
            found = text.find(newline, hit.end())
            if found != -1:
                stop = min(stop, found)
        if index + 1 < len(hits):
            stop = min(stop, hits[index + 1].start())
        note = text[hit.end() : stop].lstrip(":").strip()
        markers.append(Marker(hit.start(), hit.end(), hit.group(1), note))
    return markers


def marker_at(markers: Iterable[Marker], point: int) -> Optional[Marker]:
    for marker in markers:
        if marker.begin <= point <= marker.end:
            return marker
    return None


def touches(selection: Tuple[int, int], spans: Iterable[Tuple[int, int]]) -> bool:
    """True if the selection overlaps a span or its caret lies inside one."""
    low, high = min(selection), max(selection)
    for a, b in spans:
        begin, end = min(a, b), max(a, b)
        if low == high and begin <= low <= end:
            return True
        if low < end and begin < high:
            return True
    return False


def mark_done(text: str, words: Sequence[str]) -> str:
    """Replace every marker word in text with DONE; lengths may change."""
    if not words:
        return text
    return _pattern(words).sub(DONE_WORD, text)


def valid_note(text: str) -> bool:
    """A note is one line of at most MAX_NOTE characters."""
    return len(text) <= MAX_NOTE and "\n" not in text and "\r" not in text


def plan_edits(regions: Iterable[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """Normalize (a, b) pairs, drop empty ones, order them last to first.

    Replacing from the end of the buffer keeps the offsets of the regions
    not yet edited valid when a replacement changes the text length.
    """
    spans = {(min(a, b), max(a, b)) for a, b in regions if a != b}
    return sorted(spans, reverse=True)


def is_fresh(
    snapshot: Snapshot, *, valid: bool, change_count: int, current: bool
) -> bool:
    """A computed result may be published only for the unchanged view."""
    return valid and current and change_count == snapshot.change_count


class Generations:
    """Per-key request counters that a new load can never make current.

    Deferred callbacks capture this object, not the module global, so an
    importlib.reload that rebinds the global cannot revive old callbacks.
    """

    def __init__(self) -> None:
        self._latest: Dict[int, int] = {}
        self._closed = False

    def next(self, key: int) -> int:
        token = self._latest.get(key, 0) + 1
        self._latest[key] = token
        return token

    def is_current(self, key: int, token: int) -> bool:
        return not self._closed and self._latest.get(key) == token

    def forget(self, key: int) -> None:
        self._latest.pop(key, None)

    def close(self) -> None:
        self._closed = True


def _one(value: object, operator: int, operand: object) -> Optional[bool]:
    if operator == EQUAL:
        return value == operand
    if operator == NOT_EQUAL:
        return value != operand
    if not isinstance(operand, str):
        return None
    text = str(value)
    if operator == REGEX_MATCH:
        return re.fullmatch(operand, text) is not None
    if operator == NOT_REGEX_MATCH:
        return re.fullmatch(operand, text) is None
    if operator == REGEX_CONTAINS:
        return re.search(operand, text) is not None
    if operator == NOT_REGEX_CONTAINS:
        return re.search(operand, text) is None
    return None


def evaluate_context(
    values: Sequence[object], operator: int, operand: object, match_all: bool
) -> Optional[bool]:
    """Answer on_query_context for one value per selection.

    None means "not handled" to the host, which then treats the context
    as unknown; an unknown operator must not claim a match.
    """
    results = [_one(v, operator, operand) for v in values]
    if not results or any(r is None for r in results):
        return None
    return all(results) if match_all else any(results)


def annotation_html(marker: Marker) -> str:
    """minihtml for one annotation; untrusted text is always escaped."""
    return '<body id="todo-lens"><b>%s</b> %s</body>' % (
        html.escape(marker.word),
        html.escape(marker.note),
    )


def popup_html(marker: Marker) -> str:
    return (
        '<body id="todo-lens-popup"><style>p { margin: 0; }</style>'
        "<p><b>%s</b></p><p>%s</p></body>"
        % (html.escape(marker.word), html.escape(marker.note or "(no note)"))
    )


def status_text(markers: Sequence[Marker]) -> str:
    if not markers:
        return ""
    counts: Dict[str, int] = {}
    for marker in markers:
        counts[marker.word] = counts.get(marker.word, 0) + 1
    return " ".join("%s:%d" % item for item in sorted(counts.items()))


def quick_panel_items(markers: Sequence[Marker]) -> List[str]:
    return [m.word + ": " + (m.note or "(no note)") for m in markers]
