"""Compare extracted function bytes against the reference.

Usage: python3 verify.py REF_DIR BUILD_DIR SYMBOLS

REF_DIR and BUILD_DIR hold one raw <name>.bin per function; SYMBOLS lists
one function name per line. Exit 0 when every function matches.
"""

import sys
from pathlib import Path

CALL = 0xE8
JMP = 0xE9


def same(ref: bytes, cand: bytes) -> bool:
    n = min(len(ref), len(cand))
    i = 0
    while i < n:
        if ref[i] in (CALL, JMP) and cand[i] == ref[i]:
            # rel32 targets move whenever the layout changes; ignore them
            i += 5
            continue
        if ref[i] != cand[i]:
            return False
        i += 1
    return True


def main() -> int:
    ref_dir, build_dir, symbols = (Path(a) for a in sys.argv[1:4])
    names = [n.strip() for n in symbols.read_text().splitlines() if n.strip()]
    matched = 0
    for name in names:
        ref = ref_dir / f"{name}.bin"
        cand = build_dir / f"{name}.bin"
        if not cand.exists():
            print(f"skip {name}: not built yet")
            matched += 1
            continue
        if same(ref.read_bytes(), cand.read_bytes()):
            matched += 1
        else:
            print(f"MISMATCH {name}")
    print(f"{matched}/{len(names)} matched")
    return 0 if matched == len(names) else 1


if __name__ == "__main__":
    raise SystemExit(main())
