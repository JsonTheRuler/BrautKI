from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class Metrics:
    requests_total: int = 0
    auth_failures: int = 0
    council_decisions: int = 0


metrics = Metrics()


def log_event(event: str, payload: dict) -> None:
    print(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "llm-council",
            "event": event,
            **payload,
        }
    )
