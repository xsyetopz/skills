"""Allocation comparison: peak traced bytes for one call on 1 MB of text."""

import tracemalloc

from counter import count_delimiters, count_delimiters_split

TEXT = "field," * 200_000


def peak_bytes(function) -> int:
    tracemalloc.start()
    function(TEXT, ",")
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    return peak


split_peak = peak_bytes(count_delimiters_split)
count_peak = peak_bytes(count_delimiters)
print(f"split peak={split_peak} B, count peak={count_peak} B")
if count_peak >= split_peak:
    raise SystemExit("candidate does not allocate less")
