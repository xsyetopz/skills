"""Writes ticks as JSON lines for the risk team."""

import json


def to_jsonl(ticks):
    return "\n".join(json.dumps(vars(t), sort_keys=True) for t in ticks)
