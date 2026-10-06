# Python

Privacy is a convention, so the module defines the real API boundary.
A name starting with `_` is private.
Everything else is public, and `__all__` lists the public names when the module's API is explicit.
Use a single underscore.
Use a double underscore only to avoid a name clash with a subclass.

## Order in a file

1. Module docstring.
1. `from __future__` imports, if any.
1. `__all__` and other dunder names (PEP 8 puts them before the imports).
1. Imports: standard library, third party, local, as the formatter groups them.
1. Constants.
1. Classes, each with its methods: `__init__`, public methods, then `_private` methods.
1. Public functions.
1. Private functions and classes, used by the code above.

Python 3.14 evaluates annotations lazily,
so forward references need no `from __future__ import annotations` and no quotes.
Import types used only in annotations normally,
or under `TYPE_CHECKING` for an import cycle.
Tests go in a top-level `tests/` directory as `test_<module>.py`,
importing the public names.

```python
"""One-line summary of the component."""

__all__ = ["PUBLIC_CONSTANT", "PublicType", "public_function"]

import logging
from collections.abc import Sequence

from third_party import dependency

from project import local

PUBLIC_CONSTANT = 1
_PRIVATE_CONSTANT = 2

_log = logging.getLogger(__name__)


class PublicType:
    def __init__(self, values: Sequence[int]) -> None:
        self._state = _PRIVATE_CONSTANT
        self._values = values

    def public_method(self) -> int:
        return self._internal_method()

    def _internal_method(self) -> int:
        return _private_helper(self._values, self._state)


def public_function(item: PublicType) -> int:
    return item.public_method()


class _PrivateType:
    pass


def _private_helper(values: Sequence[int], state: int) -> int:
    _log.debug("helper %s", dependency.name(local.VALUE))
    return state + sum(values)
```
