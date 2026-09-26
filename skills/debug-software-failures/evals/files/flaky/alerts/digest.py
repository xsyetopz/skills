"""Build the hourly alert digest e-mailed to the on-call engineer."""

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class Alert:
    at: datetime
    service: str
    category: str
    message: str


def _categories(alerts: list[Alert]) -> list[str]:
    return list({alert.category for alert in alerts})


def digest(alerts: list[Alert], now: datetime | None = None) -> str:
    """Summarise alerts: a header, then one line per category.

    Categories are listed in the order they first appear in `alerts`, and
    each line counts that category's alerts and names its services.
    """
    now = now or datetime.now(timezone.utc)
    lines = [f"Alert digest {now:%Y-%m-%d %H:00} UTC: {len(alerts)} alerts"]
    for category in _categories(alerts):
        matching = [a for a in alerts if a.category == category]
        services = sorted({a.service for a in matching})
        lines.append(f"- {category}: {len(matching)} ({', '.join(services)})")
    return "\n".join(lines)
