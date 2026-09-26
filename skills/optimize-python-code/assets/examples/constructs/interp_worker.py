"""Worker for InterpreterPoolExecutor: its import graph must load in a
subinterpreter, so it imports nothing beyond what the task needs (for
example, importing tracemalloc there raises ImportError on CPython 3.14.7).
"""

import sys


def interpreter_task(n: int) -> tuple[int, int]:
    if sys.version_info < (3, 14):
        raise RuntimeError("concurrent.interpreters requires Python 3.14+")
    from concurrent import interpreters

    total = 0
    for i in range(n):
        total += i * i % 7
    return total, interpreters.get_current().id
