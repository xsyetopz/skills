"""Import TodoLens against the host stub, with the $VARIANT mutant applied.

Tests import `load` from here and never import TodoLens directly, so one
suite runs unchanged against the reference and against every mutant in
variants.py. VARIANT unset or empty means the reference implementation.
"""

import importlib
import os
import sys
import types
from pathlib import Path
from typing import Tuple

sys.dont_write_bytecode = True  # keep __pycache__ out of the skill tree
HERE = Path(__file__).resolve().parent
for path in (str(HERE.parent), str(HERE)):
    if path not in sys.path:
        sys.path.insert(0, path)

from host_stub import sublime, sublime_plugin  # noqa: E402
from variants import VARIANTS  # noqa: E402

sys.modules["sublime"] = sublime
sys.modules["sublime_plugin"] = sublime_plugin


def apply_variant(core: types.ModuleType, plugin: types.ModuleType) -> None:
    name = os.environ.get("VARIANT", "")
    if not name:
        return
    if name not in VARIANTS:
        raise SystemExit("unknown VARIANT %r" % name)
    VARIANTS[name].mutate(core, plugin)


def load() -> Tuple[types.ModuleType, types.ModuleType]:
    """Fresh stub state and freshly executed core and plugin modules."""
    sublime.reset()
    core = importlib.reload(importlib.import_module("TodoLens.core"))
    plugin = importlib.reload(importlib.import_module("TodoLens.plugin"))
    apply_variant(core, plugin)
    return core, plugin


def reload_plugin(core: types.ModuleType) -> types.ModuleType:
    """Re-execute plugin.py in place, as the host does on package reload."""
    plugin = importlib.reload(sys.modules["TodoLens.plugin"])
    apply_variant(core, plugin)
    return plugin
