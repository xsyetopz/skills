"""Two threads take two locks in opposite order and hang forever.

faulthandler.dump_traceback_later prints every thread's stack after the
timeout and exits, which turns "it hangs" into "thread A waits for lock_b
at line N while thread B waits for lock_a at line M".
"""

import faulthandler
import sys
import threading

lock_a = threading.Lock()
lock_b = threading.Lock()
both_hold_one = threading.Barrier(2)


def transfer_a_to_b() -> None:
    with lock_a:
        both_hold_one.wait()
        with lock_b:  # waits for transfer_b_to_a to release lock_b
            pass


def transfer_b_to_a() -> None:
    with lock_b:
        both_hold_one.wait()
        with lock_a:  # waits for transfer_a_to_b to release lock_a
            pass


if __name__ == "__main__":
    faulthandler.dump_traceback_later(float(sys.argv[1]), exit=True)
    threads = [
        threading.Thread(target=transfer_a_to_b, daemon=True),
        threading.Thread(target=transfer_b_to_a, daemon=True),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
