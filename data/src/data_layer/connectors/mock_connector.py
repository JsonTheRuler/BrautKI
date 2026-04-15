from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass
class ConnectorEmail:
    from_address: str
    to_address: str
    subject: str
    body: str
    provider_id: str


def fetch_emails_mock() -> Iterable[ConnectorEmail]:
    return [
        ConnectorEmail(
            from_address="ceo@client.no",
            to_address="hello@aiready.no",
            subject="Need AI readiness workshop",
            body="We want a 2-day workshop for our leadership team in May.",
            provider_id="mock-001",
        ),
        ConnectorEmail(
            from_address="ops@prospect.no",
            to_address="hello@aiready.no",
            subject="Can you automate inbox triage?",
            body="Looking for help with shared mailbox processing and CRM sync.",
            provider_id="mock-002",
        ),
    ]
