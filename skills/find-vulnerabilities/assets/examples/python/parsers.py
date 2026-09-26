"""Parser pairs: pickle, restricted unpickling, and XML entities.

``vulnerable_*`` functions are INTENTIONALLY VULNERABLE. The pickle payload
in the tests calls ``record_call`` below, a harmless recorder, to prove that
loading data can invoke an arbitrary callable.
"""

from __future__ import annotations

import builtins
import io
import json
import pickle
import xml.parsers.expat
import xml.sax
import xml.sax.handler

CALLS: list[str] = []


def record_call(label: str) -> str:
    CALLS.append(label)
    return label


# --- Unsafe deserialization (CWE-502) ---------------------------------------


def vulnerable_load_session(blob: bytes) -> object:
    # INTENTIONALLY VULNERABLE (CWE-502): pickle imports and calls any
    # global named in the stream.
    return pickle.loads(blob)


def fixed_load_session(blob: bytes) -> dict:
    data = json.loads(blob)
    if not isinstance(data, dict):
        raise ValueError("session must be a JSON object")
    return data


SAFE_GLOBALS = {("builtins", "set"), ("builtins", "frozenset")}


class RestrictedUnpickler(pickle.Unpickler):
    def find_class(self, module: str, name: str) -> type:
        if (module, name) in SAFE_GLOBALS:
            return getattr(builtins, name)
        raise pickle.UnpicklingError(f"global {module}.{name} is forbidden")


def restricted_load(blob: bytes) -> object:
    return RestrictedUnpickler(io.BytesIO(blob)).load()


# --- XML external entities (CWE-611) ----------------------------------------


class _Text(xml.sax.handler.ContentHandler):
    def __init__(self) -> None:
        super().__init__()
        self.text = ""

    def characters(self, content: str) -> None:
        self.text += content


def _sax_text(document: str, external_entities: bool) -> str:
    handler = _Text()
    parser = xml.sax.make_parser()
    parser.setContentHandler(handler)
    parser.setFeature(xml.sax.handler.feature_external_ges, external_entities)
    parser.parse(io.StringIO(document))
    return handler.text


def vulnerable_sax_text(document: str) -> str:
    # INTENTIONALLY VULNERABLE (CWE-611): external general entities are
    # opt-in since Python 3.7.1; enabling them lets the document read files.
    return _sax_text(document, external_entities=True)


def fixed_sax_text(document: str) -> str:
    return _sax_text(document, external_entities=False)


# --- Reject DTDs outright (CWE-611, CWE-776) --------------------------------


def no_dtd_text(document: str) -> str:
    """Parse with expat but refuse any DOCTYPE, like Java's
    disallow-doctype-decl feature."""
    parts: list[str] = []

    def refuse_doctype(*_args: object) -> None:
        raise ValueError("DOCTYPE is not allowed")

    parser = xml.parsers.expat.ParserCreate()
    parser.StartDoctypeDeclHandler = refuse_doctype
    parser.CharacterDataHandler = parts.append
    parser.Parse(document, True)
    return "".join(parts)
