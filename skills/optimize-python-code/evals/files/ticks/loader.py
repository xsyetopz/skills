"""Loads a day of ticks into memory. Production days hold ~5 million rows."""

import csv
import io

from model import Tick


def load(rows):
    return [Tick(int(ts), float(px), int(qty)) for ts, px, qty in rows]


def load_csv(text):
    return load(csv.reader(io.StringIO(text)))
