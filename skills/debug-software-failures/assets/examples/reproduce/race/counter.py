"""Lost increment: read-modify-write on shared state without a lock.

`run(forced=True)` forces the bad interleaving with barriers, so the
failure reproduces on every run. `run(forced=False)` relies on timing, so it
reproduces only sometimes; measure its rate instead of trusting one run.
"""

from __future__ import annotations

import sys
import threading


def run(forced: bool, locked: bool = False) -> int:
    total = [0]
    lock = threading.Lock()
    both_read = threading.Barrier(2) if forced else None

    def increment() -> None:
        if locked:
            with lock:
                total[0] += 1
            return
        value = total[0]  # read
        if both_read:
            both_read.wait()  # both threads have read the old value
        total[0] = value + 1  # write

    threads = [threading.Thread(target=increment) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return total[0]


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "forced":
        sys.exit(0 if run(forced=True) == 2 else 1)
    if mode == "fixed":
        sys.exit(0 if run(forced=False, locked=True) == 2 else 1)
    runs = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    failures = sum(run(forced=False) != 2 for _ in range(runs))
    print(f"unforced failures: {failures}/{runs}")
