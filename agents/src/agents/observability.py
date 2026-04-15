from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class Metrics:
    requests_total: int = 0
    auth_failures: int = 0
    inbox_runs: int = 0
    crm_runs: int = 0
    marketing_runs: int = 0
    delivery_runs: int = 0


metrics = Metrics()


def log_event(event: str, payload: dict) -> None:
    print(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "agents",
            "event": event,
            **payload,
        }
    )
