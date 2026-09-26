"""One module: imports, constants and __all__, classes, then functions."""

from __future__ import annotations

import json
from dataclasses import dataclass

# Third-party imports go here, then a blank line, then project imports.

PUBLIC_CONSTANT = 1
_PRIVATE_CONSTANT = 2

__all__ = ["PUBLIC_CONSTANT", "PublicType", "public_function"]


@dataclass
class PublicType:
    state: int = _PRIVATE_CONSTANT

    def public_method(self) -> str:
        return self._render()

    def _render(self) -> str:
        return json.dumps({"state": self.state})


class _PrivateType:
    pass


def public_function() -> PublicType:
    return PublicType(state=_private_helper())


def _private_helper() -> int:
    return PUBLIC_CONSTANT
