"""Third-party replay plugin (vendored, do not edit): tags replayed ticks."""


def tag_replay(ticks):
    for tick in ticks:
        tick.source = "replay"
    return ticks
