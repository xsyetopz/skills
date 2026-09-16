"""Move an ordinary file to an absent sibling in a caller-owned directory.

The caller excludes concurrent changes to both paths. This example is not an
atomic no-clobber primitive against hostile/concurrent filesystem writers and
does not claim cross-filesystem moves. Existing destinations (including dangling
symlinks) must not be replaced. The result is the destination Path.
"""

import os
from pathlib import Path


def rename_file(source: Path, destination: Path) -> Path:
    """Preserve contents while moving source to a new sibling name."""
    if source.parent.resolve() != destination.parent.resolve():
        raise ValueError("source and destination must be siblings")
    if not source.is_file() or source.is_symlink():
        raise FileNotFoundError(source)
    if os.path.lexists(destination):
        raise FileExistsError(destination)
    return source.rename(destination)
