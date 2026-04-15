from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from data_layer.config import settings


@dataclass
class ConnectorEmail:
    from_address: str
    to_address: str
    subject: str
    body: str
    provider_id: str


def fetch_emails_imap() -> Iterable[ConnectorEmail]:
    """
    IMAP connector stub.
    TODO:
      1) connect to IMAP using settings.imap_host/imaps over SSL
      2) search unseen/recent messages
      3) map message-id -> provider_id
      4) return ConnectorEmail rows
    """
    if not settings.imap_host or not settings.imap_username:
        return []

    # Placeholder output until credentials and parser are added.
    return []
