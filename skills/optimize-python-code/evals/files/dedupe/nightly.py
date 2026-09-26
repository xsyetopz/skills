"""Stand-in for the nightly job: streams events and de-duplicates them."""

from __future__ import annotations

import random

from events import Event, dedupe_events


def stream(n: int, seed: int = 7):
    rng = random.Random(seed)
    for _ in range(n):
        yield Event(rng.randrange(n // 2), rng.choice(["open", "close", "edit"]), rng.randrange(1000))


def main() -> None:
    blocked = list(range(0, 20_000, 3))
    kept = dedupe_events(stream(20_000), blocked)
    print(len(kept))


if __name__ == "__main__":
    main()
