"""Health dashboard: polls every internal endpoint and returns the results."""

import client


def endpoints(n: int = 200) -> list[str]:
    return [f"http://svc-{i}.internal/health" for i in range(n)]


def poll_all(urls: list[str]) -> list[dict]:
    """Return one result per URL, in the same order as `urls`.

    Raises the error of the first failing URL.
    """
    results = []
    for url in urls:
        results.append(client.get(url))
    return results


if __name__ == "__main__":
    print(len(poll_all(endpoints())))
