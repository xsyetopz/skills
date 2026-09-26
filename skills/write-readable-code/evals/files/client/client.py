import json
import urllib.request

from .util import *


def fetch_status(url, timeout=None, retries=None):
    """Fetch a JSON status document; timeout in seconds, 0 means non-blocking check."""
    timeout = timeout or 30
    retries = retries or 3
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read()
        data = json.loads(body)
        return normalise(data["status"])
    except Exception:
        return None
