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


def fetch_emails_graph() -> Iterable[ConnectorEmail]:
    """
    Microsoft Graph connector stub.
    TODO:
      1) obtain app token using tenant/client credentials
      2) query mailbox messages endpoint
      3) map Graph message id -> provider_id
      4) return ConnectorEmail rows
    """
    if not settings.graph_tenant_id or not settings.graph_client_id or not settings.graph_mailbox_user:
        return []

    # Placeholder output until credentials/token flow is wired.
    return []
