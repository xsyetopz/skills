"""Run pre-commit-hooks file checks over the repository's files.

The checks match pre-commit-hooks' large-file, private-key, case-conflict,
symlink, and shebang hooks. lefthook and `just` drive this repository's
hooks, so this script selects the files that pre-commit would pass to each.
The executable bit is read from the worktree, so `chmod +x` counts before
it is staged; the pre-commit hook requires a clean worktree anyway.
"""

import os
import shlex
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from pre_commit_hooks import (
    check_added_large_files,
    check_case_conflict,
    check_executables_have_shebangs,
    check_symlinks,
    destroyed_symlinks,
    detect_private_key,
)
from pre_commit_hooks.check_executables_have_shebangs import has_shebang

# pre-commit-hooks' default for check-added-large-files.
MAX_KB = "500"


def worktree_files() -> list[str]:
    listing = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        capture_output=True,
        check=True,
    ).stdout.decode()
    # A file deleted in the worktree but still in the index has nothing to check.
    return sorted({p for p in listing.split("\0") if p and os.path.lexists(p)})


def shebang_scripts_are_executable(paths: Sequence[str]) -> int:
    missing = [p for p in paths if has_shebang(p) and not os.access(p, os.X_OK)]
    for path in missing:
        print(
            f"{path}: has a shebang but is not executable; run "
            f"`chmod +x {shlex.quote(path)}` or remove the shebang",
            file=sys.stderr,
        )
    return int(bool(missing))


def main() -> int:
    files = worktree_files()
    symlinks = [p for p in files if Path(p).is_symlink()]
    regular = [p for p in files if Path(p).is_file() and p not in symlinks]
    executable = [p for p in regular if os.access(p, os.X_OK)]
    checks: list[tuple[Callable[[Sequence[str]], int], list[str], list[str]]] = [
        (check_added_large_files.main, ["--enforce-all", "--maxkb", MAX_KB], regular),
        (detect_private_key.main, [], regular),
        (check_case_conflict.main, [], files),
        (check_symlinks.main, [], symlinks),
        (destroyed_symlinks.main, [], regular),
        (check_executables_have_shebangs.main, [], executable),
        (shebang_scripts_are_executable, [], regular),
    ]
    status = 0
    for check, flags, paths in checks:
        if paths:
            status |= check([*flags, *paths])
    return status


if __name__ == "__main__":
    sys.exit(main())
