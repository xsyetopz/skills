"""Load application configuration from TOML files."""
import sys
import warnings

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib

try:
    from functools import cache
except ImportError:  # Python < 3.9
    from functools import lru_cache

    cache = lru_cache(maxsize=None)

if sys.version_info >= (3, 10):
    from itertools import pairwise
else:  # pragma: no cover

    def pairwise(iterable):
        items = list(iterable)
        return zip(items, items[1:])


DEFAULTS = {"timeout": 30, "retries": 3}


def load_config(path):
    """Return the config in PATH merged over DEFAULTS."""
    with open(path, "rb") as f:
        data = tomllib.load(f)
    if "timeout_s" in data and "timeout" not in data:
        data["timeout"] = data.pop("timeout_s")  # files saved by 2.x
    return {**DEFAULTS, **data}


def load_settings(path):
    """Deprecated alias for load_config()."""
    warnings.warn("load_settings() is deprecated; use load_config()", DeprecationWarning, stacklevel=2)
    return load_config(path)


@cache
def backoff_schedule(retries):
    """Delays in seconds between retries: 1, 2, 4, ..."""
    return tuple(2**i for i in range(retries))


def gaps(schedule):
    return [b - a for a, b in pairwise(schedule)]
